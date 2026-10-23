# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.util.reminders import MAX_REMINDERS, Reminders
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta, UTC
from takina.libs import lyerrors, lyviews
from takina import database, models
from types import SimpleNamespace
from tests import fakes
from typing import Any
import discord
import pytest

pytestmark = pytest.mark.usefixtures("db")


@pytest.fixture
def world() -> SimpleNamespace:
    bot = fakes.make_bot()
    user = fakes.make_user(name="sakuya")
    return SimpleNamespace(bot=bot, user=user, cog=fakes.make_cog(Reminders, bot))


def ctx(world: SimpleNamespace, *, interaction: bool = False) -> Any:
    return fakes.make_ctx(bot=world.bot, author=world.user, interaction=interaction)


async def reminders(world: SimpleNamespace) -> list[models.ReminderModel]:
    return await database.get_all(models.ReminderModel, user_id=world.user.id)


class TestSet:
    async def test_sets(self, world: SimpleNamespace) -> None:
        context = ctx(world)
        before = datetime.now(UTC)
        await fakes.call(world.cog.reminder_set, context, "2h", reminder="wind the clocks")

        (saved,) = await reminders(world)
        assert saved.reminder == "wind the clocks"
        assert timedelta(hours=2) <= saved.remind_at - before < timedelta(hours=2, seconds=5)

        description = fakes.sent_embed(context.reply).description or ""
        assert "Reminder set for 2h from now" in description
        assert f"`{saved.id}`" in description
        assert "arrives by DM" in description

    async def test_prefix_joins_split_durations(self, world: SimpleNamespace) -> None:
        # ".reminder set 1h 30m feed the cat" arrives as time="1h", reminder="30m feed the cat"
        context = ctx(world)
        await fakes.call(world.cog.reminder_set, context, "1h", reminder="30m 5s feed the cat")
        (saved,) = await reminders(world)
        assert saved.reminder == "feed the cat"
        assert "Reminder set for 1h 30m 5s" in (fakes.sent_embed(context.reply).description or "")

    async def test_slash_keeps_the_text(self, world: SimpleNamespace) -> None:
        await fakes.call(
            world.cog.reminder_set, ctx(world, interaction=True), "1h", reminder="30m of reading"
        )
        (saved,) = await reminders(world)
        assert saved.reminder == "30m of reading"

    async def test_number_words_stay(self, world: SimpleNamespace) -> None:
        await fakes.call(world.cog.reminder_set, ctx(world), "1h", reminder="buy 5 knives")
        (saved,) = await reminders(world)
        assert saved.reminder == "buy 5 knives"

    async def test_lone_duration_word_stays(self, world: SimpleNamespace) -> None:
        # nothing would be left to remind about, so the word is the reminder
        await fakes.call(world.cog.reminder_set, ctx(world), "1h", reminder="30m")
        (saved,) = await reminders(world)
        assert saved.reminder == "30m"

    @pytest.mark.parametrize(
        ("time", "message"), [("4m", "minimum duration"), ("2y", "at most a year")]
    )
    async def test_bounds(self, world: SimpleNamespace, time: str, message: str) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError, match=message):
            await fakes.call(world.cog.reminder_set, ctx(world), time, reminder="x")

    @pytest.mark.parametrize("time", ["5m", "1y"])
    async def test_bounds_inclusive(self, world: SimpleNamespace, time: str) -> None:
        await fakes.call(world.cog.reminder_set, ctx(world), time, reminder="x")

    async def test_bad_duration(self, world: SimpleNamespace) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError, match="Invalid duration"):
            await fakes.call(world.cog.reminder_set, ctx(world), "soon", reminder="x")

    async def test_limit(self, world: SimpleNamespace) -> None:
        for number in range(MAX_REMINDERS):
            await fakes.call(world.cog.reminder_set, ctx(world), "1h", reminder=f"knife {number}")

        with pytest.raises(lyerrors.TakinaError, match="25 active reminders"):
            await fakes.call(world.cog.reminder_set, ctx(world), "1h", reminder="one more")

    async def test_limit_is_per_user(self, world: SimpleNamespace) -> None:
        for number in range(MAX_REMINDERS):
            await fakes.call(world.cog.reminder_set, ctx(world), "1h", reminder=f"knife {number}")
        other = fakes.make_ctx(bot=world.bot, author=fakes.make_user(name="remilia"))
        await fakes.call(world.cog.reminder_set, other, "1h", reminder="tea")


