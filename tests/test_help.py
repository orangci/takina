# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.core import help as help_module
from takina.libs import lyerrors, lyviews
from takina.cogs.core.help import Help
from unittest.mock import AsyncMock
from discord.ext import commands
from takina import config
from typing import cast
from tests import fakes
import discord
import pytest


async def denied(ctx: commands.Context) -> bool:
    return False


class Shrine(commands.Cog):
    @commands.command(description="Sweep the shrine grounds.", aliases=["clean"])
    async def sweep(self, ctx: commands.Context, broom: str, *, area: str = "steps") -> None:
        pass

    @commands.command(description="Count the donations.")
    async def donations(self, ctx: commands.Context) -> None:
        pass

    @commands.command()
    async def nap(self, ctx: commands.Context) -> None:
        pass

    @commands.command(hidden=True, description="Raid Marisa's house.")
    async def raid(self, ctx: commands.Context) -> None:
        pass

    @commands.command(description="Only Yukari may use this.")
    @commands.check(denied)
    async def gap(self, ctx: commands.Context) -> None:
        pass

    @commands.group(description="Manage the ofuda.", aliases=["talisman"])
    async def ofuda(self, ctx: commands.Context) -> None:
        pass

    @ofuda.command(description="Throw an ofuda.")
    async def throw(self, ctx: commands.Context, target: str) -> None:
        pass

    @ofuda.command(description="Bless an ofuda.")
    async def bless(self, ctx: commands.Context) -> None:
        pass

    @commands.group(description="A locked storehouse.")
    async def storehouse(self, ctx: commands.Context) -> None:
        pass

    @storehouse.command()
    @commands.check(denied)
    async def unlock(self, ctx: commands.Context) -> None:
        pass


class Locked(commands.Cog):
    @commands.command()
    @commands.check(denied)
    async def seal(self, ctx: commands.Context) -> None:
        pass


@pytest.fixture
async def bot() -> commands.Bot:
    bot = commands.Bot(command_prefix=".", intents=discord.Intents(guilds=True), help_command=None)
    await bot.add_cog(Shrine())
    await bot.add_cog(Locked())
    return bot


@pytest.fixture
def help_command(bot: commands.Bot) -> Help:
    help_command = Help()
    help_command.context = fakes.make_ctx(bot=bot)
    return help_command


def sent_to(help_command: Help) -> AsyncMock:
    # the context is a fake, so its channel's send is a mock
    return cast(AsyncMock, help_command.context.channel.send)


def channel_embed(help_command: Help, call: int = -1) -> discord.Embed:
    return fakes.sent_embed(sent_to(help_command), call)


async def ask(help_command: Help, query: str | None = None) -> None:
    await help_command.command_callback(help_command.context, command=query)


class TestSignature:
    def test_with_parameters(self, bot: commands.Bot, help_command: Help) -> None:
        command = bot.get_command("sweep")
        assert command is not None
        assert help_command.get_command_signature(command) == "**.sweep** <broom> [area=steps]"

    def test_without_parameters(self, bot: commands.Bot, help_command: Help) -> None:
        command = bot.get_command("donations")
        assert command is not None
        assert help_command.get_command_signature(command) == "**.donations**"

    def test_subcommand(self, bot: commands.Bot, help_command: Help) -> None:
        command = bot.get_command("ofuda throw")
        assert command is not None
        assert help_command.get_command_signature(command) == "**.ofuda throw** <target>"


