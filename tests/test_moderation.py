# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.mod.mute import MAX_TIMEOUT, Mute, parse_timeout
from takina.libs import lyerrors, lymodlog, lyviews
from takina.cogs.mod.ban import Ban, parse_user_id
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta, UTC
from takina.cogs.mod.reports import Reports
from takina.cogs.mod.modlog import ModLog
from takina.cogs.mod.warn import Warnings
from takina.cogs.mod.purge import Purge
from takina.cogs.mod.kick import Kick
from takina.cogs.mod.nick import Nick
from takina import database, models
from types import SimpleNamespace
from discord.ext import commands
from tests import fakes
from typing import Any
import discord
import pytest


def not_found() -> discord.NotFound:
    return discord.NotFound(MagicMock(status=404, reason="Not Found"), "Unknown")


@pytest.fixture
def world() -> SimpleNamespace:
    guild = fakes.make_guild(name="Gensokyo")
    bot_role = fakes.make_role(guild, position=50, name="Takina")
    mod_role = fakes.make_role(guild, position=20, name="Moderator")
    fairy_role = fakes.make_role(guild, position=1, name="Fairy")
    guild.me = fakes.make_member(guild, name="takina", top_role=bot_role, bot=True)
    moderator = fakes.make_member(
        guild,
        name="reimu",
        top_role=mod_role,
        permissions=discord.Permissions(
            ban_members=True,
            kick_members=True,
            moderate_members=True,
            manage_messages=True,
            manage_nicknames=True,
        ),
    )
    guild.owner = fakes.make_member(
        guild, name="yukari", top_role=fakes.make_role(guild, position=60)
    )
    cirno = fakes.make_member(guild, name="cirno", top_role=fairy_role)
    bot = fakes.make_bot()
    return SimpleNamespace(
        guild=guild, moderator=moderator, cirno=cirno, mod_role=mod_role, bot=bot
    )


def ctx(world: SimpleNamespace, **kwargs: Any) -> Any:
    return fakes.make_ctx(bot=world.bot, guild=world.guild, author=world.moderator, **kwargs)


@pytest.fixture
def moderate(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """lymodlog.moderate, recorded instead of run; its own tests cover what it does."""
    mock = AsyncMock()
    monkeypatch.setattr(lymodlog, "moderate", mock)
    return mock


class TestParsers:
    @pytest.mark.parametrize(
        ("text", "user_id"),
        [
            ("716306888492318790", 716306888492318790),
            (" 716306888492318790 ", 716306888492318790),
            ("<@716306888492318790>", 716306888492318790),
            ("<@!716306888492318790>", 716306888492318790),
        ],
    )
    def test_user_ids(self, text: str, user_id: int) -> None:
        # well past 2^53, which is why slash takes these as text
        assert parse_user_id(text) == user_id

    @pytest.mark.parametrize("text", ["", "cirno", "<@&123>", "<#123>", "12a", "-5", "1.5"])
    def test_bad_user_ids(self, text: str) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError):
            parse_user_id(text)

    @pytest.mark.parametrize(
        ("text", "timeout"),
        [
            ("30s", timedelta(seconds=30)),
            ("1h 30m", timedelta(minutes=90)),
            ("28d", MAX_TIMEOUT),
            ("4w", MAX_TIMEOUT),
        ],
    )
    def test_timeouts(self, text: str, timeout: timedelta) -> None:
        assert parse_timeout(text) == timeout

    @pytest.mark.parametrize(
        ("text", "message"), [("29s", "minimum"), ("29d", "maximum"), ("1y", "maximum")]
    )
    def test_bad_timeouts(self, text: str, message: str) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError, match=message):
            parse_timeout(text)


