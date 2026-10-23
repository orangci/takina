# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors, lymodlog, lyviews
from unittest.mock import AsyncMock, MagicMock
from takina import config, database, models
from datetime import datetime, UTC
from types import SimpleNamespace
from tests import fakes
from typing import Any
import discord
import asyncio
import pytest


def forbidden() -> discord.Forbidden:
    return discord.Forbidden(MagicMock(status=403, reason="Forbidden"), "Missing Permissions")


def a_case(**overrides: Any) -> models.ModLogCaseModel:
    fields: dict[str, Any] = {
        "guild_id": 1,
        "case_id": 7,
        "action": "ban",
        "member_ids": [10],
        "member_names": ["cirno"],
        "moderator_id": 20,
        "reason": "Freezing frogs",
        "timestamp": datetime(2026, 10, 23, 14, 0, tzinfo=UTC),
    }
    return models.ModLogCaseModel(**(fields | overrides))


def field(embed: discord.Embed, name: str) -> str:
    for embed_field in embed.fields:
        if embed_field.name == name:
            return embed_field.value or ""
    raise AssertionError(f"no {name!r} field in {[f.name for f in embed.fields]}")


class TestCaseEmbed:
    def test_fields(self) -> None:
        embed = lymodlog.case_embed(a_case())
        fakes.assert_embed_fits(embed)
        assert field(embed, "Action") == "Ban"
        assert field(embed, "Case") == "#7"
        assert field(embed, "Moderator") == "<@20>"
        assert field(embed, "Target") == "<@10>"
        assert field(embed, "Reason") == "Freezing frogs"
        assert embed.timestamp == datetime(2026, 10, 23, 14, 0, tzinfo=UTC)

    def test_duration(self) -> None:
        embed = lymodlog.case_embed(a_case(action="mute", duration="4w"))
        assert field(embed, "Action") == "Mute (4w)"

    def test_mass_action(self) -> None:
        embed = lymodlog.case_embed(
            a_case(action="mass ban", member_ids=[1, 2], mass_action=True), "https://x/a.png"
        )
        assert field(embed, "Targets") == "<@1>, <@2>"
        assert field(embed, "Action") == "Mass Ban"
        # one thumbnail cannot stand for several targets
        assert embed.thumbnail.url is None

    def test_thumbnail(self) -> None:
        embed = lymodlog.case_embed(a_case(), "https://cdn.discordapp.com/cirno.png")
        assert embed.thumbnail.url == "https://cdn.discordapp.com/cirno.png"

    def test_no_targets(self) -> None:
        assert field(lymodlog.case_embed(a_case(member_ids=[])), "Target") == "Unknown"

    def test_edited(self) -> None:
        editor = fakes.make_user(name="eiki")
        embed = lymodlog.case_embed(a_case(), edited_by=editor)
        assert field(embed, "Edited").startswith(f"By {editor.mention} <t:")

    def test_longest_reason_fits(self) -> None:
        embed = lymodlog.case_embed(a_case(reason="r" * lymodlog.MAX_REASON_LENGTH))
        fakes.assert_embed_fits(embed)


class TestMassTargets:
    def test_dedupes(self) -> None:
        cirno, daiyousei = fakes.make_user(name="cirno"), fakes.make_user(name="daiyousei")
        assert lymodlog.mass_targets([cirno, daiyousei, cirno], "ban") == [cirno, daiyousei]

    def test_needs_two(self) -> None:
        cirno = fakes.make_user(name="cirno")
        with pytest.raises(lyerrors.TakinaUserInputError, match="at least two members to ban"):
            lymodlog.mass_targets([cirno, cirno], "ban")

    def test_needs_any(self) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError):
            lymodlog.mass_targets([], "kick")

    def test_cap(self) -> None:
        targets = [fakes.make_user() for _ in range(lymodlog.MAX_MASS_TARGETS + 1)]
        with pytest.raises(lyerrors.TakinaUserInputError, match="more than 10 members"):
            lymodlog.mass_targets(targets, "mute")

    def test_exactly_the_cap(self) -> None:
        targets = [fakes.make_user() for _ in range(lymodlog.MAX_MASS_TARGETS)]
        assert len(lymodlog.mass_targets(targets, "warn")) == lymodlog.MAX_MASS_TARGETS


@pytest.mark.usefixtures("db")
class TestCaseIds:
    async def test_first_case_is_zero(self) -> None:
        assert await lymodlog.next_case_id(1) == 0

    async def test_counts_per_guild(self) -> None:
        await database.save(a_case(guild_id=1, case_id=0))
        await database.save(a_case(guild_id=1, case_id=5))
        await database.save(a_case(guild_id=2, case_id=40))
        assert await lymodlog.next_case_id(1) == 6
        assert await lymodlog.next_case_id(3) == 0


