# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.listeners.triggers import TriggerResponses, trigger_pattern
from takina.cogs.listeners import triggers as triggers_module
from unittest.mock import AsyncMock, MagicMock
from takina.libs import lyerrors, lyviews
from takina import database, models
from types import SimpleNamespace
from tests import fakes
from typing import Any
import discord
import pytest


class TestPattern:
    @pytest.mark.parametrize(
        ("trigger", "message"),
        [
            ("vertin", "vertin"),
            ("vertin", "where is Vertin?"),
            ("vertin", "VERTIN!!"),
            ("reverse: 1999", "i love reverse: 1999 so much"),
            ("c++", "is c++ hard"),
            ("?help", "say ?help please"),
            ("!!", "wow !! really"),
            ("a.b", "see a.b now"),
        ],
    )
    def test_matches(self, trigger: str, message: str) -> None:
        assert trigger_pattern(trigger).search(message)

    @pytest.mark.parametrize(
        ("trigger", "message"),
        [
            ("cat", "concatenate"),
            ("cat", "cats"),
            ("cat", "bobcat"),
            ("a.b", "axb"),
            ("c++", "c++x"),
            ("vertin", "vert in"),
        ],
    )
    def test_whole_words_only(self, trigger: str, message: str) -> None:
        assert not trigger_pattern(trigger).search(message)

    def test_regex_characters_are_literal(self) -> None:
        assert not trigger_pattern(".*").search("anything at all")
        assert trigger_pattern(".*").search("literally .* here")


@pytest.fixture
def world() -> SimpleNamespace:
    guild = fakes.make_guild()
    bot = fakes.make_bot()
    bot.get_prefix = AsyncMock(return_value=[".", "takina "])
    cog = fakes.make_cog(TriggerResponses, bot)
    admin = fakes.make_member(guild, permissions=discord.Permissions(manage_channels=True))
    return SimpleNamespace(guild=guild, bot=bot, cog=cog, admin=admin)


def ctx(world: SimpleNamespace) -> MagicMock:
    return fakes.make_ctx(bot=world.bot, guild=world.guild, author=world.admin)


@pytest.mark.usefixtures("db")
class TestAdd:
    async def test_adds(self, world: SimpleNamespace) -> None:
        context = ctx(world)
        await fakes.call(world.cog.add_trigger, context, "r1999", "  vertin  ", "Timekeeper!")

        saved = await database.get(models.TriggerResponsesModel, guild_id=world.guild.id)
        assert saved is not None
        assert saved.triggers == {"r1999": {"trigger": "vertin", "response": "Timekeeper!"}}
        assert "Trigger `r1999` added." in (fakes.sent_embed(context.reply).description or "")

    @pytest.mark.parametrize(
        ("name", "trigger", "response", "message"),
        [
            ("r1999", "v", "x", "at least 2 characters"),
            ("r1999", "  v  ", "x", "at least 2 characters"),
            ("n" * 21, "vertin", "x", "name cannot exceed 20"),
            ("r1999", "v" * 76, "x", "text cannot exceed 75"),
            ("r1999", "vertin", "x" * 501, "response text cannot exceed 500"),
        ],
    )
    async def test_limits(
        self, world: SimpleNamespace, name: str, trigger: str, response: str, message: str
    ) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError, match=message):
            await fakes.call(world.cog.add_trigger, ctx(world), name, trigger, response)

    async def test_limits_inclusive(self, world: SimpleNamespace) -> None:
        await fakes.call(world.cog.add_trigger, ctx(world), "n" * 20, "v" * 75, "x" * 500)

    async def test_duplicate_text_case_insensitive(self, world: SimpleNamespace) -> None:
        await fakes.call(world.cog.add_trigger, ctx(world), "one", "Vertin", "a")
        with pytest.raises(lyerrors.TakinaError, match="text `vertin` already exists"):
            await fakes.call(world.cog.add_trigger, ctx(world), "two", "vertin", "b")

    async def test_duplicate_name(self, world: SimpleNamespace) -> None:
        await fakes.call(world.cog.add_trigger, ctx(world), "one", "vertin", "a")
        with pytest.raises(lyerrors.TakinaError, match="name `one` already exists"):
            await fakes.call(world.cog.add_trigger, ctx(world), "one", "sonetto", "b")

    async def test_maximum(self, world: SimpleNamespace) -> None:
        for number in range(triggers_module.MAX_TRIGGERS):
            await fakes.call(world.cog.add_trigger, ctx(world), f"t{number}", f"word{number}", "x")

        with pytest.raises(lyerrors.TakinaError, match="Maximum of 30 triggers"):
            await fakes.call(world.cog.add_trigger, ctx(world), "extra", "extra", "x")

    async def test_per_guild(self, world: SimpleNamespace) -> None:
        await fakes.call(world.cog.add_trigger, ctx(world), "one", "vertin", "a")
        other = fakes.make_guild()
        await fakes.call(
            world.cog.add_trigger, fakes.make_ctx(bot=world.bot, guild=other), "one", "vertin", "a"
        )
        assert len(await database.get_all(models.TriggerResponsesModel)) == 2


