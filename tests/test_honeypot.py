# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.listeners.honeypot import Honeypot, HONEYPOT_TIMEOUT, MAX_EVIDENCE_FILES
from unittest.mock import AsyncMock, MagicMock
from takina import database, models
from types import SimpleNamespace
from takina.libs import lymodlog
from takina.libs import lyerrors
from datetime import timedelta
from tests import fakes
from typing import Any
import discord
import pytest

pytestmark = pytest.mark.usefixtures("db")


def forbidden() -> discord.Forbidden:
    return discord.Forbidden(MagicMock(status=403, reason="Forbidden"), "Missing Permissions")


@pytest.fixture
async def world(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    guild = fakes.make_guild(filesize_limit=8 * 1024 * 1024)
    honeypot = fakes.make_channel(guild, name="free-nitro")
    general = fakes.make_channel(guild, name="general")
    modlog = fakes.make_channel(guild, name="mod-log")
    log_message = MagicMock(spec=discord.Message)
    log_message.channel = modlog
    modlog.send.return_value = log_message
    guild.get_channel.side_effect = {modlog.id: modlog}.get

    await database.save(
        models.GuildSettingsModel(
            guild_id=guild.id, honeypot_channel_id=honeypot.id, modlog_channel_id=modlog.id
        )
    )

    bot = fakes.make_bot()
    cog = fakes.make_cog(Honeypot, bot)
    scammer = fakes.make_member(guild, name="free_nitro_giver")
    return SimpleNamespace(
        guild=guild,
        honeypot=honeypot,
        general=general,
        modlog=modlog,
        log_message=log_message,
        bot=bot,
        cog=cog,
        scammer=scammer,
    )


def message(world: SimpleNamespace, channel: Any = None, **kwargs: Any) -> MagicMock:
    return fakes.make_message(
        author=world.scammer,
        channel=channel or world.honeypot,
        guild=world.guild,
        content=kwargs.pop("content", "free nitro at [discord.gift](https://scam.example)"),
        **kwargs,
    )


class TestTrigger:
    async def test_mutes_for_four_weeks(self, world: SimpleNamespace) -> None:
        await world.cog.on_message(message(world))
        world.scammer.timeout.assert_awaited_once_with(
            HONEYPOT_TIMEOUT, reason="Muted for triggering the honeypot system."
        )
        assert HONEYPOT_TIMEOUT <= timedelta(days=28), "discord refuses longer timeouts"

    async def test_dms_the_member(self, world: SimpleNamespace) -> None:
        await world.cog.on_message(message(world))
        embed = fakes.sent_embed(world.scammer.send)
        assert f"You were muted in **{world.guild.name}** for 4 weeks." in (embed.description or "")

    async def test_closed_dms_dont_stop_it(self, world: SimpleNamespace) -> None:
        world.scammer.send.side_effect = forbidden()
        await world.cog.on_message(message(world))
        assert world.modlog.send.await_count == 1

    async def test_logs_a_case(self, world: SimpleNamespace) -> None:
        await world.cog.on_message(message(world))
        (case,) = await database.get_all(models.ModLogCaseModel)
        assert case.action == "mute"
        assert case.duration == "4w"
        assert case.member_ids == [world.scammer.id]
        assert case.moderator_id == world.bot.user.id

    async def test_other_channels_ignored(self, world: SimpleNamespace) -> None:
        await world.cog.on_message(message(world, channel=world.general))
        world.scammer.timeout.assert_not_awaited()

    async def test_bots_ignored(self, world: SimpleNamespace) -> None:
        world.scammer.bot = True
        await world.cog.on_message(message(world))
        world.scammer.timeout.assert_not_awaited()

    async def test_dms_ignored(self, world: SimpleNamespace) -> None:
        dm = fakes.make_message(author=fakes.make_user(), channel=fakes.make_channel())
        await world.cog.on_message(dm)

    async def test_unconfigured_guild(self, world: SimpleNamespace) -> None:
        other = fakes.make_guild()
        member = fakes.make_member(other)
        await world.cog.on_message(
            fakes.make_message(author=member, channel=fakes.make_channel(other), guild=other)
        )
        member.timeout.assert_not_awaited()

    async def test_untouchable_member_is_left_alone(self, world: SimpleNamespace) -> None:
        # staff testing the honeypot outrank the bot, and must not lose their messages
        world.scammer.timeout.side_effect = forbidden()
        cached = message(world)
        world.bot.cached_messages = [cached]

        await world.cog.on_message(cached)

        world.honeypot.delete_messages.assert_not_awaited()
        world.modlog.send.assert_not_awaited()
        world.scammer.send.assert_not_awaited()


class TestPurge:
    async def test_clears_recent_messages_everywhere(self, world: SimpleNamespace) -> None:
        bait = message(world)
        elsewhere = message(world, channel=world.general, content="spam")
        old = message(world, channel=world.general, content="last month")
        old.created_at = discord.utils.utcnow() - timedelta(hours=1)
        someone_else = fakes.make_message(
            author=fakes.make_member(world.guild), channel=world.general, guild=world.guild
        )
        world.bot.cached_messages = [bait, elsewhere, old, someone_else]

        await world.cog.on_message(bait)

        world.honeypot.delete_messages.assert_awaited_once()
        assert world.honeypot.delete_messages.await_args_list[-1].args[0] == [bait]
        assert world.general.delete_messages.await_args_list[-1].args[0] == [elsewhere]

    async def test_other_guilds_untouched(self, world: SimpleNamespace) -> None:
        other = fakes.make_guild()
        other_channel = fakes.make_channel(other)
        same_user_elsewhere = fakes.make_message(
            author=world.scammer, channel=other_channel, guild=other
        )
        world.bot.cached_messages = [same_user_elsewhere]

        await world.cog.on_message(message(world))
        other_channel.delete_messages.assert_not_awaited()

    async def test_chunks_of_a_hundred(self, world: SimpleNamespace) -> None:
        world.bot.cached_messages = [message(world, channel=world.general) for _ in range(250)]
        await world.cog.on_message(message(world))
        sizes = [len(call.args[0]) for call in world.general.delete_messages.await_args_list]
        assert sizes == [100, 100, 50]

    async def test_failed_purge_continues(self, world: SimpleNamespace) -> None:
        world.general.delete_messages.side_effect = forbidden()
        bait = message(world)
        world.bot.cached_messages = [message(world, channel=world.general), bait]

        await world.cog.on_message(bait)
        world.honeypot.delete_messages.assert_awaited_once()
        world.modlog.send.assert_awaited_once()


class TestEvidence:
    """#110: moderators without message logs see what the member posted."""

    async def test_replies_to_the_case(self, world: SimpleNamespace) -> None:
        await world.cog.on_message(message(world))

        world.log_message.reply.assert_awaited_once()
        kwargs = fakes.sent(world.log_message.reply)
        assert kwargs["mention_author"] is False
        embed = fakes.sent_embed(world.log_message.reply)
        assert embed.author.name == "free_nitro_giver"
        assert f"**Caught message** in {world.honeypot.mention}" in (embed.description or "")

    async def test_markdown_shown_raw(self, world: SimpleNamespace) -> None:
        # a masked link must show where it really goes
        await world.cog.on_message(message(world))
        description = fakes.sent_embed(world.log_message.reply).description or ""
        assert r"\[discord.gift](https://scam.example)" in description

    async def test_empty_message(self, world: SimpleNamespace) -> None:
        await world.cog.on_message(message(world, content=""))
        assert "*No text.*" in (fakes.sent_embed(world.log_message.reply).description or "")

    async def test_long_message_fits(self, world: SimpleNamespace) -> None:
        await world.cog.on_message(message(world, content="*" * 4000))
        fakes.sent_embed(world.log_message.reply)

    async def test_attachments_kept_and_spoilered(self, world: SimpleNamespace) -> None:
        attachments = [fakes.make_attachment(filename=f"scam{n}.png") for n in range(3)]
        await world.cog.on_message(message(world, attachments=attachments))

        for attachment in attachments:
            attachment.to_file.assert_awaited_once_with(spoiler=True)
        files = fakes.sent(world.log_message.reply)["files"]
        assert files == [attachment.to_file.return_value for attachment in attachments]
        assert fakes.sent_embed(world.log_message.reply).footer.text is None

    async def test_attachments_fetched_before_purge(self, world: SimpleNamespace) -> None:
        order: list[str] = []
        attachment = fakes.make_attachment()
        attachment.to_file.side_effect = lambda **kwargs: order.append("fetch")
        world.honeypot.delete_messages.side_effect = lambda *args, **kwargs: order.append("purge")
        bait = message(world, attachments=[attachment])
        world.bot.cached_messages = [bait]

        await world.cog.on_message(bait)
        assert order == ["fetch", "purge"]

    async def test_oversized_attachments_counted(self, world: SimpleNamespace) -> None:
        small = fakes.make_attachment(size=1024)
        huge = fakes.make_attachment(size=world.guild.filesize_limit + 1)
        await world.cog.on_message(message(world, attachments=[huge, small]))

        huge.to_file.assert_not_awaited()
        assert fakes.sent(world.log_message.reply)["files"] == [small.to_file.return_value]
        assert fakes.sent_embed(world.log_message.reply).footer.text == (
            "1 attachment(s) could not be kept."
        )

    async def test_files_share_one_upload_limit(self, world: SimpleNamespace) -> None:
        half = world.guild.filesize_limit // 2 + 1
        first, second = fakes.make_attachment(size=half), fakes.make_attachment(size=half)
        await world.cog.on_message(message(world, attachments=[first, second]))

        first.to_file.assert_awaited_once()
        second.to_file.assert_not_awaited()

    async def test_at_most_ten_files(self, world: SimpleNamespace) -> None:
        attachments = [fakes.make_attachment(size=1) for _ in range(MAX_EVIDENCE_FILES + 2)]
        await world.cog.on_message(message(world, attachments=attachments))
        assert len(fakes.sent(world.log_message.reply)["files"]) == MAX_EVIDENCE_FILES

    async def test_unfetchable_attachment_skipped(self, world: SimpleNamespace) -> None:
        gone = fakes.make_attachment()
        gone.to_file.side_effect = discord.NotFound(MagicMock(status=404), "gone")
        kept = fakes.make_attachment()
        await world.cog.on_message(message(world, attachments=[gone, kept]))

        assert fakes.sent(world.log_message.reply)["files"] == [kept.to_file.return_value]

    async def test_nothing_without_a_modlog(self, world: SimpleNamespace) -> None:
        settings = await database.get(models.GuildSettingsModel, guild_id=world.guild.id)
        assert settings is not None
        settings.modlog_channel_id = None
        await database.save(settings)

        await world.cog.on_message(message(world))
        world.modlog.send.assert_not_awaited()
        world.log_message.reply.assert_not_awaited()

    async def test_failed_reply_is_logged(
        self, world: SimpleNamespace, caplog: pytest.LogCaptureFixture
    ) -> None:
        world.log_message.reply.side_effect = forbidden()
        await world.cog.on_message(message(world))
        assert any("could not post evidence" in record.message for record in caplog.records)

    async def test_no_bot_user(
        self, world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        world.bot.user = None
        log_action = AsyncMock()
        monkeypatch.setattr(lymodlog, "log_action", log_action)
        await world.cog.on_message(message(world))
        log_action.assert_not_awaited()


class TestCommands:
    async def test_set_moves_to_settings(self, world: SimpleNamespace) -> None:
        ctx = fakes.make_ctx(guild=world.guild)
        ctx.bot.get_command.return_value = MagicMock()
        await fakes.call(world.cog.honeypot_set, ctx, world.general)
        ctx.bot.get_command.assert_called_once_with("settings guild honeypot")

    async def test_disable_moves_to_settings(self, world: SimpleNamespace) -> None:
        ctx = fakes.make_ctx(guild=world.guild)
        ctx.bot.get_command.return_value = MagicMock()
        await fakes.call(world.cog.honeypot_disable, ctx)
        ctx.invoke.assert_awaited_once_with(ctx.bot.get_command.return_value, feature="honeypot")

    @pytest.mark.parametrize("name", ["honeypot", "honeypot set", "honeypot disable"])
    async def test_need_manage_server(self, world: SimpleNamespace, name: str) -> None:
        command = next(c for c in world.cog.walk_commands() if c.qualified_name == name)
        with pytest.raises(lyerrors.TakinaPermissionError, match="Manage Guild"):
            await fakes.run_checks(command, fakes.make_ctx(guild=world.guild))