class TestSingleActions:
    async def test_ban(self, world: SimpleNamespace, moderate: AsyncMock) -> None:
        cog = fakes.make_cog(Ban, world.bot)
        context = ctx(world)
        await fakes.call(cog.ban, context, world.cirno, reason="Freezing frogs")

        args, kwargs = moderate.await_args_list[-1]
        assert args[1:4] == ([world.cirno], "ban", "Freezing frogs")
        assert args[5] == "You were banned in **Gensokyo**."
        assert kwargs == {"dm_first": True}

        await args[4](world.cirno, "audit")
        world.cirno.ban.assert_awaited_once_with(reason="audit")

    async def test_kick(self, world: SimpleNamespace, moderate: AsyncMock) -> None:
        cog = fakes.make_cog(Kick, world.bot)
        await fakes.call(cog.kick, ctx(world), world.cirno, reason="Pranks")
        args, kwargs = moderate.await_args_list[-1]
        assert args[2] == "kick" and kwargs == {"dm_first": True}
        await args[4](world.cirno, "audit")
        world.cirno.kick.assert_awaited_once_with(reason="audit")

    async def test_mute(self, world: SimpleNamespace, moderate: AsyncMock) -> None:
        cog = fakes.make_cog(Mute, world.bot)
        await fakes.call(cog.mute, ctx(world), world.cirno, "12h", reason="Spam")
        args, kwargs = moderate.await_args_list[-1]
        assert args[5] == "You were muted in **Gensokyo** for 12h."
        assert kwargs == {"duration": "12h"}
        await args[4](world.cirno, "audit")
        world.cirno.timeout.assert_awaited_once_with(timedelta(hours=12), reason="audit")

    async def test_mute_checks_duration_first(
        self, world: SimpleNamespace, moderate: AsyncMock
    ) -> None:
        cog = fakes.make_cog(Mute, world.bot)
        with pytest.raises(lyerrors.TakinaUserInputError):
            await fakes.call(cog.mute, ctx(world), world.cirno, "30d")
        moderate.assert_not_awaited()

    async def test_unmute(self, world: SimpleNamespace, moderate: AsyncMock) -> None:
        cog = fakes.make_cog(Mute, world.bot)
        await fakes.call(cog.unmute, ctx(world), world.cirno)
        args, _ = moderate.await_args_list[-1]
        assert args[2:4] == ("unmute", "No reason provided")
        await args[4](world.cirno, "audit")
        world.cirno.timeout.assert_awaited_once_with(None, reason="audit")

    async def test_warn(self, world: SimpleNamespace, moderate: AsyncMock) -> None:
        cog = fakes.make_cog(Warnings, world.bot)
        await fakes.call(cog.warn, ctx(world), world.cirno, reason="Be nice")
        args, _ = moderate.await_args_list[-1]
        assert args[2] == "warn" and args[4] is None

    @pytest.mark.parametrize(
        ("cog_class", "name", "extra"),
        [
            (Ban, "ban", ()),
            (Kick, "kick", ()),
            (Mute, "mute", ("1h",)),
            (Mute, "unmute", ()),
            (Warnings, "warn", ()),
        ],
    )
    async def test_refuse_higher_members(
        self,
        world: SimpleNamespace,
        moderate: AsyncMock,
        cog_class: type[commands.Cog],
        name: str,
        extra: tuple,
    ) -> None:
        cog = fakes.make_cog(cog_class, world.bot)
        peer = fakes.make_member(world.guild, name="sanae", top_role=world.mod_role)
        with pytest.raises(lyerrors.TakinaPermissionError):
            await fakes.call(getattr(cog, name), ctx(world), peer, *extra)
        moderate.assert_not_awaited()

    @pytest.mark.parametrize(
        ("cog_class", "name"), [(Ban, "ban"), (Kick, "kick"), (Warnings, "warn")]
    )
    async def test_refuse_self(
        self, world: SimpleNamespace, moderate: AsyncMock, cog_class: type[commands.Cog], name: str
    ) -> None:
        cog = fakes.make_cog(cog_class, world.bot)
        with pytest.raises(lyerrors.TakinaPermissionError, match="yourself"):
            await fakes.call(getattr(cog, name), ctx(world), world.moderator)

    async def test_refuse_owner(self, world: SimpleNamespace, moderate: AsyncMock) -> None:
        cog = fakes.make_cog(Ban, world.bot)
        with pytest.raises(lyerrors.TakinaPermissionError):
            await fakes.call(cog.ban, ctx(world), world.guild.owner)