class TestListAndDelete:
    async def test_list_empty(self, world: SimpleNamespace) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError, match="no active reminders"):
            await fakes.call(world.cog.reminder_list, ctx(world))

    async def test_list_sorted(self, world: SimpleNamespace) -> None:
        await fakes.call(world.cog.reminder_set, ctx(world), "3h", reminder="late")
        await fakes.call(world.cog.reminder_set, ctx(world), "1h", reminder="early")

        context = ctx(world)
        await fakes.call(world.cog.reminder_list, context)
        description = fakes.sent_embed(context.reply).description or ""
        assert description.index("early") < description.index("late")

    async def test_list_paginates(
        self, world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for number in range(10):
            await fakes.call(
                world.cog.reminder_set, ctx(world), "1h", reminder="r" * 300 + str(number)
            )

        send = AsyncMock()
        monkeypatch.setattr(lyviews.PaginatorView, "send", send)
        await fakes.call(world.cog.reminder_list, ctx(world))

        embeds = send.await_args_list[-1].args[1]
        assert len(embeds) > 1
        for embed in embeds:
            fakes.assert_embed_fits(embed)
        assert sum((embed.description or "").count("> **ID**") for embed in embeds) == 10

    async def test_only_own_reminders(self, world: SimpleNamespace) -> None:
        other = fakes.make_ctx(bot=world.bot, author=fakes.make_user(name="remilia"))
        await fakes.call(world.cog.reminder_set, other, "1h", reminder="tea")
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(world.cog.reminder_list, ctx(world))

    async def test_delete(self, world: SimpleNamespace) -> None:
        await fakes.call(world.cog.reminder_set, ctx(world), "1h", reminder="x")
        (saved,) = await reminders(world)

        await fakes.call(world.cog.reminder_delete, ctx(world), saved.id)
        assert await reminders(world) == []

    async def test_cannot_delete_someone_elses(self, world: SimpleNamespace) -> None:
        other = fakes.make_ctx(bot=world.bot, author=fakes.make_user(name="remilia"))
        await fakes.call(world.cog.reminder_set, other, "1h", reminder="tea")
        (theirs,) = await database.get_all(models.ReminderModel)

        with pytest.raises(lyerrors.TakinaNotFoundError, match="No reminder found"):
            await fakes.call(world.cog.reminder_delete, ctx(world), theirs.id)
        assert len(await database.get_all(models.ReminderModel)) == 1


class TestDelivery:
    async def due(
        self, world: SimpleNamespace, *, ago: timedelta = timedelta(minutes=1)
    ) -> models.ReminderModel:
        return await database.save(
            models.ReminderModel(
                user_id=world.user.id, reminder="wind the clocks", remind_at=datetime.now(UTC) - ago
            )
        )

    async def tick(self, world: SimpleNamespace) -> None:
        await world.cog._check_reminders.coro(world.cog)

    async def test_due_reminders_sent_and_removed(self, world: SimpleNamespace) -> None:
        world.bot.get_user.return_value = world.user
        await self.due(world)
        await self.tick(world)

        assert "**Reminder**: wind the clocks" in (
            fakes.sent_embed(world.user.send).description or ""
        )
        assert await reminders(world) == []

    async def test_future_reminders_wait(self, world: SimpleNamespace) -> None:
        world.bot.get_user.return_value = world.user
        await self.due(world, ago=-timedelta(hours=1))
        await self.tick(world)
        world.user.send.assert_not_awaited()
        assert len(await reminders(world)) == 1

    async def test_uncached_user_is_fetched(self, world: SimpleNamespace) -> None:
        world.bot.fetch_user.return_value = world.user
        await self.due(world)
        await self.tick(world)
        world.bot.fetch_user.assert_awaited_once_with(world.user.id)
        world.user.send.assert_awaited_once()

    async def test_deleted_user_dropped(self, world: SimpleNamespace) -> None:
        world.bot.fetch_user.side_effect = discord.NotFound(MagicMock(status=404), "gone")
        await self.due(world)
        await self.tick(world)
        assert await reminders(world) == []

    async def test_closed_dms_dropped(self, world: SimpleNamespace) -> None:
        world.bot.get_user.return_value = world.user
        world.user.send.side_effect = discord.Forbidden(MagicMock(status=403), "closed")
        await self.due(world)
        await self.tick(world)
        assert await reminders(world) == []

    async def test_transient_failure_retried(self, world: SimpleNamespace) -> None:
        world.bot.get_user.return_value = world.user
        world.user.send.side_effect = discord.HTTPException(MagicMock(status=500), "oops")
        await self.due(world)
        await self.tick(world)
        assert len(await reminders(world)) == 1

    async def test_one_failure_does_not_stop_others(self, world: SimpleNamespace) -> None:
        broken, fine = fakes.make_user(), fakes.make_user()
        broken.send.side_effect = discord.HTTPException(MagicMock(status=500), "oops")
        world.bot.get_user.side_effect = {broken.id: broken, fine.id: fine}.get

        for user, ago in ((broken, timedelta(minutes=2)), (fine, timedelta(minutes=1))):
            await database.save(
                models.ReminderModel(
                    user_id=user.id, reminder="x", remind_at=datetime.now(UTC) - ago
                )
            )

        await self.tick(world)
        fine.send.assert_awaited_once()

    async def test_database_outage_keeps_loop_alive(
        self, world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(database, "get_all", AsyncMock(side_effect=OSError("postgres is down")))
        await self.tick(world)
