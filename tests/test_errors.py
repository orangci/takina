# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.core.errors import Errors
from unittest.mock import MagicMock
from takina.libs import lyerrors
from discord.ext import commands
from takina import config
from tests import fakes
import inspect
import logging
import discord
import aiohttp
import pytest


@pytest.fixture
def cog() -> Errors:
    return Errors(fakes.make_bot())


def http_error(kind: type[discord.HTTPException], status: int) -> discord.HTTPException:
    response = MagicMock(status=status, reason="Nope")
    return kind(response, "Nope")


async def handle(
    cog: Errors, error: commands.CommandError, *, interaction: bool = False
) -> MagicMock:
    ctx = fakes.make_ctx(guild=fakes.make_guild(), interaction=interaction)
    await cog.on_command_error(ctx, error)
    return ctx


def reply_text(ctx: MagicMock) -> str:
    embed = fakes.sent_embed(ctx.reply)
    assert embed.colour is not None and embed.colour.value == config.ERROR_COLOUR
    assert embed.description is not None
    return embed.description


class TestRendering:
    async def test_takina_error_message(self, cog: Errors) -> None:
        ctx = await handle(cog, lyerrors.TakinaNotFoundError("Cirno is not here."))
        assert reply_text(ctx) == f"{config.emojis.ERROR} Cirno is not here."
        assert fakes.sent(ctx.reply)["mention_author"] is False

    async def test_empty_message_falls_back_to_name(self, cog: Errors) -> None:
        ctx = await handle(cog, lyerrors.TakinaPermissionError(""))
        assert reply_text(ctx).endswith("Missing Permissions")

    async def test_interaction_answers_ephemerally(self, cog: Errors) -> None:
        ctx = await handle(cog, lyerrors.TakinaError("Hakkero overheated."), interaction=True)
        ctx.reply.assert_not_awaited()
        assert fakes.sent(ctx.send)["ephemeral"] is True
        assert "Hakkero overheated." in (fakes.sent_embed(ctx.send).description or "")

    async def test_unwraps_invoke_errors(self, cog: Errors) -> None:
        error = commands.CommandInvokeError(lyerrors.TakinaUserInputError("Bad spell card."))
        ctx = await handle(cog, error)
        assert "Bad spell card." in reply_text(ctx)


class TestTranslation:
    @pytest.mark.parametrize(
        ("error", "expected"),
        [
            (commands.DisabledCommand(), "disabled by Takina's maintainers"),
            (commands.NotOwner(), "restricted to Takina's maintainers"),
            (
                commands.BotMissingPermissions(["ban_members", "manage_roles"]),
                "I am missing the following permissions required to use this command: Ban Members, Manage Roles.",
            ),
            (
                commands.MissingPermissions(["manage_guild"]),
                "You are missing the following permissions required to use this command: Manage Guild.",
            ),
            (
                commands.MissingRequiredArgument(
                    commands.Parameter("reason", inspect.Parameter.POSITIONAL_OR_KEYWORD)
                ),
                "Missing required argument: `reason`.",
            ),
            (commands.MemberNotFound("Cirno"), 'Member "Cirno" not found.'),
            (commands.BadArgument("That is not a number."), "That is not a number."),
            (commands.CommandInvokeError(TimeoutError()), "took too long to respond"),
        ],
    )
    async def test_wording(self, cog: Errors, error: commands.CommandError, expected: str) -> None:
        ctx = await handle(cog, error)
        assert expected in reply_text(ctx)

    async def test_forbidden(self, cog: Errors) -> None:
        ctx = await handle(cog, commands.CommandInvokeError(http_error(discord.Forbidden, 403)))
        assert "sufficient permissions" in reply_text(ctx)

    async def test_client_response_error(
        self, cog: Errors, caplog: pytest.LogCaptureFixture
    ) -> None:
        error = aiohttp.ClientResponseError(MagicMock(), (), status=502, message="Bad Gateway")
        ctx = await handle(cog, commands.CommandInvokeError(error))
        assert "Error [502](https://http.cat/502.png): Bad Gateway." in reply_text(ctx)

    async def test_unexpected_is_logged_not_shown(
        self, cog: Errors, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.ERROR, logger="takina.errors"):
            ctx = await handle(cog, commands.CommandInvokeError(KeyError("sakuya's knives")))

        text = reply_text(ctx)
        assert "Something went wrong on our end" in text
        assert "sakuya" not in text
        assert any("Unhandled command exception" in record.message for record in caplog.records)

    async def test_expected_errors_are_not_logged(
        self, cog: Errors, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.ERROR, logger="takina.errors"):
            await handle(cog, lyerrors.TakinaNotFoundError("Not found."))
        assert not caplog.records


class TestSilence:
    async def test_command_not_found(self, cog: Errors) -> None:
        ctx = await handle(cog, commands.CommandNotFound())
        ctx.reply.assert_not_awaited()
        ctx.send.assert_not_awaited()

    async def test_plain_check_failure_is_quiet_on_prefix(self, cog: Errors) -> None:
        ctx = await handle(cog, commands.CheckFailure())
        ctx.reply.assert_not_awaited()

    async def test_plain_check_failure_answers_interactions(self, cog: Errors) -> None:
        # otherwise discord tells the user the application did not respond
        ctx = await handle(cog, commands.CheckFailure(), interaction=True)
        assert "not available here" in (fakes.sent_embed(ctx.send).description or "")
        assert fakes.sent(ctx.send)["ephemeral"] is True

    async def test_no_private_message_answers_interactions(self, cog: Errors) -> None:
        ctx = await handle(cog, commands.NoPrivateMessage(), interaction=True)
        assert "not available here" in (fakes.sent_embed(ctx.send).description or "")

    async def test_takina_check_failures_still_speak(self, cog: Errors) -> None:
        # takina errors raised from checks are check failures too, but carry their own message
        ctx = await handle(cog, lyerrors.TakinaPermissionError("Shrine staff only."))
        assert "Shrine staff only." in reply_text(ctx)


class TestCooldowns:
    def error(self) -> commands.CommandOnCooldown:
        return commands.CommandOnCooldown(commands.Cooldown(1, 5), 3.21, commands.BucketType.user)

    async def test_prefix_reacts_instead_of_replying(self, cog: Errors) -> None:
        ctx = await handle(cog, self.error())
        ctx.message.add_reaction.assert_awaited_once_with("⏳")
        ctx.reply.assert_not_awaited()
        ctx.send.assert_not_awaited()

    async def test_reaction_failure_is_ignored(self, cog: Errors) -> None:
        ctx = fakes.make_ctx(guild=fakes.make_guild())
        ctx.message.add_reaction.side_effect = http_error(discord.Forbidden, 403)
        await cog.on_command_error(ctx, self.error())

    async def test_interaction_says_how_long(self, cog: Errors) -> None:
        ctx = await handle(cog, self.error(), interaction=True)
        assert "Try again in 3.2s" in (fakes.sent_embed(ctx.send).description or "")
        assert fakes.sent(ctx.send)["ephemeral"] is True
