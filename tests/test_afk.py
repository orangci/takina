# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.util.afk import AFK, MAX_LISTED_AFK, MAX_STATUS_LENGTH
from collections.abc import Sequence
from takina import database, models
from types import SimpleNamespace
from tests import fakes
from typing import Any
import asyncio
import pytest

pytestmark = pytest.mark.usefixtures("db")


@pytest.fixture
def world() -> SimpleNamespace:
    bot = fakes.make_bot()
    bot.get_context.return_value.valid = False
    guild = fakes.make_guild()
    return SimpleNamespace(bot=bot, guild=guild, cog=fakes.make_cog(AFK, bot))


def message(
    world: SimpleNamespace, author: Any, content: str = "", mentions: Sequence[Any] = ()
) -> Any:
    msg = fakes.make_message(
        author=author, channel=fakes.make_channel(world.guild), guild=world.guild, content=content
    )
    msg.mentions = list(mentions)
    return msg


class TestCommand:
    async def test_toggles(self, world: SimpleNamespace) -> None:
        reimu = fakes.make_user(name="reimu")
        ctx = fakes.make_ctx(bot=world.bot, author=reimu)

        await fakes.call(world.cog.afk, ctx, status="drinking tea")
        status = await database.get(models.AFKStatusModel, user_id=reimu.id)
        assert status is not None and status.status == "drinking tea"
        assert f"{reimu.mention} is now AFK: drinking tea" in (
            fakes.sent_embed(ctx.reply).description or ""
        )

        await fakes.call(world.cog.afk, ctx, status="ignored")
        assert await database.get(models.AFKStatusModel, user_id=reimu.id) is None
        assert "no longer AFK" in (fakes.sent_embed(ctx.reply).description or "")

    async def test_default_status(self, world: SimpleNamespace) -> None:
        reimu = fakes.make_user()
        await fakes.call(world.cog.afk, fakes.make_ctx(bot=world.bot, author=reimu))
        status = await database.get(models.AFKStatusModel, user_id=reimu.id)
        assert status is not None and status.status == "AFK"

    def test_status_is_capped(self, world: SimpleNamespace) -> None:
        param = world.cog.afk.clean_params["status"]
        assert param.annotation.max == MAX_STATUS_LENGTH


class TestListener:
    async def test_return_clears_status(self, world: SimpleNamespace) -> None:
        reimu = fakes.make_user(name="reimu")
        await database.save(models.AFKStatusModel(user_id=reimu.id, status="tea"))

        msg = message(world, reimu, "i'm back")
        await world.cog.on_message(msg)

        assert await database.get(models.AFKStatusModel, user_id=reimu.id) is None
        kwargs = fakes.sent(msg.channel.send)
        assert "no longer AFK" in kwargs["embed"].description
        assert kwargs["delete_after"] == 5

    async def test_commands_do_not_clear(self, world: SimpleNamespace) -> None:
        # the afk command's own message would otherwise undo it at once
        world.bot.get_context.return_value.valid = True
        reimu = fakes.make_user()
        await database.save(models.AFKStatusModel(user_id=reimu.id, status="tea"))

        await world.cog.on_message(message(world, reimu, ".afk"))
        assert await database.get(models.AFKStatusModel, user_id=reimu.id) is not None

    async def test_mentions_are_told(self, world: SimpleNamespace) -> None:
        reimu, marisa = fakes.make_user(name="reimu"), fakes.make_user(name="marisa")
        await database.save(models.AFKStatusModel(user_id=reimu.id, status="tea @everyone"))

        msg = message(world, marisa, "hey", [reimu])
        await world.cog.on_message(msg)

        kwargs = fakes.sent(msg.channel.send)
        assert kwargs["embed"].description == f"<@{reimu.id}> is currently AFK: tea @everyone"
        mentions = kwargs["allowed_mentions"]
        assert not mentions.everyone and not mentions.users

    async def test_not_afk(self, world: SimpleNamespace) -> None:
        msg = message(world, fakes.make_user(), "hey", [fakes.make_user()])
        await world.cog.on_message(msg)
        msg.channel.send.assert_not_awaited()

    async def test_self_and_bot_mentions_ignored(self, world: SimpleNamespace) -> None:
        reimu = fakes.make_user()
        bot_user = fakes.make_user(bot=True)
        await database.save(models.AFKStatusModel(user_id=bot_user.id, status="beep"))

        msg = message(world, reimu, "me and the bot", [reimu, bot_user])
        await world.cog.on_message(msg)
        msg.channel.send.assert_not_awaited()

    async def test_mass_ping_is_capped(self, world: SimpleNamespace) -> None:
        users = [fakes.make_user() for _ in range(MAX_LISTED_AFK + 3)]
        for user in users:
            await database.save(
                models.AFKStatusModel(user_id=user.id, status="s" * MAX_STATUS_LENGTH)
            )

        msg = message(world, fakes.make_user(), "everyone!", users)
        await world.cog.on_message(msg)

        embed = fakes.sent_embed(msg.channel.send)
        lines = (embed.description or "").split("\n")
        assert len(lines) == MAX_LISTED_AFK + 1
        assert lines[-1] == "…and 3 more."

    async def test_bots_ignored(self, world: SimpleNamespace) -> None:
        bot_user = fakes.make_user(bot=True)
        await database.save(models.AFKStatusModel(user_id=bot_user.id, status="beep"))
        await world.cog.on_message(message(world, bot_user))
        assert await database.get(models.AFKStatusModel, user_id=bot_user.id) is not None

    async def test_quick_messages_after_return(self, world: SimpleNamespace) -> None:
        # two messages racing to clear one status must not raise
        reimu = fakes.make_user()
        await database.save(models.AFKStatusModel(user_id=reimu.id, status="tea"))

        await asyncio.gather(
            world.cog.on_message(message(world, reimu, "back")),
            world.cog.on_message(message(world, reimu, "for real")),
        )
        assert await database.get(models.AFKStatusModel, user_id=reimu.id) is None
