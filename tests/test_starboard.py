# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.models import StarboardMessageModel, StarboardSettingsModel
from takina.cogs.listeners.starboard import Starboard, is_public_source
from unittest.mock import MagicMock
from types import SimpleNamespace
from takina.libs import lyerrors
from typing import Any, cast
from takina import database
from tests import fakes
import discord
import asyncio
import pytest


class FakeReaction:
    def __init__(self, emoji: str, users: list[Any]) -> None:
        self.emoji = emoji
        self._users = users
        self.count = len(users)

    async def users(self) -> Any:
        for user in self._users:
            yield user


def reaction(emoji: str, users: list[Any] | None = None) -> discord.Reaction:
    # all a starboard needs from a reaction, passed where the real thing goes
    return cast(discord.Reaction, FakeReaction(emoji, users or []))


def readable(channel: MagicMock, everyone: bool = True) -> MagicMock:
    channel.permissions_for.return_value = discord.Permissions(read_messages=everyone)
    return channel


class TestIsPublicSource:
    def setup_method(self) -> None:
        self.guild = fakes.make_guild()
        self.starboard = fakes.make_channel(self.guild, name="starboard")
        self.settings = StarboardSettingsModel(guild_id=self.guild.id)

    def test_public_channel(self) -> None:
        channel = readable(fakes.make_channel(self.guild))
        assert is_public_source(channel, self.starboard, self.settings)

    def test_private_channel(self) -> None:
        channel = readable(fakes.make_channel(self.guild), everyone=False)
        assert not is_public_source(channel, self.starboard, self.settings)

    def test_nsfw_into_sfw(self) -> None:
        channel = readable(fakes.make_channel(self.guild, nsfw=True))
        assert not is_public_source(channel, self.starboard, self.settings)

    def test_nsfw_into_nsfw(self) -> None:
        channel = readable(fakes.make_channel(self.guild, nsfw=True))
        starboard = fakes.make_channel(self.guild, nsfw=True)
        assert is_public_source(channel, starboard, self.settings)

    def test_whitelist_opts_in_private(self) -> None:
        channel = readable(fakes.make_channel(self.guild), everyone=False)
        self.settings.whitelisted_channel_ids = [channel.id]
        assert is_public_source(channel, self.starboard, self.settings)

    def test_whitelist_excludes_others(self) -> None:
        channel = readable(fakes.make_channel(self.guild))
        self.settings.whitelisted_channel_ids = [12345]
        assert not is_public_source(channel, self.starboard, self.settings)

    def test_whitelist_keeps_nsfw_guard(self) -> None:
        channel = readable(fakes.make_channel(self.guild, nsfw=True))
        self.settings.whitelisted_channel_ids = [channel.id]
        assert not is_public_source(channel, self.starboard, self.settings)

    def test_thread_follows_parent_whitelist(self) -> None:
        thread = readable(fakes.make_channel(self.guild, discord.Thread))
        thread.parent_id = 777
        self.settings.whitelisted_channel_ids = [777]
        assert is_public_source(thread, self.starboard, self.settings)

    def test_private_thread(self) -> None:
        thread = readable(fakes.make_channel(self.guild, discord.Thread))
        thread.is_private.return_value = True
        assert not is_public_source(thread, self.starboard, self.settings)

    def test_public_thread(self) -> None:
        thread = readable(fakes.make_channel(self.guild, discord.Thread))
        thread.is_private.return_value = False
        assert is_public_source(thread, self.starboard, self.settings)


@pytest.fixture
async def world() -> SimpleNamespace:
    guild = fakes.make_guild()
    starboard = fakes.make_channel(guild, name="starboard")
    starboard.send.return_value = MagicMock(spec=discord.Message, id=5555)
    source = readable(fakes.make_channel(guild, name="art"))

    channels = {starboard.id: starboard, source.id: source}
    guild.get_channel.side_effect = channels.get
    guild.get_channel_or_thread.side_effect = channels.get

    bot = fakes.make_bot()
    bot.get_guild.side_effect = {guild.id: guild}.get
    cog = fakes.make_cog(Starboard, bot)

    await database.save(
        StarboardSettingsModel(
            guild_id=guild.id, starboard_channel_id=starboard.id, minimum_reaction_count=3
        )
    )
    author = fakes.make_member(guild, name="alice")
    return SimpleNamespace(
        guild=guild, starboard=starboard, source=source, bot=bot, cog=cog, author=author
    )