class TestMassActions:
    @pytest.mark.parametrize(
        ("cog_class", "name", "extra", "action"),
        [
            (Ban, "massban", (), "ban"),
            (Kick, "masskick", (), "kick"),
            (Mute, "massmute", ("1h",), "mute"),
            (Warnings, "masswarn", (), "warn"),
        ],
    )
    async def test_dedupes_and_acts(
        self,
        world: SimpleNamespace,
        moderate: AsyncMock,
        cog_class: type[commands.Cog],
        name: str,
        extra: tuple,
        action: str,
    ) -> None:
        cog = fakes.make_cog(cog_class, world.bot)
        daiyousei = fakes.make_member(world.guild, name="daiyousei")
        await fakes.call(
            getattr(cog, name), ctx(world), [world.cirno, daiyousei, world.cirno], *extra
        )

        args, _ = moderate.await_args_list[-1]
        assert args[1] == [world.cirno, daiyousei]
        assert args[2] == action

    @pytest.mark.parametrize(
        ("cog_class", "name", "extra"),
        [
            (Ban, "massban", ()),
            (Kick, "masskick", ()),
            (Mute, "massmute", ("1h",)),
            (Warnings, "masswarn", ()),
        ],
    )
    async def test_one_untouchable_stops_all(
        self,
        world: SimpleNamespace,
        moderate: AsyncMock,
        cog_class: type[commands.Cog],
        name: str,
        extra: tuple,
    ) -> None:
        cog = fakes.make_cog(cog_class, world.bot)
        peer = fakes.make_member(world.guild, name="sanae", top_role=world.mod_role)
        with pytest.raises(lyerrors.TakinaPermissionError):
            await fakes.call(getattr(cog, name), ctx(world), [world.cirno, peer], *extra)
        moderate.assert_not_awaited()

    async def test_needs_two(self, world: SimpleNamespace, moderate: AsyncMock) -> None:
        cog = fakes.make_cog(Ban, world.bot)
        with pytest.raises(lyerrors.TakinaUserInputError, match="at least two"):
            await fakes.call(cog.massban, ctx(world), [world.cirno])


class TestHackban:
    @pytest.fixture
    def cog(self, world: SimpleNamespace) -> Ban:
        return fakes.make_cog(Ban, world.bot)

    async def test_bans_outsider(
        self, world: SimpleNamespace, cog: Ban, moderate: AsyncMock
    ) -> None:
        outsider = fakes.make_user(name="seija", user_id=716306888492318790)
        world.guild.fetch_member.side_effect = not_found()
        world.bot.fetch_user.return_value = outsider
        world.guild.fetch_ban.side_effect = not_found()

        await fakes.call(cog.hackban, ctx(world), "<@716306888492318790>")

        args, _ = moderate.await_args_list[-1]
        assert args[1] == [outsider] and args[2] == "hackban" and args[5] is None
        await args[4](outsider, "audit")
        world.guild.ban.assert_awaited_once_with(outsider, reason="audit")

    async def test_checks_uncached_members(
        self, world: SimpleNamespace, cog: Ban, moderate: AsyncMock
    ) -> None:
        # the cache misses most members, which must not skip the role check
        peer = fakes.make_member(world.guild, name="sanae", top_role=world.mod_role)
        world.guild.fetch_member.return_value = peer

        with pytest.raises(lyerrors.TakinaPermissionError):
            await fakes.call(cog.hackban, ctx(world), str(peer.id))
        moderate.assert_not_awaited()

    async def test_not_itself(self, world: SimpleNamespace, cog: Ban, moderate: AsyncMock) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError, match="ban myself"):
            await fakes.call(cog.hackban, ctx(world), str(world.guild.me.id))

    async def test_unknown_user(
        self, world: SimpleNamespace, cog: Ban, moderate: AsyncMock
    ) -> None:
        world.guild.fetch_member.side_effect = not_found()
        world.bot.fetch_user.side_effect = not_found()
        with pytest.raises(lyerrors.TakinaNotFoundError, match="could not be found"):
            await fakes.call(cog.hackban, ctx(world), "716306888492318790")

    async def test_already_banned(
        self, world: SimpleNamespace, cog: Ban, moderate: AsyncMock
    ) -> None:
        world.guild.fetch_member.side_effect = not_found()
        world.bot.fetch_user.return_value = fakes.make_user(
            name="seija", user_id=716306888492318790
        )
        with pytest.raises(lyerrors.TakinaError, match="already banned"):
            await fakes.call(cog.hackban, ctx(world), "716306888492318790")
        moderate.assert_not_awaited()