class TestBotHelp:
    async def test_lists_usable_commands(self, help_command: Help) -> None:
        await ask(help_command)

        embed = channel_embed(help_command)
        description = embed.description or ""
        assert "> **sweep**: Sweep the shrine grounds." in description
        assert "> **nap**: No description." in description
        assert "> **ofuda**: Manage the ofuda." in description
        # hidden, or failing their checks
        assert "raid" not in description
        assert "gap" not in description
        assert "seal" not in description
        assert embed.footer.text == "Page 1 of 1"

    async def test_sorted(self, help_command: Help) -> None:
        await ask(help_command)
        description = channel_embed(help_command).description or ""
        names = [line.split("**")[1] for line in description.splitlines()]
        assert names == sorted(names)

    async def test_paginates(self, bot: commands.Bot, help_command: Help) -> None:
        for number in range(23):

            async def callback(ctx: commands.Context) -> None:
                pass

            bot.add_command(
                commands.Command(callback, name=f"fumo{number:02}", description="Fumo.")
            )

        await ask(help_command)

        reply = sent_to(help_command).await_args_list[-1]
        view = reply.kwargs["view"]
        assert isinstance(view, lyviews.PaginatorView)
        # five from the shrine, two groups, and the 23 fumos
        assert len(view.embeds) == 3
        assert [embed.footer.text for embed in view.embeds] == [
            "Page 1 of 3",
            "Page 2 of 3",
            "Page 3 of 3",
        ]
        assert all(len((embed.description or "").splitlines()) <= 10 for embed in view.embeds)
        assert view.message is not None
        # only the person who asked may turn the pages
        assert view.author is help_command.context.author

    async def test_nothing_usable(self) -> None:
        bot = commands.Bot(
            command_prefix=".", intents=discord.Intents(guilds=True), help_command=None
        )
        await bot.add_cog(Locked())
        help_command = Help()
        help_command.context = fakes.make_ctx(bot=bot)
        await ask(help_command)

        embed = channel_embed(help_command)
        assert embed.colour is not None
        assert embed.colour.value == config.ERROR_COLOUR
        assert "No commands were found." in (embed.description or "")


class TestCommandHelp:
    async def test_command(self, help_command: Help) -> None:
        await ask(help_command, "sweep")

        description = channel_embed(help_command).description or ""
        assert description.startswith("Sweep the shrine grounds.\n\n")
        assert "> **Command**: .sweep <broom> [area=steps]" in description
        assert "> **Aliases**: clean" in description

    async def test_by_alias(self, help_command: Help) -> None:
        await ask(help_command, "clean")
        assert "> **Command**: .sweep" in (channel_embed(help_command).description or "")

    async def test_bare_command(self, help_command: Help) -> None:
        await ask(help_command, "nap")
        description = channel_embed(help_command).description or ""
        assert description == "> **Command**: .nap "
        assert "Aliases" not in description

    async def test_subcommand(self, help_command: Help) -> None:
        await ask(help_command, "ofuda throw")
        description = channel_embed(help_command).description or ""
        assert "> **Command**: .ofuda throw <target>" in description


class TestGroupHelp:
    async def test_group(self, help_command: Help) -> None:
        await ask(help_command, "ofuda")

        description = channel_embed(help_command).description or ""
        assert description.startswith("Manage the ofuda.\n\n")
        assert "> **Aliases**: talisman" in description
        assert "**Subcommands**\n> **.ofuda bless**\n> **.ofuda throw** <target>" in description

    async def test_nothing_usable(self, help_command: Help) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await ask(help_command, "storehouse")


class TestCogHelp:
    async def test_cog(self, help_command: Help) -> None:
        await ask(help_command, "Shrine")

        description = channel_embed(help_command).description or ""
        lines = description.splitlines()
        assert "> **.sweep** <broom> [area=steps]" in lines
        assert "> **.ofuda**" in lines
        assert not any("raid" in line or "gap" in line for line in lines)
        # top level only; the group's own help lists its subcommands
        assert not any("throw" in line for line in lines)

    async def test_nothing_usable(self, help_command: Help) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await ask(help_command, "Locked")


class TestNotFound:
    async def test_command(self, help_command: Help) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError, match="That command does not exist."):
            await ask(help_command, "spellcard")

    async def test_subcommand(self, help_command: Help) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError, match="That subcommand does not exist."):
            await ask(help_command, "ofuda burn")

    async def test_subcommand_of_command(self, help_command: Help) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError, match="subcommand"):
            await ask(help_command, "nap deeply")


async def test_setup_installs_help(bot: commands.Bot) -> None:
    await help_module.setup(bot)
    assert isinstance(bot.help_command, Help)