def starred(world: SimpleNamespace, stars: int, *, self_star: bool = False, **kwargs: Any) -> Any:
    message = fakes.make_message(
        author=world.author,
        channel=world.source,
        guild=world.guild,
        content=kwargs.pop("content", "Shanghai doll"),
    )
    users = [fakes.make_user() for _ in range(stars - self_star)] + (
        [world.author] if self_star else []
    )
    message.reactions = [FakeReaction("⭐", users)] if stars else []
    for key, value in kwargs.items():
        setattr(message, key, value)
    world.bot.cached_messages = [message]
    return message


def payload(world: SimpleNamespace, message: Any) -> Any:
    return SimpleNamespace(
        guild_id=world.guild.id, channel_id=world.source.id, message_id=message.id
    )


@pytest.mark.usefixtures("db")
class TestSync:
    async def test_below_threshold(self, world: SimpleNamespace) -> None:
        message = starred(world, 2)
        await world.cog.on_raw_reaction_add(payload(world, message))
        world.starboard.send.assert_not_awaited()

    async def test_posts_at_threshold(self, world: SimpleNamespace) -> None:
        message = starred(world, 3)
        await world.cog.on_raw_reaction_add(payload(world, message))

        kwargs = fakes.sent(world.starboard.send)
        embed = kwargs["embeds"][0]
        fakes.assert_embed_fits(embed)
        assert embed.description == "Shanghai doll"
        assert embed.url == message.jump_url
        assert embed.fields[0].value == "3 ⭐ reactions"
        assert kwargs["view"].children[0].url == message.jump_url

        saved = await database.get(StarboardMessageModel, message_id=message.id)
        assert saved is not None and saved.starboard_message_id == 5555

    async def test_self_star_does_not_count(self, world: SimpleNamespace) -> None:
        message = starred(world, 3, self_star=True)
        await world.cog.on_raw_reaction_add(payload(world, message))
        world.starboard.send.assert_not_awaited()

    async def test_most_popular_emoji_counts(self, world: SimpleNamespace) -> None:
        message = starred(world, 0)
        message.reactions = [
            FakeReaction("👍", [fakes.make_user()]),
            FakeReaction("🔥", [fakes.make_user() for _ in range(4)]),
        ]
        await world.cog.on_raw_reaction_add(payload(world, message))
        assert fakes.sent(world.starboard.send)["embeds"][0].fields[0].value == "4 🔥 reactions"

    async def test_edits_when_counts_change(self, world: SimpleNamespace) -> None:
        message = starred(world, 3)
        await world.cog.on_raw_reaction_add(payload(world, message))

        partial = MagicMock(spec=discord.PartialMessage)
        world.starboard.get_partial_message.return_value = partial
        message.reactions = [FakeReaction("⭐", [fakes.make_user() for _ in range(5)])]
        await world.cog.on_raw_reaction_add(payload(world, message))

        world.starboard.get_partial_message.assert_called_with(5555)
        assert (
            partial.edit.await_args_list[-1].kwargs["embeds"][0].fields[0].value == "5 ⭐ reactions"
        )
        assert world.starboard.send.await_count == 1

    async def test_removed_below_threshold(self, world: SimpleNamespace) -> None:
        message = starred(world, 3)
        await world.cog.on_raw_reaction_add(payload(world, message))

        partial = MagicMock(spec=discord.PartialMessage)
        world.starboard.get_partial_message.return_value = partial
        message.reactions = [FakeReaction("⭐", [fakes.make_user()])]
        await world.cog.on_raw_reaction_remove(payload(world, message))

        partial.delete.assert_awaited_once()
        assert await database.get(StarboardMessageModel, message_id=message.id) is None

    async def test_all_reactions_gone(self, world: SimpleNamespace) -> None:
        message = starred(world, 3)
        await world.cog.on_raw_reaction_add(payload(world, message))
        world.starboard.get_partial_message.return_value = MagicMock(spec=discord.PartialMessage)

        message.reactions = []
        await world.cog.on_raw_reaction_remove(payload(world, message))
        assert await database.get(StarboardMessageModel, message_id=message.id) is None

    async def test_post_deleted_by_hand_is_reposted(self, world: SimpleNamespace) -> None:
        message = starred(world, 3)
        await world.cog.on_raw_reaction_add(payload(world, message))

        partial = MagicMock(spec=discord.PartialMessage)
        partial.edit.side_effect = discord.NotFound(MagicMock(status=404), "gone")
        world.starboard.get_partial_message.return_value = partial
        world.starboard.send.return_value = MagicMock(spec=discord.Message, id=6666)

        await world.cog.on_raw_reaction_add(payload(world, message))
        saved = await database.get(StarboardMessageModel, message_id=message.id)
        assert saved is not None and saved.starboard_message_id == 6666

    async def test_concurrent_reactions_post_once(self, world: SimpleNamespace) -> None:
        message = starred(world, 3)
        await asyncio.gather(
            *(world.cog.on_raw_reaction_add(payload(world, message)) for _ in range(5))
        )
        assert world.starboard.send.await_count == 1

    async def test_fetches_uncached(self, world: SimpleNamespace) -> None:
        message = starred(world, 3)
        world.bot.cached_messages = []
        world.source.fetch_message.return_value = message
        await world.cog.on_raw_reaction_add(payload(world, message))
        world.source.fetch_message.assert_awaited_once_with(message.id)
        world.starboard.send.assert_awaited_once()

    async def test_deleted_source(self, world: SimpleNamespace) -> None:
        message = starred(world, 3)
        world.bot.cached_messages = []
        world.source.fetch_message.side_effect = discord.NotFound(MagicMock(status=404), "gone")
        await world.cog.on_raw_reaction_add(payload(world, message))
        world.starboard.send.assert_not_awaited()

    async def test_bot_messages_ignored(self, world: SimpleNamespace) -> None:
        world.author.bot = True
        message = starred(world, 5)
        await world.cog.on_raw_reaction_add(payload(world, message))
        world.starboard.send.assert_not_awaited()

    async def test_private_source_ignored(self, world: SimpleNamespace) -> None:
        readable(world.source, everyone=False)
        message = starred(world, 5)
        await world.cog.on_raw_reaction_add(payload(world, message))
        world.starboard.send.assert_not_awaited()

    async def test_unconfigured(self, world: SimpleNamespace) -> None:
        settings = await database.get(StarboardSettingsModel, guild_id=world.guild.id)
        assert settings is not None
        settings.starboard_channel_id = None
        await database.save(settings)

        message = starred(world, 5)
        await world.cog.on_raw_reaction_add(payload(world, message))
        world.starboard.send.assert_not_awaited()

    async def test_dm_reactions(self, world: SimpleNamespace) -> None:
        await world.cog.on_raw_reaction_add(
            SimpleNamespace(guild_id=None, channel_id=1, message_id=2)
        )

    async def test_unknown_guild(self, world: SimpleNamespace) -> None:
        await world.cog.on_raw_reaction_add(SimpleNamespace(guild_id=1, channel_id=1, message_id=2))