class TestUnban:
    async def test_unbans(self, world: SimpleNamespace, moderate: AsyncMock) -> None:
        cog = fakes.make_cog(Ban, world.bot)
        seija = fakes.make_user(name="seija")
        world.bot.fetch_user.return_value = seija

        await fakes.call(cog.unban, ctx(world), str(seija.id), reason="Sorry")
        args, _ = moderate.await_args_list[-1]
        await args[4](seija, "audit")
        world.guild.unban.assert_awaited_once_with(seija, reason="audit")

    async def test_not_banned(self, world: SimpleNamespace, moderate: AsyncMock) -> None:
        cog = fakes.make_cog(Ban, world.bot)
        seija = fakes.make_user(name="seija")
        world.bot.fetch_user.return_value = seija
        world.guild.unban.side_effect = not_found()

        await fakes.call(cog.unban, ctx(world), str(seija.id))
        apply = moderate.await_args_list[-1].args[4]
        with pytest.raises(lyerrors.TakinaNotFoundError, match="is not banned"):
            await apply(seija, "audit")

    async def test_unknown_user(self, world: SimpleNamespace, moderate: AsyncMock) -> None:
        cog = fakes.make_cog(Ban, world.bot)
        world.bot.fetch_user.side_effect = not_found()
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(cog.unban, ctx(world), "716306888492318790")


class TestPurge:
    async def test_prefix(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Purge, world.bot)
        context = ctx(world)
        context.channel.purge.return_value = [object()] * 7

        await fakes.call(cog.purge, context, 7)

        context.message.delete.assert_awaited_once()
        kwargs = context.channel.purge.await_args_list[-1].kwargs
        assert kwargs["limit"] == 7 and kwargs["bulk"] is True
        # bulk deletes refuse anything older than two weeks
        assert discord.utils.utcnow() - kwargs["after"] <= timedelta(weeks=2, seconds=5)
        assert "purged 7 messages" in (fakes.sent_embed(context.send).description or "")
        assert fakes.sent(context.send)["delete_after"] == 2

    async def test_slash(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Purge, world.bot)
        context = ctx(world, interaction=True)
        context.channel.purge.return_value = []
        await fakes.call(cog.purge, context, 5)
        context.defer.assert_awaited_once_with(ephemeral=True)
        context.message.delete.assert_not_awaited()
        assert fakes.sent(context.send)["ephemeral"] is True

    async def test_wrong_channel(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Purge, world.bot)
        context = ctx(world, channel=fakes.make_channel(world.guild, discord.ForumChannel))
        with pytest.raises(lyerrors.TakinaError, match="text channel or thread"):
            await fakes.call(cog.purge, context, 5)

    def test_amount_bounded(self) -> None:
        annotation = Purge.purge.clean_params["amount"].annotation
        assert (annotation.min, annotation.max) == (1, 200)


class TestNick:
    async def test_changes(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Nick, world.bot)
        context = ctx(world)
        await fakes.call(cog.nick, context, world.cirno, nickname="Strongest")
        world.cirno.edit.assert_awaited_once_with(nick="Strongest")
        assert "**Strongest**" in (fakes.sent_embed(context.reply).description or "")

    async def test_resets(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Nick, world.bot)
        context = ctx(world)
        await fakes.call(cog.nick, context, world.cirno)
        world.cirno.edit.assert_awaited_once_with(nick=None)
        assert "has been reset" in (fakes.sent_embed(context.reply).description or "")

    async def test_own_nickname(self, world: SimpleNamespace) -> None:
        # your top role never outranks itself, yet you may rename yourself
        cog = fakes.make_cog(Nick, world.bot)
        await fakes.call(cog.nick, ctx(world), None, nickname="Miko")
        world.moderator.edit.assert_awaited_once_with(nick="Miko")

    async def test_too_long(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Nick, world.bot)
        with pytest.raises(lyerrors.TakinaUserInputError, match="32 characters"):
            await fakes.call(cog.nick, ctx(world), world.cirno, nickname="x" * 33)

    async def test_higher_member(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Nick, world.bot)
        peer = fakes.make_member(world.guild, name="sanae", top_role=world.mod_role)
        with pytest.raises(lyerrors.TakinaPermissionError):
            await fakes.call(cog.nick, ctx(world), peer, nickname="x")
        peer.edit.assert_not_awaited()


