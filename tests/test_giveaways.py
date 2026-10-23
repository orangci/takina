# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.fun.giveaways import GiveawayView, Giveaways, giveaway_embed
from takina.cogs.fun import giveaways as giveaways_module
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta, UTC
from takina import database, models
from types import SimpleNamespace
from takina.libs import lyerrors
from tests import fakes
from typing import Any
import discord
import asyncio
import pytest

pytestmark = pytest.mark.usefixtures("db")


@pytest.fixture
def world(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    monkeypatch.setattr(giveaways_module, "EDIT_DELAY", 0)
    guild = fakes.make_guild()
    channel = fakes.make_channel(guild, name="giveaways")
    posted = MagicMock(spec=discord.Message, id=4242)
    posted.channel = channel
    channel.send.return_value = posted
    channel.fetch_message.return_value = posted

    bot = fakes.make_bot()
    bot.get_channel.side_effect = {channel.id: channel}.get
    cog = fakes.make_cog(Giveaways, bot)
    host = fakes.make_member(
        guild, name="yuyuko", permissions=discord.Permissions(manage_events=True)
    )
    return SimpleNamespace(guild=guild, channel=channel, posted=posted, bot=bot, cog=cog, host=host)


def ctx(world: SimpleNamespace, *, interaction: bool = False) -> Any:
    return fakes.make_ctx(
        bot=world.bot,
        guild=world.guild,
        author=world.host,
        channel=world.channel,
        interaction=interaction,
    )


async def start(world: SimpleNamespace, **kwargs: Any) -> models.GiveawayModel:
    arguments = {
        "duration": "1h",
        "title": "Cherry blossoms",
        "description": None,
        "winners": 1,
    } | kwargs
    await fakes.call(world.cog.start, ctx(world), **arguments)
    latest = await world.cog.next_id(world.guild.id) - 1
    return await world.cog.get_giveaway((world.guild.id, latest))


async def enter(
    world: SimpleNamespace, giveaway: models.GiveawayModel, user_ids: list[int]
) -> None:
    for user_id in user_ids:
        await database.toggle_in_array(
            models.GiveawayModel,
            "participants",
            user_id,
            guild_id=giveaway.guild_id,
            id=giveaway.id,
        )


class TestEmbed:
    def giveaway(self, **overrides: Any) -> models.GiveawayModel:
        fields: dict[str, Any] = {
            "guild_id": 1,
            "id": 3,
            "channel_id": 2,
            "message_id": 4,
            "title": "Cherry blossoms",
            "description": "Saigyou Ayakashi petals",
            "ends_at": datetime(2026, 10, 23, 14, 0, tzinfo=UTC),
            "participants": [1, 2, 3],
            "winners": 2,
        }
        return models.GiveawayModel(**(fields | overrides))

    def test_running(self) -> None:
        embed = giveaway_embed(self.giveaway())
        fakes.assert_embed_fits(embed)
        description = embed.description or ""
        assert embed.title == "Cherry blossoms"
        assert description.startswith("Saigyou Ayakashi petals\n")
        assert "**Ends**: <t:1792764000>" in description
        assert "**Giveaway ID**: `#3`" in description
        assert "**Participants**: 3" in description
        assert "**Winners**: 2" in description

    def test_ended(self) -> None:
        description = giveaway_embed(self.giveaway(ended=True, winner_ids=[1, 2])).description or ""
        assert "**Ended**:" in description
        assert "**Winners**: <@1>, <@2>" in description

    def test_ended_empty(self) -> None:
        description = giveaway_embed(self.giveaway(ended=True, participants=[])).description or ""
        assert "ended with no participants" in description

    def test_no_description(self) -> None:
        assert (giveaway_embed(self.giveaway(description="")).description or "").startswith(
            "\n> **Ends**"
        )

    def test_longest_inputs_fit(self) -> None:
        fakes.assert_embed_fits(
            giveaway_embed(
                self.giveaway(
                    title="t" * 256,
                    description="d" * giveaways_module.MAX_DESCRIPTION_LENGTH,
                    ended=True,
                    winner_ids=list(range(10**17, 10**17 + giveaways_module.MAX_WINNERS)),
                )
            )
        )


class TestStart:
    async def test_starts(self, world: SimpleNamespace) -> None:
        # the cog drops the microseconds, so the second may tick over between the two clocks
        before = datetime.now(UTC).replace(microsecond=0)
        giveaway = await start(world, description="Petals", winners=3)
        after = datetime.now(UTC)

        assert giveaway.id == 1
        assert giveaway.message_id == 4242
        assert giveaway.channel_id == world.channel.id
        assert giveaway.winners == 3
        assert not giveaway.ended
        assert before + timedelta(hours=1) <= giveaway.ends_at <= after + timedelta(hours=1)

        kwargs = fakes.sent(world.channel.send)
        assert isinstance(kwargs["view"], GiveawayView)
        assert kwargs["view"].join_button.custom_id == f"giveaway:{world.guild.id}:1:join"
        world.bot.add_view.assert_called_once_with(kwargs["view"], message_id=4242)

    async def test_ids_count_up_per_guild(self, world: SimpleNamespace) -> None:
        assert (await start(world)).id == 1
        assert (await start(world)).id == 2
        other = fakes.make_guild()
        await fakes.call(
            world.cog.start,
            fakes.make_ctx(bot=world.bot, guild=other, channel=world.channel),
            "1h",
            "Elsewhere",
        )
        assert await world.cog.next_id(other.id) == 2

    async def test_concurrent_starts_get_distinct_ids(self, world: SimpleNamespace) -> None:
        await asyncio.gather(
            *(fakes.call(world.cog.start, ctx(world), "1h", "Rush") for _ in range(4))
        )
        rows = await database.get_all(models.GiveawayModel, guild_id=world.guild.id)
        assert sorted(row.id for row in rows) == [1, 2, 3, 4]

    async def test_prefix_no_confirmation(self, world: SimpleNamespace) -> None:
        context = ctx(world)
        await fakes.call(world.cog.start, context, "1h", "Quiet")
        context.send.assert_not_awaited()
        context.message.add_reaction.assert_not_awaited()

    async def test_slash_confirms_privately(self, world: SimpleNamespace) -> None:
        context = ctx(world, interaction=True)
        await fakes.call(world.cog.start, context, "1h", "Loud")
        assert fakes.sent(context.send)["ephemeral"] is True

    async def test_failed_send_leaves_no_row(self, world: SimpleNamespace) -> None:
        world.channel.send.side_effect = discord.Forbidden(MagicMock(status=403), "no")
        with pytest.raises(discord.Forbidden):
            await fakes.call(world.cog.start, ctx(world), "1h", "Doomed")
        assert await database.get_all(models.GiveawayModel) == []

    @pytest.mark.parametrize(
        ("duration", "message"),
        [
            ("0s", "greater than zero"),
            ("1y", "less than one year"),
            ("forever", "Invalid duration"),
        ],
    )
    async def test_durations(self, world: SimpleNamespace, duration: str, message: str) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError, match=message):
            await fakes.call(world.cog.start, ctx(world), duration, "x")

    async def test_long_description(self, world: SimpleNamespace) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError, match="2,000 characters"):
            await fakes.call(world.cog.start, ctx(world), "1h", "x", "d" * 2001)

    async def test_active_limit(self, world: SimpleNamespace) -> None:
        for number in range(giveaways_module.MAXIMUM_GUILD_GIVEAWAYS):
            await database.save(
                models.GiveawayModel(
                    guild_id=world.guild.id,
                    id=number + 1,
                    channel_id=1,
                    message_id=1,
                    title="x",
                    description="",
                    ends_at=datetime.now(UTC) + timedelta(hours=1),
                )
            )
        with pytest.raises(lyerrors.TakinaError, match="maximum number of active giveaways"):
            await fakes.call(world.cog.start, ctx(world), "1h", "One too many")

    @pytest.mark.parametrize("kind", [discord.VoiceChannel, discord.StageChannel, discord.Thread])
    async def test_other_channel_kinds_draw(self, world: SimpleNamespace, kind: type) -> None:
        channel = fakes.make_channel(world.guild, kind)
        channel.send.return_value = world.posted
        channel.fetch_message.return_value = world.posted
        world.bot.get_channel.side_effect = {channel.id: channel}.get

        await fakes.call(
            world.cog.start,
            fakes.make_ctx(bot=world.bot, guild=world.guild, channel=channel),
            "1h",
            "Voice",
        )
        giveaway = await world.cog.get_giveaway((world.guild.id, 1))
        await enter(world, giveaway, [7])

        await fakes.call(world.cog.stop, ctx(world), 1)
        assert (await world.cog.get_giveaway((world.guild.id, 1))).winner_ids == [7]