class TestEmbed:
    def message(self, **kwargs: Any) -> Any:
        guild = fakes.make_guild()
        message = fakes.make_message(
            author=fakes.make_member(guild), channel=fakes.make_channel(guild), guild=guild
        )
        for key, value in kwargs.items():
            setattr(message, key, value)
        return message

    def test_no_text(self) -> None:
        embeds, _ = Starboard._create_embed(self.message(), reaction("⭐"), 1)
        assert embeds[0].description == "*No text content*"
        assert embeds[0].fields[0].value == "1 ⭐ reaction"

    def test_images_make_a_gallery(self) -> None:
        attachments = [fakes.make_attachment(filename=f"{n}.png") for n in range(3)] + [
            fakes.make_attachment(filename="notes.txt", content_type="text/plain")
        ]
        message = self.message(attachments=attachments)

        embeds, _ = Starboard._create_embed(message, reaction("⭐"), 4)
        assert embeds[0].image.url == attachments[0].url
        assert [embed.image.url for embed in embeds[1:]] == [attachments[1].url, attachments[2].url]
        # sharing the jump url is what makes discord show them as one gallery
        assert all(embed.url == message.jump_url for embed in embeds)

    def test_link_embeds_and_stickers(self) -> None:
        image = discord.Embed.from_dict(
            {
                "type": "image",
                "url": "https://i.example/a.png",
                "thumbnail": {"url": "https://i.example/thumb.png"},
            }
        )
        rich = discord.Embed(title="Bunbunmaru News", description="Extra!")
        sticker = SimpleNamespace(url="https://media.discordapp.net/stickers/1.png")
        message = self.message(embeds=[image, rich], stickers=[sticker])

        embeds, _ = Starboard._create_embed(message, reaction("⭐"), 4)
        assert embeds[0].image.url == "https://i.example/thumb.png"
        assert embeds[1].image.url == sticker.url
        assert embeds[-1] is rich

    def test_capped_at_ten(self) -> None:
        attachments = [fakes.make_attachment(filename=f"{n}.png") for n in range(15)]
        embeds, _ = Starboard._create_embed(
            self.message(attachments=attachments), reaction("⭐"), 4
        )
        assert len(embeds) == 10

    def test_counts_formatted(self) -> None:
        embeds, _ = Starboard._create_embed(self.message(), reaction("⭐"), 1234)
        assert embeds[0].fields[0].value == "1,234 ⭐ reactions"