@pytest.mark.usefixtures("db")
class TestReports:
    @pytest.fixture
    def setup(self, world: SimpleNamespace) -> SimpleNamespace:
        channel = fakes.make_channel(world.guild, name="reports")
        world.bot.get_channel.side_effect = {channel.id: channel}.get
        return SimpleNamespace(cog=fakes.make_cog(Reports, world.bot), channel=channel)

    async def configure(
        self, world: SimpleNamespace, setup: SimpleNamespace, role_id: int | None = None
    ) -> None:
        await database.save(
            models.GuildSettingsModel(
                guild_id=world.guild.id,
                reports_channel_id=setup.channel.id,
                reports_notification_role_id=role_id,
            )
        )

    async def test_sends_report(self, world: SimpleNamespace, setup: SimpleNamespace) -> None:
        await self.configure(world, setup, role_id=77)
        reporter = fakes.make_member(world.guild, name="aya")
        context = fakes.make_ctx(
            bot=world.bot, guild=world.guild, author=reporter, interaction=True
        )

        await fakes.call(setup.cog.report_member, context, world.cirno, reason="Froze the lake")

        kwargs = fakes.sent(setup.channel.send)
        assert kwargs["content"] == "<@&77>"
        mentions = kwargs["allowed_mentions"]
        assert not mentions.everyone and not mentions.users
        assert [role.id for role in mentions.roles] == [77]
        embed = kwargs["embed"]
        fakes.assert_embed_fits(embed)
        assert world.cirno.mention in (embed.description or "")
        assert {field.name: field.value for field in embed.fields}["📝 Reason"] == "Froze the lake"
        assert fakes.sent(context.send)["ephemeral"] is True

    async def test_no_ping_role(self, world: SimpleNamespace, setup: SimpleNamespace) -> None:
        await self.configure(world, setup)
        context = fakes.make_ctx(bot=world.bot, guild=world.guild, interaction=True)
        await fakes.call(setup.cog.report_member, context, world.cirno, reason="x")
        kwargs = fakes.sent(setup.channel.send)
        assert kwargs["content"] is None
        assert kwargs["allowed_mentions"].roles is False

    async def test_not_yourself(self, world: SimpleNamespace, setup: SimpleNamespace) -> None:
        await self.configure(world, setup)
        context = fakes.make_ctx(
            bot=world.bot, guild=world.guild, author=world.cirno, interaction=True
        )
        with pytest.raises(lyerrors.TakinaUserInputError, match="report yourself"):
            await fakes.call(setup.cog.report_member, context, world.cirno, reason="x")

    async def test_unconfigured(self, world: SimpleNamespace, setup: SimpleNamespace) -> None:
        context = fakes.make_ctx(bot=world.bot, guild=world.guild, interaction=True)
        with pytest.raises(lyerrors.TakinaError, match="/settings guild reports"):
            await fakes.call(setup.cog.report_member, context, world.cirno, reason="x")

    async def test_deleted_channel(self, world: SimpleNamespace, setup: SimpleNamespace) -> None:
        await self.configure(world, setup)
        world.bot.get_channel.side_effect = lambda channel_id: None
        context = fakes.make_ctx(bot=world.bot, guild=world.guild, interaction=True)
        with pytest.raises(lyerrors.TakinaError, match="could not be found"):
            await fakes.call(setup.cog.report_member, context, world.cirno, reason="x")

    async def test_slash_only_and_cooled_down(
        self, world: SimpleNamespace, setup: SimpleNamespace
    ) -> None:
        command = setup.cog.report_member
        with pytest.raises(lyerrors.TakinaUserInputError, match="slash command"):
            await fakes.run_checks(command, fakes.make_ctx(bot=world.bot, guild=world.guild))

        context = fakes.make_ctx(bot=world.bot, guild=world.guild, interaction=True)
        command._prepare_cooldowns(context)
        with pytest.raises(commands.CommandOnCooldown):
            command._prepare_cooldowns(context)

    async def test_channel_moves_to_settings(
        self, world: SimpleNamespace, setup: SimpleNamespace
    ) -> None:
        context = ctx(world)
        context.bot.get_command.return_value = MagicMock()
        await fakes.call(setup.cog.report_channel, context, setup.channel, None)
        context.bot.get_command.assert_called_once_with("settings guild reports")