class TestJoinButton:
    async def press(self, world: SimpleNamespace, giveaway: models.GiveawayModel, user: Any) -> Any:
        view = GiveawayView(world.cog, giveaway.guild_id, giveaway.id)
        interaction = fakes.make_interaction(user=user)
        await view.join_button.callback(interaction)
        return interaction

    async def test_enter_and_withdraw(self, world: SimpleNamespace) -> None:
        giveaway = await start(world)
        user = fakes.make_user(name="youmu")

        interaction = await self.press(world, giveaway, user)
        assert "You have entered giveaway `#1`" in (
            fakes.sent_embed(interaction.response.send_message).description or ""
        )
        assert fakes.sent(interaction.response.send_message)["ephemeral"] is True
        assert (await world.cog.get_giveaway((world.guild.id, 1))).participants == [user.id]

        interaction = await self.press(world, giveaway, user)
        assert "withdrawn" in (
            fakes.sent_embed(interaction.response.send_message).description or ""
        )
        assert (await world.cog.get_giveaway((world.guild.id, 1))).participants == []

    async def test_ended_giveaway(self, world: SimpleNamespace) -> None:
        giveaway = await start(world)
        await fakes.call(world.cog.stop, ctx(world), giveaway.id)

        interaction = await self.press(world, giveaway, fakes.make_user())
        assert "already ended" in (
            fakes.sent_embed(interaction.response.send_message).description or ""
        )
        assert (await world.cog.get_giveaway((world.guild.id, 1))).participants == []

    async def test_burst_is_one_edit(
        self, world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(giveaways_module, "EDIT_DELAY", 0.2)
        giveaway = await start(world)
        world.posted.edit.reset_mock()

        await asyncio.gather(*(self.press(world, giveaway, fakes.make_user()) for _ in range(10)))
        pending = list(world.cog._pending_updates.values())
        assert len(pending) == 1
        await asyncio.gather(*pending)

        world.posted.edit.assert_awaited_once()
        embed = world.posted.edit.await_args_list[-1].kwargs["embed"]
        assert "**Participants**: 10" in (embed.description or "")

    async def test_stale_update_skipped_after_end(self, world: SimpleNamespace) -> None:
        giveaway = await start(world)
        await self.press(world, giveaway, fakes.make_user())
        pending = list(world.cog._pending_updates.values())

        await fakes.call(world.cog.stop, ctx(world), giveaway.id)
        world.posted.edit.reset_mock()
        await asyncio.gather(*pending)
        world.posted.edit.assert_not_awaited()


class TestStop:
    async def test_draws_winners(self, world: SimpleNamespace) -> None:
        giveaway = await start(world, winners=2)
        await enter(world, giveaway, [1, 2, 3, 4])

        context = ctx(world)
        await fakes.call(world.cog.stop, context, giveaway.id)

        ended = await world.cog.get_giveaway((world.guild.id, giveaway.id))
        assert ended.ended
        assert len(ended.winner_ids) == 2 and set(ended.winner_ids) <= {1, 2, 3, 4}

        announcement = fakes.sent(world.channel.send)
        assert announcement["content"] == ", ".join(f"<@{winner}>" for winner in ended.winner_ids)
        assert "You have won giveaway `#1`" in announcement["embed"].description

        edit = world.posted.edit.await_args_list[-1].kwargs
        assert edit["view"].join_button.disabled
        context.message.add_reaction.assert_awaited_once()

    async def test_fewer_participants_than_winners(self, world: SimpleNamespace) -> None:
        giveaway = await start(world, winners=5)
        await enter(world, giveaway, [1, 2])
        await fakes.call(world.cog.stop, ctx(world), giveaway.id)
        assert sorted((await world.cog.get_giveaway((world.guild.id, 1))).winner_ids) == [1, 2]

    async def test_nobody_entered(self, world: SimpleNamespace) -> None:
        giveaway = await start(world)
        world.channel.send.reset_mock()
        await fakes.call(world.cog.stop, ctx(world), giveaway.id)
        world.channel.send.assert_not_awaited()
        assert (
            "no participants" in world.posted.edit.await_args_list[-1].kwargs["embed"].description
        )

    async def test_already_ended(self, world: SimpleNamespace) -> None:
        giveaway = await start(world)
        await fakes.call(world.cog.stop, ctx(world), giveaway.id)
        with pytest.raises(lyerrors.TakinaError, match="already ended"):
            await fakes.call(world.cog.stop, ctx(world), giveaway.id)

    async def test_unknown(self, world: SimpleNamespace) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError, match="`#99` does not exist"):
            await fakes.call(world.cog.stop, ctx(world), 99)

    async def test_other_guilds_giveaway(self, world: SimpleNamespace) -> None:
        await start(world)
        other = fakes.make_ctx(bot=world.bot, guild=fakes.make_guild())
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(world.cog.stop, other, 1)

    async def test_message_gone(self, world: SimpleNamespace) -> None:
        giveaway = await start(world)
        await enter(world, giveaway, [1])
        world.channel.fetch_message.side_effect = discord.NotFound(MagicMock(status=404), "gone")

        with pytest.raises(lyerrors.TakinaNotFoundError, match="no winners were drawn"):
            await fakes.call(world.cog.stop, ctx(world), giveaway.id)
        ended = await world.cog.get_giveaway((world.guild.id, 1))
        assert ended.ended and ended.winner_ids == []

    async def test_channel_gone(self, world: SimpleNamespace) -> None:
        giveaway = await start(world)
        world.bot.get_channel.side_effect = lambda channel_id: None
        world.bot.fetch_channel.side_effect = discord.NotFound(MagicMock(status=404), "gone")
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(world.cog.stop, ctx(world), giveaway.id)

    async def test_concurrent_stops_draw_once(self, world: SimpleNamespace) -> None:
        giveaway = await start(world)
        await enter(world, giveaway, [1, 2, 3])
        world.channel.send.reset_mock()

        results = await asyncio.gather(
            fakes.call(world.cog.stop, ctx(world), giveaway.id),
            fakes.call(world.cog.stop, ctx(world), giveaway.id),
            return_exceptions=True,
        )
        assert sum(isinstance(result, lyerrors.TakinaError) for result in results) == 1
        assert world.channel.send.await_count == 1


