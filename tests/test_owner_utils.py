# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.core import owner_utils as owner_utils_module
from takina.libs import lyerrors, lyhelpers, lymal, lymodlog
from takina.cogs.core.owner_utils import OwnerUtils
from unittest.mock import AsyncMock, MagicMock
from discord import app_commands
from discord.ext import commands
from takina import config
from tests import fakes
from typing import Any
import discord
import pytest


@pytest.fixture
def owner() -> fakes.MagicMock:
    return fakes.make_user(name="orangc")


@pytest.fixture
def bot(owner: fakes.MagicMock) -> fakes.MagicMock:
    return fakes.make_bot(owners={owner.id})


@pytest.fixture
def cog(bot: fakes.MagicMock) -> OwnerUtils:
    return fakes.make_cog(OwnerUtils, bot)


@pytest.fixture
def ctx(bot: fakes.MagicMock, owner: fakes.MagicMock) -> fakes.MagicMock:
    return fakes.make_ctx(bot=bot, author=owner)


def not_found() -> discord.NotFound:
    response = MagicMock()
    response.status = 404
    response.reason = "Not Found"
    return discord.NotFound(response, "Unknown User")


class TestCleanupCode:
    @pytest.mark.parametrize(
        ("content", "expected"),
        [
            ("```py\nprint('reimu')\n```", "print('reimu')"),
            ("```\nreturn 9\n```", "return 9"),
            ("```py\na = 1\nb = 2\n```", "a = 1\nb = 2"),
            ("`return 9`", "return 9"),
            ("  return 9 \n", "return 9"),
            ("return 9", "return 9"),
        ],
    )
    def test_cleanup(self, cog: OwnerUtils, content: str, expected: str) -> None:
        assert cog.cleanup_code(content) == expected