@pytest.mark.usefixtures("db")
class TestModLogCommands:
    @pytest.fixture
    def cog(self, world: SimpleNamespace) -> ModLog:
        return fakes.make_cog(ModLog, world.bot)

    async def add_case(
        self, world: SimpleNamespace, case_id: int, **overrides: Any
    ) -> models.ModLogCaseModel:
        fields: dict[str, Any] = {
            "guild_id": world.guild.id,
            "case_id": case_id,
            "action": "warn",
            "member_ids": [world.cirno.id],
            "member_names": ["cirno"],
            "moderator_id": world.moderator.id,
            "reason": "Freezing frogs",
            "timestamp": datetime.now(UTC),
        }
        return await database.save(models.ModLogCaseModel(**(fields | overrides)))

    async def test_case(self, world: SimpleNamespace, cog: ModLog) -> None:
        await self.add_case(world, 3)
        context = ctx(world)
        await fakes.call(cog.case, context, 3)
        embed = fakes.sent_embed(context.reply)
        assert {field.name: field.value for field in embed.fields}["Case"] == "#3"

    async def test_case_missing(self, world: SimpleNamespace, cog: ModLog) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError, match="`#3` does not exist"):
            await fakes.call(cog.case, ctx(world), 3)

    async def test_case_from_another_guild(self, world: SimpleNamespace, cog: ModLog) -> None:
        await self.add_case(world, 3, guild_id=1)
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(cog.case, ctx(world), 3)

    async def test_edit_case(
        self, world: SimpleNamespace, cog: ModLog, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        await self.add_case(world, 3)
        update = AsyncMock()
        monkeypatch.setattr(lymodlog, "update_logged_case", update)

        await fakes.call(cog.edit_case, ctx(world), 3, new_reason="Froze the whole lake")

        saved = await database.get(models.ModLogCaseModel, guild_id=world.guild.id, case_id=3)
        assert saved is not None and saved.reason == "Froze the whole lake"
        assert update.await_args_list[-1].args[1].reason == "Froze the whole lake"

    async def test_cases_for_user(self, world: SimpleNamespace, cog: ModLog) -> None:
        await self.add_case(world, 0)
        await self.add_case(world, 1, member_ids=[42])
        await self.add_case(world, 2, action="mass ban", member_ids=[42, world.cirno.id])

        context = ctx(world)
        await fakes.call(cog.cases, context, world.cirno)
        embed = fakes.sent_embed(context.reply)
        lines = (embed.description or "").split("\n")
        assert [line.split(":")[0] for line in lines] == ["`#2`", "`#0`"]
        assert embed.footer.text == "Cases for cirno"

    async def test_cases_for_departed_user(self, world: SimpleNamespace, cog: ModLog) -> None:
        # banned users are not members, which is when their cases matter most
        banned = fakes.make_user(name="seija")
        await self.add_case(world, 0, member_ids=[banned.id])
        context = ctx(world)
        await fakes.call(cog.cases, context, banned)
        assert "`#0`" in (fakes.sent_embed(context.reply).description or "")

    async def test_all_cases(self, world: SimpleNamespace, cog: ModLog) -> None:
        for number in range(3):
            await self.add_case(world, number)
        context = ctx(world)
        await fakes.call(cog.cases, context)
        assert fakes.sent_embed(context.reply).footer.text is None

    async def test_no_cases(self, world: SimpleNamespace, cog: ModLog) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(cog.cases, ctx(world))

    async def test_cases_paginate(
        self, world: SimpleNamespace, cog: ModLog, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for number in range(25):
            await self.add_case(world, number)

        send = AsyncMock()
        monkeypatch.setattr(lyviews.PaginatorView, "send", send)
        await fakes.call(cog.cases, ctx(world))
        assert len(send.await_args_list[-1].args[1]) == 3

    async def test_modcases(self, world: SimpleNamespace, cog: ModLog) -> None:
        await self.add_case(world, 0)
        await self.add_case(world, 1, moderator_id=1)
        context = ctx(world)
        await fakes.call(cog.modcases, context)
        assert (fakes.sent_embed(context.reply).description or "").count("`#") == 1

    async def test_modcases_none(self, world: SimpleNamespace, cog: ModLog) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError, match="has not performed"):
            await fakes.call(cog.modcases, ctx(world), world.cirno)

    async def test_modstats(self, world: SimpleNamespace, cog: ModLog) -> None:
        now = datetime.now(UTC)
        await self.add_case(world, 0, action="warn", timestamp=now - timedelta(days=1))
        await self.add_case(world, 1, action="mass ban", timestamp=now - timedelta(days=10))
        await self.add_case(world, 2, action="hackban", timestamp=now - timedelta(days=100))
        await self.add_case(world, 3, action="kick", timestamp=now - timedelta(days=2))
        await self.add_case(world, 4, action="mute", moderator_id=1)

        context = ctx(world)
        await fakes.call(cog.modstats, context)
        fields = {field.name: field.value or "" for field in fakes.sent_embed(context.reply).fields}
        assert (
            fields["Last 7 Days"] == "> **Warns**: 1\n> **Mutes**: 0\n> **Kicks**: 1\n> **Bans**: 0"
        )
        assert fields["Last 30 Days"].endswith("> **Bans**: 1")
        # a mass ban and a hackban are both bans
        assert fields["All Time"].endswith("> **Bans**: 2")

    async def test_channel_moves_to_settings(self, world: SimpleNamespace, cog: ModLog) -> None:
        context = ctx(world)
        context.bot.get_command.return_value = MagicMock()
        await fakes.call(cog.channel, context, fakes.make_channel(world.guild))
        context.bot.get_command.assert_called_once_with("settings guild modlog-channel")


class TestChecks:
    @pytest.mark.parametrize(
        ("cog_class", "name", "permission"),
        [
            (Ban, "ban", "Ban Members"),
            (Ban, "massban", "Ban Members"),
            (Ban, "hackban", "Ban Members"),
            (Ban, "unban", "Ban Members"),
            (Kick, "kick", "Kick Members"),
            (Kick, "masskick", "Kick Members"),
            (Mute, "mute", "Moderate Members"),
            (Mute, "massmute", "Moderate Members"),
            (Mute, "unmute", "Moderate Members"),
            (Warnings, "warn", "Moderate Members"),
            (Warnings, "masswarn", "Moderate Members"),
            (Purge, "purge", "Manage Messages"),
            (Nick, "nick", "Manage Nicknames"),
            (ModLog, "case", "Moderate Members"),
            (ModLog, "edit_case", "Moderate Members"),
            (ModLog, "cases", "Moderate Members"),
            (ModLog, "modcases", "Moderate Members"),
            (ModLog, "modstats", "Moderate Members"),
            (ModLog, "modlog channel", "Manage Guild"),
            (Reports, "report channel", "Manage Guild"),
        ],
    )
    async def test_permissions(
        self, world: SimpleNamespace, cog_class: type[commands.Cog], name: str, permission: str
    ) -> None:
        cog = fakes.make_cog(cog_class, world.bot)
        command = next(c for c in cog.walk_commands() if c.qualified_name == name)

        with pytest.raises(lyerrors.TakinaPermissionError, match=permission):
            await fakes.run_checks(
                command, fakes.make_ctx(bot=world.bot, guild=world.guild, author=world.cirno)
            )

        with pytest.raises(commands.CheckFailure):
            await fakes.run_checks(command, fakes.make_ctx(bot=world.bot))