class TestReroll:
    async def test_never_redraws_past_winners(self, world: SimpleNamespace) -> None:
        giveaway = await start(world, winners=2)
        await enter(world, giveaway, [1, 2, 3, 4, 5, 6])
        await fakes.call(world.cog.stop, ctx(world), giveaway.id)

        seen: set[int] = set((await world.cog.get_giveaway((world.guild.id, 1))).winner_ids)
        for _ in range(2):
            await fakes.call(world.cog.reroll, ctx(world), giveaway.id)
            winners = set((await world.cog.get_giveaway((world.guild.id, 1))).winner_ids)
            assert len(winners) == 2 and not winners & seen
            seen |= winners

        assert seen == {1, 2, 3, 4, 5, 6}
        with pytest.raises(lyerrors.TakinaError, match="already won"):
            await fakes.call(world.cog.reroll, ctx(world), giveaway.id)

    async def test_full_set_when_possible(self, world: SimpleNamespace) -> None:
        giveaway = await start(world, winners=3)
        await enter(world, giveaway, [1, 2, 3, 4])
        await fakes.call(world.cog.stop, ctx(world), giveaway.id)
        await fakes.call(world.cog.reroll, ctx(world), giveaway.id)

        rerolled = await world.cog.get_giveaway((world.guild.id, 1))
        # only one person is left who has not won
        assert len(rerolled.winner_ids) == 1
        assert sorted(rerolled.past_winner_ids + rerolled.winner_ids) == [1, 2, 3, 4]

    async def test_announces(self, world: SimpleNamespace) -> None:
        giveaway = await start(world)
        await enter(world, giveaway, [1, 2])
        await fakes.call(world.cog.stop, ctx(world), giveaway.id)
        await fakes.call(world.cog.reroll, ctx(world), giveaway.id)
        assert "Due to a reroll" in fakes.sent(world.channel.send)["embed"].description

    async def test_old_rows_without_past_winners(self, world: SimpleNamespace) -> None:
        # giveaways from before past_winner_ids only know their current winners
        await database.save(
            models.GiveawayModel(
                guild_id=world.guild.id,
                id=1,
                channel_id=world.channel.id,
                message_id=4242,
                title="Old",
                description="",
                ends_at=datetime.now(UTC),
                ended=True,
                participants=[1, 2],
                winner_ids=[1],
                past_winner_ids=[],
            )
        )
        await fakes.call(world.cog.reroll, ctx(world), 1)
        assert (await world.cog.get_giveaway((world.guild.id, 1))).winner_ids == [2]

    async def test_running_giveaway(self, world: SimpleNamespace) -> None:
        giveaway = await start(world)
        with pytest.raises(lyerrors.TakinaError, match="has not ended yet"):
            await fakes.call(world.cog.reroll, ctx(world), giveaway.id)