@pytest.fixture
def logging_guild() -> SimpleNamespace:
    guild = fakes.make_guild()
    channel = fakes.make_channel(guild, name="mod-log")
    channel.send.return_value = MagicMock(spec=discord.Message, id=999)
    guild.get_channel.side_effect = lambda channel_id: channel if channel_id == channel.id else None
    return SimpleNamespace(guild=guild, channel=channel)


@pytest.mark.usefixtures("db")
class TestLogAction:
    async def test_saves_without_a_channel(self, logging_guild: SimpleNamespace) -> None:
        cirno = fakes.make_user(name="cirno")
        moderator = fakes.make_user(name="reimu")

        message = await lymodlog.log_action(
            logging_guild.guild, "warn", [cirno], "Freezing frogs", moderator
        )

        assert message is None
        (saved,) = await database.get_all(models.ModLogCaseModel)
        assert saved.guild_id == logging_guild.guild.id
        assert saved.case_id == 0
        assert saved.member_ids == [cirno.id]
        assert saved.member_names == ["cirno"]
        assert saved.moderator_id == moderator.id
        assert saved.log_message_id is None

    async def test_posts_and_remembers_message(self, logging_guild: SimpleNamespace) -> None:
        await database.save(
            models.GuildSettingsModel(
                guild_id=logging_guild.guild.id, modlog_channel_id=logging_guild.channel.id
            )
        )

        message = await lymodlog.log_action(
            logging_guild.guild, "mute", [fakes.make_user()], "Spam", fakes.make_user(), "1h"
        )

        assert message is logging_guild.channel.send.return_value
        embed = fakes.sent_embed(logging_guild.channel.send)
        assert field(embed, "Action") == "Mute (1h)"

        (saved,) = await database.get_all(models.ModLogCaseModel)
        assert saved.log_channel_id == logging_guild.channel.id
        assert saved.log_message_id == 999
        assert saved.duration == "1h"

    async def test_broken_channel_keeps_the_case(self, logging_guild: SimpleNamespace) -> None:
        await database.save(
            models.GuildSettingsModel(
                guild_id=logging_guild.guild.id, modlog_channel_id=logging_guild.channel.id
            )
        )
        logging_guild.channel.send.side_effect = forbidden()

        message = await lymodlog.log_action(
            logging_guild.guild, "kick", [fakes.make_user()], "Bye", fakes.make_user()
        )

        assert message is None
        assert len(await database.get_all(models.ModLogCaseModel)) == 1

    async def test_missing_channel(self, logging_guild: SimpleNamespace) -> None:
        await database.save(
            models.GuildSettingsModel(guild_id=logging_guild.guild.id, modlog_channel_id=12345)
        )
        assert (
            await lymodlog.log_action(
                logging_guild.guild, "kick", [fakes.make_user()], "Bye", fakes.make_user()
            )
            is None
        )

    async def test_case_ids_count_up(self, logging_guild: SimpleNamespace) -> None:
        for _ in range(3):
            await lymodlog.log_action(
                logging_guild.guild, "warn", [fakes.make_user()], "Again", fakes.make_user()
            )
        cases = await database.get_all(models.ModLogCaseModel)
        assert sorted(found.case_id for found in cases) == [0, 1, 2]

    async def test_concurrent_actions_get_distinct_ids(
        self, logging_guild: SimpleNamespace
    ) -> None:
        await asyncio.gather(
            *(
                lymodlog.log_action(
                    logging_guild.guild, "warn", [fakes.make_user()], "Raid", fakes.make_user()
                )
                for _ in range(4)
            )
        )
        cases = await database.get_all(models.ModLogCaseModel)
        assert sorted(found.case_id for found in cases) == [0, 1, 2, 3]

    async def test_gives_up_eventually(
        self, logging_guild: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        await database.save(a_case(guild_id=logging_guild.guild.id, case_id=0))
        # a stuck counter, as if another action always claimed the id first
        monkeypatch.setattr(lymodlog, "next_case_id", AsyncMock(return_value=0))

        with pytest.raises(lyerrors.TakinaError, match="Could not allocate"):
            await lymodlog.log_action(
                logging_guild.guild, "warn", [fakes.make_user()], "Raid", fakes.make_user()
            )


class TestUpdateLoggedCase:
    async def test_edits_the_posted_message(self, logging_guild: SimpleNamespace) -> None:
        partial = MagicMock(spec=discord.PartialMessage)
        logging_guild.channel.get_partial_message.return_value = partial
        editor = fakes.make_user(name="eiki")

        found = a_case(log_channel_id=logging_guild.channel.id, log_message_id=999, reason="New")
        await lymodlog.update_logged_case(logging_guild.guild, found, editor)

        logging_guild.channel.get_partial_message.assert_called_once_with(999)
        embed = partial.edit.await_args_list[-1].kwargs["embed"]
        assert field(embed, "Reason") == "New"
        assert editor.mention in field(embed, "Edited")

    async def test_unposted_case(self, logging_guild: SimpleNamespace) -> None:
        await lymodlog.update_logged_case(logging_guild.guild, a_case(), fakes.make_user())
        logging_guild.guild.get_channel.assert_not_called()

    async def test_deleted_message_is_ignored(self, logging_guild: SimpleNamespace) -> None:
        partial = MagicMock(spec=discord.PartialMessage)
        partial.edit.side_effect = discord.NotFound(MagicMock(status=404), "Unknown Message")
        logging_guild.channel.get_partial_message.return_value = partial

        found = a_case(log_channel_id=logging_guild.channel.id, log_message_id=999)
        await lymodlog.update_logged_case(logging_guild.guild, found, fakes.make_user())


@pytest.fixture
def confirmation(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """The confirm buttons, pressed in advance, and the moderation log, recorded."""
    state = SimpleNamespace(confirmed=True, success=None, logged=[])

    async def prompt(view: lyviews.ModerationConfirmationView) -> bool:
        state.prompted = view
        return state.confirmed

    async def edit_success(view: lyviews.ModerationConfirmationView, embed: discord.Embed) -> None:
        state.success = embed

    async def log_action(*args: Any, **kwargs: Any) -> None:
        state.logged.append((args, kwargs))

    monkeypatch.setattr(lyviews.ModerationConfirmationView, "prompt", prompt)
    monkeypatch.setattr(lyviews.ModerationConfirmationView, "edit_success", edit_success)
    monkeypatch.setattr(lymodlog, "log_action", log_action)
    return state


class TestModerate:
    def ctx(self) -> MagicMock:
        guild = fakes.make_guild()
        return fakes.make_ctx(guild=guild, author=fakes.make_member(guild, name="reimu"))

    async def test_cancelled_does_nothing(self, confirmation: SimpleNamespace) -> None:
        confirmation.confirmed = False
        target = fakes.make_user(name="cirno")
        apply = AsyncMock()

        await lymodlog.moderate(self.ctx(), [target], "ban", "Frogs", apply, "Bye", dm_first=True)

        apply.assert_not_awaited()
        target.send.assert_not_awaited()
        assert confirmation.logged == []

    async def test_single_action(self, confirmation: SimpleNamespace) -> None:
        ctx = self.ctx()
        target = fakes.make_user(name="cirno")
        apply = AsyncMock()

        await lymodlog.moderate(ctx, [target], "ban", "Frogs", apply, "You were banned.")

        apply.assert_awaited_once_with(target, "Banned by reimu for: Frogs")
        dm = target.send.await_args_list[-1].kwargs["embed"].description
        assert dm.startswith("You were banned.") and "**Reason**: Frogs" in dm

        description = confirmation.success.description
        assert description.startswith(
            f"{config.emojis.SUCCESS} Successfully banned {target.mention}."
        )
        assert "**Reason**: Frogs" in description
        assert "**Moderator**: reimu" in description
        assert confirmation.success.footer.text is None

        (args, kwargs) = confirmation.logged[0]
        assert args == (ctx.guild, "ban", [target], "Frogs", ctx.author, None)
        assert kwargs == {"mass_action": False}

    async def test_confirmation_names_targets(self, confirmation: SimpleNamespace) -> None:
        targets = [fakes.make_user(name="cirno"), fakes.make_user(name="daiyousei")]
        await lymodlog.moderate(self.ctx(), targets, "kick", "Pranks", AsyncMock(), None)

        view = confirmation.prompted
        assert view.action == "mass kick"
        assert view.member == ", ".join(target.mention for target in targets)

    async def test_dm_first_order(self, confirmation: SimpleNamespace) -> None:
        order: list[str] = []
        target = fakes.make_user(name="cirno")
        target.send.side_effect = lambda **kwargs: order.append("dm")

        async def apply(member: Any, reason: str) -> None:
            order.append("ban")

        await lymodlog.moderate(self.ctx(), [target], "ban", "x", apply, "Bye", dm_first=True)
        assert order == ["dm", "ban"]

    async def test_dm_after_by_default(self, confirmation: SimpleNamespace) -> None:
        order: list[str] = []
        target = fakes.make_user(name="cirno")
        target.send.side_effect = lambda **kwargs: order.append("dm")

        async def apply(member: Any, reason: str) -> None:
            order.append("mute")

        await lymodlog.moderate(self.ctx(), [target], "mute", "x", apply, "Shush")
        assert order == ["mute", "dm"]

    async def test_failed_action_deletes_early_dm(self, confirmation: SimpleNamespace) -> None:
        target = fakes.make_user(name="cirno")
        dm = MagicMock(spec=discord.Message)
        target.send.return_value = dm

        with pytest.raises(lyerrors.TakinaError, match="I could not ban"):
            await lymodlog.moderate(
                self.ctx(),
                [target],
                "ban",
                "x",
                AsyncMock(side_effect=forbidden()),
                "Bye",
                dm_first=True,
            )

        dm.delete.assert_awaited_once()
        assert confirmation.logged == []

    async def test_undeletable_dm_is_fine(self, confirmation: SimpleNamespace) -> None:
        target = fakes.make_user(name="cirno")
        target.send.return_value.delete.side_effect = forbidden()

        with pytest.raises(lyerrors.TakinaError):
            await lymodlog.moderate(
                self.ctx(),
                [target],
                "ban",
                "x",
                AsyncMock(side_effect=forbidden()),
                "Bye",
                dm_first=True,
            )

    async def test_closed_dms_noted(self, confirmation: SimpleNamespace) -> None:
        target = fakes.make_user(name="cirno")
        target.send.side_effect = forbidden()

        await lymodlog.moderate(self.ctx(), [target], "warn", "x", None, "Warned")
        assert confirmation.success.footer.text == "I was unable to DM the user."

    async def test_no_dm_no_footer(self, confirmation: SimpleNamespace) -> None:
        target = fakes.make_user(name="cirno")
        await lymodlog.moderate(self.ctx(), [target], "hackban", "x", AsyncMock(), None)
        target.send.assert_not_awaited()
        assert confirmation.success.footer.text is None

    async def test_warn_has_no_action(self, confirmation: SimpleNamespace) -> None:
        target = fakes.make_user(name="cirno")
        await lymodlog.moderate(self.ctx(), [target], "warn", "Be nice", None, "Warned")
        assert "Successfully warned" in confirmation.success.description
        assert len(confirmation.logged) == 1

    async def test_duration(self, confirmation: SimpleNamespace) -> None:
        target = fakes.make_user(name="cirno")
        await lymodlog.moderate(
            self.ctx(), [target], "mute", "x", AsyncMock(), None, duration="12h"
        )
        assert f"Successfully muted {target.mention} for 12h." in confirmation.success.description
        assert confirmation.logged[0][0][5] == "12h"

    async def test_mass_partial_failure(self, confirmation: SimpleNamespace) -> None:
        cirno, daiyousei, rumia = (
            fakes.make_user(name=name) for name in ("cirno", "daiyousei", "rumia")
        )
        rumia.send.side_effect = forbidden()

        async def apply(member: Any, reason: str) -> None:
            if member is daiyousei:
                raise forbidden()

        await lymodlog.moderate(self.ctx(), [cirno, daiyousei, rumia], "kick", "x", apply, "Bye")

        description = confirmation.success.description
        assert (
            f"Successfully kicked 2 of 3 members: {cirno.mention}, {rumia.mention}." in description
        )
        assert f"**Failed**: {daiyousei.mention} (Missing Permissions)" in description
        assert confirmation.success.footer.text == "I was unable to DM 1 user(s)."

        (args, kwargs) = confirmation.logged[0]
        assert args[1] == "mass kick"
        assert args[2] == [cirno, rumia]
        assert kwargs == {"mass_action": True}

    async def test_mass_success(self, confirmation: SimpleNamespace) -> None:
        targets = [fakes.make_user() for _ in range(3)]
        await lymodlog.moderate(self.ctx(), targets, "ban", "Raid", AsyncMock(), None)
        assert "Successfully banned the following 3 members" in confirmation.success.description

    async def test_all_failed(self, confirmation: SimpleNamespace) -> None:
        targets = [fakes.make_user(name="cirno"), fakes.make_user(name="daiyousei")]
        with pytest.raises(lyerrors.TakinaError) as error:
            await lymodlog.moderate(
                self.ctx(), targets, "ban", "x", AsyncMock(side_effect=forbidden()), None
            )
        assert all(target.mention in error.value.message for target in targets)
        assert confirmation.logged == []

    async def test_takina_errors_from_apply_propagate(self, confirmation: SimpleNamespace) -> None:
        # unban raises not found for someone who is not banned, which must reach the user as is
        apply = AsyncMock(side_effect=lyerrors.TakinaNotFoundError("cirno is not banned."))
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await lymodlog.moderate(self.ctx(), [fakes.make_user()], "unban", "x", apply, None)