@pytest.mark.usefixtures("db")
class TestWhitelist:
    async def test_add_and_list(self, world: SimpleNamespace) -> None:
        other = fakes.make_channel(world.guild, name="screenshots")
        ctx = fakes.make_ctx(bot=world.bot, guild=world.guild)
        await fakes.call(world.cog.whitelist_add, ctx, [world.source, other, world.source])

        settings = await database.get(StarboardSettingsModel, guild_id=world.guild.id)
        assert settings is not None
        assert settings.whitelisted_channel_ids == [world.source.id, other.id]

        world.guild.get_channel.side_effect = {world.source.id: world.source}.get
        ctx = fakes.make_ctx(bot=world.bot, guild=world.guild)
        await fakes.call(world.cog.whitelist_list, ctx)
        # the deleted channel is left out rather than shown as a broken mention
        assert fakes.sent_embed(ctx.reply).description == (
            f"📝 **Whitelisted channels**: {world.source.mention}"
        )

    async def test_add_nothing(self, world: SimpleNamespace) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError):
            await fakes.call(world.cog.whitelist_add, fakes.make_ctx(guild=world.guild), [])

    async def test_add_already_there(self, world: SimpleNamespace) -> None:
        ctx = fakes.make_ctx(guild=world.guild)
        await fakes.call(world.cog.whitelist_add, ctx, [world.source])
        with pytest.raises(lyerrors.TakinaError, match="already whitelisted"):
            await fakes.call(world.cog.whitelist_add, ctx, [world.source])

    async def test_add_without_settings(self, world: SimpleNamespace) -> None:
        guild = fakes.make_guild()
        channel = fakes.make_channel(guild)
        await fakes.call(world.cog.whitelist_add, fakes.make_ctx(guild=guild), [channel])
        settings = await database.get(StarboardSettingsModel, guild_id=guild.id)
        assert settings is not None and settings.whitelisted_channel_ids == [channel.id]

    async def test_remove(self, world: SimpleNamespace) -> None:
        ctx = fakes.make_ctx(guild=world.guild)
        await fakes.call(world.cog.whitelist_add, ctx, [world.source])
        await fakes.call(world.cog.whitelist_remove, ctx, [world.source])
        settings = await database.get(StarboardSettingsModel, guild_id=world.guild.id)
        assert settings is not None and settings.whitelisted_channel_ids == []

    async def test_remove_when_empty(self, world: SimpleNamespace) -> None:
        with pytest.raises(lyerrors.TakinaError, match="No channels are whitelisted"):
            await fakes.call(
                world.cog.whitelist_remove, fakes.make_ctx(guild=world.guild), [world.source]
            )

    async def test_remove_unlisted(self, world: SimpleNamespace) -> None:
        ctx = fakes.make_ctx(guild=world.guild)
        await fakes.call(world.cog.whitelist_add, ctx, [world.source])
        with pytest.raises(lyerrors.TakinaError, match="None of the specified"):
            await fakes.call(world.cog.whitelist_remove, ctx, [fakes.make_channel(world.guild)])

    async def test_list_empty(self, world: SimpleNamespace) -> None:
        with pytest.raises(lyerrors.TakinaError, match="No channels are whitelisted"):
            await fakes.call(world.cog.whitelist_list, fakes.make_ctx(guild=world.guild))

    async def test_list_all_deleted(self, world: SimpleNamespace) -> None:
        ctx = fakes.make_ctx(guild=world.guild)
        await fakes.call(world.cog.whitelist_add, ctx, [world.source])
        world.guild.get_channel.side_effect = lambda channel_id: None
        with pytest.raises(lyerrors.TakinaError, match="could be found"):
            await fakes.call(world.cog.whitelist_list, fakes.make_ctx(guild=world.guild))

    @pytest.mark.parametrize(
        ("name", "permission"),
        [
            ("starboard settings", "Manage Guild"),
            ("starboard disable", "Manage Guild"),
            ("starboard whitelist add", "Manage Channels"),
            ("starboard whitelist remove", "Manage Channels"),
            ("starboard whitelist list", "Manage Channels"),
        ],
    )
    async def test_checks(self, world: SimpleNamespace, name: str, permission: str) -> None:
        command = next(c for c in world.cog.walk_commands() if c.qualified_name == name)
        with pytest.raises(lyerrors.TakinaPermissionError, match=permission):
            await fakes.run_checks(command, fakes.make_ctx(guild=world.guild))