class TestView:
    async def test_shows_ended(self, world: SimpleNamespace) -> None:
        giveaway = await start(world)
        await enter(world, giveaway, [1])
        await fakes.call(world.cog.stop, ctx(world), giveaway.id)

        context = ctx(world)
        await fakes.call(world.cog.view, context, giveaway.id)
        kwargs = fakes.sent(context.reply)
        assert "<@1>" in kwargs["embed"].description
        # showing the winners again must not ping them again
        assert not kwargs["allowed_mentions"].users

    async def test_running(self, world: SimpleNamespace) -> None:
        giveaway = await start(world)
        with pytest.raises(lyerrors.TakinaError, match="not ended yet"):
            await fakes.call(world.cog.view, ctx(world), giveaway.id)


class TestLifecycle:
    async def test_expiry_loop_ends_due_giveaways(self, world: SimpleNamespace) -> None:
        due = await start(world)
        await enter(world, due, [1])
        later = await start(world, duration="1d")
        due.ends_at = datetime.now(UTC) - timedelta(seconds=1)
        await database.save(due)

        await world.cog._expiry_loop.coro(world.cog)

        assert (await world.cog.get_giveaway((world.guild.id, due.id))).ended
        assert not (await world.cog.get_giveaway((world.guild.id, later.id))).ended

    async def test_expiry_loop_survives_a_broken_giveaway(
        self, world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        first, second = await start(world), await start(world)
        for giveaway in (first, second):
            giveaway.ends_at = datetime.now(UTC) - timedelta(seconds=1)
            await database.save(giveaway)

        real_end = world.cog._end
        calls: list[int] = []

        async def flaky_end(giveaway: models.GiveawayModel) -> Any:
            calls.append(giveaway.id)
            if giveaway.id == first.id:
                raise RuntimeError("the shrine collapsed")
            return await real_end(giveaway)

        monkeypatch.setattr(world.cog, "_end", flaky_end)
        await world.cog._expiry_loop.coro(world.cog)

        assert sorted(calls) == [first.id, second.id]
        assert (await world.cog.get_giveaway((world.guild.id, second.id))).ended

    async def test_expiry_loop_survives_database_outage(
        self, world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(database, "get_all", AsyncMock(side_effect=OSError("down")))
        await world.cog._expiry_loop.coro(world.cog)

    async def test_cog_load_restores_views(
        self, world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        running = await start(world)
        ended = await start(world)
        await fakes.call(world.cog.stop, ctx(world), ended.id)
        # a start that crashed before sending leaves message_id 0
        await database.save(
            models.GiveawayModel(
                guild_id=world.guild.id,
                id=99,
                channel_id=1,
                message_id=0,
                title="Orphan",
                description="",
                ends_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        world.bot.add_view.reset_mock()
        monkeypatch.setattr(world.cog._expiry_loop, "start", MagicMock())

        await world.cog.cog_load()

        restored = [call.kwargs["message_id"] for call in world.bot.add_view.call_args_list]
        assert restored == [running.message_id]
        view = world.bot.add_view.call_args.args[0]
        assert (view.guild_id, view.giveaway_id) == (world.guild.id, running.id)
        world.cog._expiry_loop.start.assert_called_once()

    async def test_unload_cancels_pending_edits(self, world: SimpleNamespace) -> None:
        giveaway = await start(world)
        world.cog.schedule_update((world.guild.id, giveaway.id))
        (task,) = world.cog._pending_updates.values()
        world.cog.cog_unload()
        await asyncio.sleep(0)
        assert task.cancelled()


class TestChecks:
    @pytest.mark.parametrize(
        "name", ["giveaway start", "giveaway stop", "giveaway reroll", "giveaway view"]
    )
    async def test_manage_events(self, world: SimpleNamespace, name: str) -> None:
        command = next(c for c in world.cog.walk_commands() if c.qualified_name == name)
        with pytest.raises(lyerrors.TakinaPermissionError, match="Manage Events"):
            await fakes.run_checks(command, fakes.make_ctx(bot=world.bot, guild=world.guild))
        assert await fakes.run_checks(command, ctx(world))

    async def test_guild_only_group(self, world: SimpleNamespace) -> None:
        # slash subcommands inherit contexts from the group alone
        contexts = world.cog.giveaway.app_command.allowed_contexts
        assert contexts is not None and not contexts.dm_channel