@pytest.mark.usefixtures("db")
class TestRemoveAndList:
    async def test_remove(self, world: SimpleNamespace) -> None:
        await fakes.call(world.cog.add_trigger, ctx(world), "one", "vertin", "a")
        context = ctx(world)
        await fakes.call(world.cog.remove_trigger, context, "one")

        saved = await database.get(models.TriggerResponsesModel, guild_id=world.guild.id)
        assert saved is not None and saved.triggers == {}
        assert "removed" in (fakes.sent_embed(context.reply).description or "")

    async def test_remove_unknown(self, world: SimpleNamespace) -> None:
        with pytest.raises(lyerrors.TakinaError, match="No trigger with the name `ghost`"):
            await fakes.call(world.cog.remove_trigger, ctx(world), "ghost")

    async def test_list_empty(self, world: SimpleNamespace) -> None:
        with pytest.raises(lyerrors.TakinaError, match="No triggers"):
            await fakes.call(world.cog.list_triggers, ctx(world))

    async def test_list_one_page(self, world: SimpleNamespace) -> None:
        await fakes.call(world.cog.add_trigger, ctx(world), "one", "vertin", "Timekeeper!")
        context = ctx(world)
        await fakes.call(world.cog.list_triggers, context)

        description = fakes.sent_embed(context.reply).description or ""
        assert "`one`" in description and "vertin" in description and "Timekeeper!" in description
        assert "view" not in fakes.sent(context.reply)

    async def test_list_paginates_whole_entries(
        self, world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for number in range(12):
            await fakes.call(
                world.cog.add_trigger, ctx(world), f"t{number}", f"word{number}", "x" * 500
            )

        send = AsyncMock()
        monkeypatch.setattr(lyviews.PaginatorView, "send", send)
        await fakes.call(world.cog.list_triggers, ctx(world))

        embeds = send.await_args_list[-1].args[1]
        assert len(embeds) == 3
        for embed in embeds:
            fakes.assert_embed_fits(embed)
            assert (embed.description or "").count("Trigger —") == (embed.description or "").count(
                "Response —"
            )


@pytest.mark.usefixtures("db")
class TestListener:
    async def setup_trigger(self, world: SimpleNamespace, trigger: str = "vertin") -> None:
        await database.save(
            models.TriggerResponsesModel(
                guild_id=world.guild.id,
                triggers={"r1999": {"trigger": trigger, "response": "Timekeeper! @everyone"}},
            )
        )

    def message(self, world: SimpleNamespace, content: str, channel: Any = None) -> MagicMock:
        return fakes.make_message(
            author=fakes.make_member(world.guild),
            channel=channel or fakes.make_channel(world.guild),
            guild=world.guild,
            content=content,
        )

    async def test_responds_without_pings(self, world: SimpleNamespace) -> None:
        await self.setup_trigger(world)
        message = self.message(world, "where is vertin")
        await world.cog.on_message(message)

        message.channel.send.assert_awaited_once()
        kwargs = fakes.sent(message.channel.send)
        assert kwargs["content"] == "Timekeeper! @everyone"
        mentions = kwargs["allowed_mentions"]
        assert not mentions.everyone and not mentions.users and not mentions.roles

    async def test_no_match(self, world: SimpleNamespace) -> None:
        await self.setup_trigger(world)
        message = self.message(world, "where is sonetto")
        await world.cog.on_message(message)
        message.channel.send.assert_not_awaited()

    async def test_commands_ignored(self, world: SimpleNamespace) -> None:
        await self.setup_trigger(world)
        for content in (".trigger add vertin", "takina vertin"):
            message = self.message(world, content)
            await world.cog.on_message(message)
            message.channel.send.assert_not_awaited()

    async def test_string_prefix(self, world: SimpleNamespace) -> None:
        await self.setup_trigger(world)
        world.bot.get_prefix = AsyncMock(return_value="!")
        message = self.message(world, "!vertin")
        await world.cog.on_message(message)
        message.channel.send.assert_not_awaited()

    async def test_bots_and_dms_ignored(self, world: SimpleNamespace) -> None:
        await self.setup_trigger(world)
        bot_message = self.message(world, "vertin")
        bot_message.author.bot = True
        await world.cog.on_message(bot_message)
        bot_message.channel.send.assert_not_awaited()

        dm = fakes.make_message(
            author=fakes.make_user(), channel=fakes.make_channel(), content="vertin"
        )
        await world.cog.on_message(dm)
        dm.channel.send.assert_not_awaited()

    async def test_cooldown_per_channel(
        self, world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        await self.setup_trigger(world)
        clock = SimpleNamespace(now=1000.0)
        monkeypatch.setattr(triggers_module.time, "monotonic", lambda: clock.now)

        channel = fakes.make_channel(world.guild)
        other_channel = fakes.make_channel(world.guild)

        await world.cog.on_message(self.message(world, "vertin", channel))
        await world.cog.on_message(self.message(world, "vertin", channel))
        assert channel.send.await_count == 1

        await world.cog.on_message(self.message(world, "vertin", other_channel))
        assert other_channel.send.await_count == 1

        clock.now += triggers_module.TRIGGER_COOLDOWN
        await world.cog.on_message(self.message(world, "vertin", channel))
        assert channel.send.await_count == 2

    async def test_one_response_per_message(self, world: SimpleNamespace) -> None:
        await database.save(
            models.TriggerResponsesModel(
                guild_id=world.guild.id,
                triggers={
                    "a": {"trigger": "vertin", "response": "one"},
                    "b": {"trigger": "sonetto", "response": "two"},
                },
            )
        )
        message = self.message(world, "vertin and sonetto")
        await world.cog.on_message(message)
        assert message.channel.send.await_count == 1

    async def test_new_trigger_applies_at_once(self, world: SimpleNamespace) -> None:
        # the listener reads the cache, which adding a trigger must refresh
        message = self.message(world, "vertin")
        await world.cog.on_message(message)
        await fakes.call(world.cog.add_trigger, ctx(world), "r1999", "vertin", "Timekeeper!")

        message = self.message(world, "vertin")
        await world.cog.on_message(message)
        message.channel.send.assert_awaited_once()


class TestChecks:
    @pytest.mark.parametrize("name", ["trigger add", "trigger remove"])
    async def test_need_manage_channels(self, world: SimpleNamespace, name: str) -> None:
        command = next(c for c in world.cog.walk_commands() if c.qualified_name == name)
        with pytest.raises(lyerrors.TakinaPermissionError, match="Manage Channels"):
            await fakes.run_checks(command, fakes.make_ctx(bot=world.bot, guild=world.guild))

    async def test_anyone_may_list(self, world: SimpleNamespace) -> None:
        assert await fakes.run_checks(
            world.cog.list_triggers, fakes.make_ctx(bot=world.bot, guild=world.guild)
        )