class TestRunEval:
    async def test_return_value(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        assert await cog.run_eval(ctx, "return 6 * 7") == "```py\n42\n```"

    async def test_stdout(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        assert await cog.run_eval(ctx, "print('cirno')") == "```py\ncirno\n\n```"

    async def test_stdout_and_value(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        result = await cog.run_eval(ctx, "```py\nprint('baka')\nreturn 9\n```")
        assert result == "```py\nbaka\n9\n```"

    async def test_nothing(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        assert await cog.run_eval(ctx, "x = 1") is None

    async def test_syntax_error(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        result = await cog.run_eval(ctx, "return (")
        assert result is not None
        assert result.startswith("```py\nSyntaxError: ")

    async def test_exception(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        result = await cog.run_eval(ctx, "print('before')\nraise ValueError('master spark')")
        assert result is not None
        assert result.startswith("```py\nbefore\nTraceback")
        assert "ValueError: master spark" in result

    async def test_environment(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        assert await cog.run_eval(ctx, "return author.name") == "```py\norangc\n```"
        assert await cog.run_eval(ctx, "return ctx is ctx") == "```py\nTrue\n```"
        assert await cog.run_eval(ctx, "return channel.name") == "```py\nhakurei-shrine\n```"
        assert await cog.run_eval(ctx, "return config.BOT_NAME") == f"```py\n{config.BOT_NAME}\n```"

    async def test_await(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        assert await cog.run_eval(ctx, "import asyncio\nawait asyncio.sleep(0)\nreturn 1") == (
            "```py\n1\n```"
        )

    async def test_command_reacts(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        await fakes.call(cog.eval, ctx, code="return 1")
        ctx.message.add_reaction.assert_awaited_once_with(config.emojis.SUCCESS)
        assert fakes.sent(ctx.reply)["content"] == "```py\n1\n```"

    async def test_command_quiet(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        await fakes.call(cog.eval, ctx, code="x = 1")
        ctx.message.add_reaction.assert_awaited_once()
        ctx.reply.assert_not_awaited()


class TestOwnerChecks:
    @pytest.mark.parametrize(
        "name",
        [
            "eval",
            "guilds",
            "disable",
            "enable",
            "reload_exts",
            "reload_slash_command",
            "unload",
            "load",
            "send",
            "command_info",
        ],
    )
    async def test_refuses_others(self, cog: OwnerUtils, bot: fakes.MagicMock, name: str) -> None:
        guild = fakes.make_guild()
        ctx = fakes.make_ctx(bot=bot, guild=guild)
        with pytest.raises(commands.CheckFailure):
            await fakes.run_checks(getattr(cog, name), ctx)

    @pytest.mark.parametrize("name", ["eval", "guilds", "reload_exts", "command_info"])
    async def test_allows_owner(
        self, cog: OwnerUtils, bot: fakes.MagicMock, owner: fakes.MagicMock, name: str
    ) -> None:
        ctx = fakes.make_ctx(bot=bot, author=owner)
        assert await fakes.run_checks(getattr(cog, name), ctx)

    def test_hidden(self, cog: OwnerUtils) -> None:
        assert all(command.hidden for command in cog.get_commands())

    async def test_maintainers_open_to_all(self, cog: OwnerUtils, bot: fakes.MagicMock) -> None:
        assert await fakes.run_checks(cog.maintainers, fakes.make_ctx(bot=bot))


class SimpleGuild:
    def __init__(self, name: str, member_count: int | None) -> None:
        self.name = name
        self.member_count = member_count


class TestGuilds:
    async def test_sorted_by_members(
        self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock
    ) -> None:
        bot.guilds = [
            SimpleGuild("Human Village", 50),
            SimpleGuild("Hakurei Shrine", 2),
            SimpleGuild("Scarlet Devil Mansion", 300),
            SimpleGuild("Unknown", None),
        ]
        await fakes.call(cog.guilds, ctx)

        description = fakes.sent_embed(ctx.reply).description or ""
        assert description.split("\n")[1:] == [
            "**Scarlet Devil Mansion**",
            "**Human Village**",
            "**Hakurei Shrine**",
            "**Unknown**",
        ]

    async def test_none(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        await fakes.call(cog.guilds, ctx)
        assert fakes.sent_embed(ctx.reply).description == "No guilds available to display."

    async def test_many_fit(
        self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock
    ) -> None:
        bot.guilds = [SimpleGuild("Gensokyo " * 10, n) for n in range(500)]
        await fakes.call(cog.guilds, ctx)
        assert len(fakes.sent_embed(ctx.reply).description or "") <= 4096


class TestEnableDisable:
    def command(self, name: str = "weather") -> commands.Command:
        async def callback(ctx: commands.Context) -> None:
            pass

        return commands.Command(callback, name=name)

    async def test_disable(
        self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock
    ) -> None:
        command = self.command()
        bot.get_command.return_value = command
        await fakes.call(cog.disable, ctx, "weather")

        assert command.enabled is False
        bot.get_command.assert_called_with("weather")
        assert "Successfully disabled `weather`" in (fakes.sent_embed(ctx.reply).description or "")

    async def test_enable(
        self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock
    ) -> None:
        command = self.command()
        command.enabled = False
        bot.get_command.return_value = command
        await fakes.call(cog.enable, ctx, "weather")

        assert command.enabled is True
        assert "Successfully enabled `weather`" in (fakes.sent_embed(ctx.reply).description or "")

    async def test_unknown(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(cog.disable, ctx, "spellcard")

    @pytest.mark.parametrize("name", ["enable", "disable"])
    async def test_cannot_lock_itself_out(
        self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock, name: str
    ) -> None:
        # resolved by bot.get_command, so an alias lands here too
        bot.get_command.return_value = getattr(cog, name)
        with pytest.raises(lyerrors.TakinaUserInputError):
            await fakes.call(cog.disable, ctx, "off")
        assert getattr(cog, name).enabled is True


class TestMaintainers:
    async def test_owner(
        self, cog: OwnerUtils, bot: fakes.MagicMock, owner: fakes.MagicMock
    ) -> None:
        bot.get_user.return_value = owner
        ctx = fakes.make_ctx(bot=bot, author=owner)
        await fakes.call(cog.maintainers, ctx)

        description = fakes.sent_embed(ctx.reply).description or ""
        assert description.startswith("You have maintainer-level permissions")
        assert description.endswith("**Orangc**")

    async def test_others(
        self, cog: OwnerUtils, bot: fakes.MagicMock, owner: fakes.MagicMock
    ) -> None:
        bot.get_user.return_value = owner
        ctx = fakes.make_ctx(bot=bot)
        await fakes.call(cog.maintainers, ctx)
        assert (fakes.sent_embed(ctx.reply).description or "").startswith(
            f"You are not a maintainer of {config.BOT_NAME}."
        )

    async def test_fetches_once(
        self, cog: OwnerUtils, bot: fakes.MagicMock, owner: fakes.MagicMock
    ) -> None:
        bot.fetch_user = AsyncMock(return_value=owner)
        for _ in range(3):
            await fakes.call(cog.maintainers, fakes.make_ctx(bot=bot))
        bot.fetch_user.assert_awaited_once_with(owner.id)

    async def test_deleted_owner(
        self, cog: OwnerUtils, bot: fakes.MagicMock, owner: fakes.MagicMock
    ) -> None:
        bot.fetch_user = AsyncMock(side_effect=not_found())
        assert await cog._owner_name(owner.id) == f"Unknown User (ID: {owner.id})"
        # a missing user isn't cached, so it is looked up again next time
        assert cog._owner_cache == {}


class TestReload:
    @pytest.fixture(autouse=True)
    def no_reloads(self, monkeypatch: pytest.MonkeyPatch) -> list[Any]:
        # a real reload would mint new exception classes under every other test
        reloaded: list[Any] = []
        monkeypatch.setattr(owner_utils_module.importlib, "reload", reloaded.append)
        monkeypatch.setattr(lyhelpers, "setup", lambda bot: None)
        return reloaded

    async def test_all(
        self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock, no_reloads: list[Any]
    ) -> None:
        bot.extensions = {"takina.cogs.fun.fun": None, "takina.cogs.util.wiki": None}
        bot.reload_extension = AsyncMock()
        await fakes.call(cog.reload_exts, ctx)

        assert [call.args[0] for call in bot.reload_extension.await_args_list] == list(
            bot.extensions
        )
        assert "Successfully reloaded all cogs." in (fakes.sent_embed(ctx.reply).description or "")
        # the libs are reloaded before the cogs that import them, and lymodlog after its own
        assert no_reloads.index(lymodlog) > no_reloads.index(lyerrors)
        assert no_reloads.index(lymal) > no_reloads.index(lyhelpers)
        assert no_reloads[0] is config

    async def test_all_with_failures(
        self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock
    ) -> None:
        bot.extensions = {"takina.cogs.fun.fun": None, "takina.cogs.util.wiki": None}

        async def reload(name: str) -> None:
            if name.endswith("wiki"):
                raise commands.ExtensionFailed(name, RuntimeError("bad"))

        bot.reload_extension = AsyncMock(side_effect=reload)
        with pytest.raises(lyerrors.TakinaError, match="takina.cogs.util.wiki"):
            await fakes.call(cog.reload_exts, ctx)
        # the rest are still reloaded
        assert bot.reload_extension.await_count == 2

    @pytest.mark.parametrize("name", ["fun.fun", "takina.cogs.fun.fun"])
    async def test_one(
        self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock, name: str
    ) -> None:
        bot.extensions = {"takina.cogs.fun.fun": None}
        bot.reload_extension = AsyncMock()
        await fakes.call(cog.reload_exts, ctx, name)

        bot.reload_extension.assert_awaited_once_with("takina.cogs.fun.fun")
        assert "`takina.cogs.fun.fun`" in (fakes.sent_embed(ctx.reply).description or "")

    async def test_one_not_loaded(
        self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock
    ) -> None:
        bot.extensions = {}
        with pytest.raises(lyerrors.TakinaError, match="is not loaded"):
            await fakes.call(cog.reload_exts, ctx, "fun.fun")

    async def test_one_fails(
        self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock
    ) -> None:
        bot.extensions = {"takina.cogs.fun.fun": None}
        bot.reload_extension = AsyncMock(
            side_effect=commands.ExtensionFailed("takina.cogs.fun.fun", RuntimeError("bad"))
        )
        with pytest.raises(lyerrors.TakinaError, match="Failed to reload"):
            await fakes.call(cog.reload_exts, ctx, "fun.fun")


class TestExtensions:
    async def test_sync(self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock) -> None:
        bot.tree.sync = AsyncMock(return_value=[object()] * 1500)
        await fakes.call(cog.reload_slash_command, ctx)
        assert "synced 1,500 bot application commands" in (
            fakes.sent_embed(ctx.reply).description or ""
        )

    async def test_unload(
        self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock
    ) -> None:
        bot.unload_extension = AsyncMock()
        await fakes.call(cog.unload, ctx, "fun.fun")
        bot.unload_extension.assert_awaited_once_with("takina.cogs.fun.fun")
        assert "unloaded `cogs.fun.fun`" in (fakes.sent_embed(ctx.reply).description or "")

    async def test_unload_twice(
        self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock
    ) -> None:
        bot.unload_extension = AsyncMock(side_effect=commands.ExtensionNotLoaded("x"))
        with pytest.raises(lyerrors.TakinaError, match="already unloaded"):
            await fakes.call(cog.unload, ctx, "fun.fun")

    async def test_load(self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock) -> None:
        bot.load_extension = AsyncMock()
        await fakes.call(cog.load, ctx, "fun.fun")
        bot.load_extension.assert_awaited_once_with("takina.cogs.fun.fun")
        assert "loaded `cogs.fun.fun`" in (fakes.sent_embed(ctx.reply).description or "")

    @pytest.mark.parametrize(
        ("error", "expected", "message"),
        [
            (commands.ExtensionAlreadyLoaded("x"), lyerrors.TakinaError, "already loaded"),
            (commands.ExtensionNotFound("x"), lyerrors.TakinaNotFoundError, "does not exist"),
            (commands.NoEntryPointError("x"), lyerrors.TakinaError, "Failed to load"),
        ],
    )
    async def test_load_errors(
        self,
        cog: OwnerUtils,
        bot: fakes.MagicMock,
        ctx: fakes.MagicMock,
        error: Exception,
        expected: type[Exception],
        message: str,
    ) -> None:
        bot.load_extension = AsyncMock(side_effect=error)
        with pytest.raises(expected, match=message):
            await fakes.call(cog.load, ctx, "fun.fun")
        ctx.reply.assert_not_awaited()


class TestSend:
    async def test_here(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        await fakes.call(cog.send, ctx, None, message="Marisa stole the books again.")
        ctx.channel.send.assert_awaited_once_with("Marisa stole the books again.")
        # by prefix, the message speaks for itself
        ctx.reply.assert_not_awaited()

    async def test_elsewhere_by_slash(
        self, cog: OwnerUtils, bot: fakes.MagicMock, owner: fakes.MagicMock
    ) -> None:
        guild = fakes.make_guild()
        ctx = fakes.make_ctx(bot=bot, guild=guild, author=owner, interaction=True)
        target = fakes.make_channel(guild, name="voile")
        await fakes.call(cog.send, ctx, target, message="Return the books.")

        target.send.assert_awaited_once_with("Return the books.")
        ctx.channel.send.assert_not_awaited()
        assert fakes.sent(ctx.reply)["ephemeral"] is True

    async def test_guild_only(
        self, cog: OwnerUtils, bot: fakes.MagicMock, owner: fakes.MagicMock
    ) -> None:
        ctx = fakes.make_ctx(bot=bot, author=owner)
        with pytest.raises((commands.CheckFailure, lyerrors.TakinaError)):
            await fakes.run_checks(cog.send, ctx)


class TestCommandInfo:
    async def test_prefix_command(
        self, cog: OwnerUtils, bot: fakes.MagicMock, ctx: fakes.MagicMock
    ) -> None:
        bot.get_command.return_value = cog.guilds
        await fakes.call(cog.command_info, ctx, name="guilds")

        embed = fakes.sent_embed(ctx.reply)
        assert embed.title == "Command: guilds"
        description = embed.description or ""
        assert "> **Enabled**: True" in description
        assert "> **Hidden**: True" in description
        assert "Contexts" not in description

    async def test_hybrid_command(
        self, ctx: fakes.MagicMock, bot: fakes.MagicMock, cog: OwnerUtils
    ) -> None:
        class Spells(commands.Cog):
            @commands.hybrid_command(description="Fire a master spark.")
            @app_commands.allowed_installs(guilds=True, users=True)
            @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=False)
            async def spark(self, ctx: commands.Context, target: str) -> None:
                pass

        bot.get_command.return_value = Spells().spark
        await fakes.call(cog.command_info, ctx, name="spark")

        description = fakes.sent_embed(ctx.reply).description or ""
        assert "> **Description**: Fire a master spark." in description
        assert "> **Usage**: <target>" in description
        assert "> **Contexts**: Guilds, DMs\n" in description
        assert "> **Allowed Installs**: Guilds, Users" in description

    async def test_hybrid_defaults(
        self, ctx: fakes.MagicMock, bot: fakes.MagicMock, cog: OwnerUtils
    ) -> None:
        class Plain(commands.Cog):
            @commands.hybrid_command()
            async def plain(self, ctx: commands.Context) -> None:
                pass

        bot.get_command.return_value = Plain().plain
        await fakes.call(cog.command_info, ctx, name="plain")

        description = fakes.sent_embed(ctx.reply).description or ""
        assert "> **Contexts**: Default" in description
        assert "> **Allowed Installs**: Default" in description

    async def test_unknown(self, cog: OwnerUtils, ctx: fakes.MagicMock) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(cog.command_info, ctx, name="spellcard")
