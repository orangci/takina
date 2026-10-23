# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
"""
Rules every command should keep, checked across every extension at once.

Each is a convention from CONTRIBUTING that is easy to forget on the next command, and whose
breakage only shows when a user runs into it.
"""

from takina.libs.lyerrors import TakinaMissingEnvironmentVariableError
from collections.abc import Iterator
from takina.libs import lyhelpers
from discord.ext import commands
from takina import database
from typing import Any
import takina.__main__ as main
import importlib
import asyncio
import inspect
import pytest


async def no_rows(*args: Any, **kwargs: Any) -> list:
    return []


async def no_row(*args: Any, **kwargs: Any) -> None:
    return None


async def never_ready() -> None:
    # task loops wait for this before their first run, and unloading cancels them
    await asyncio.Event().wait()


@pytest.fixture(scope="module")
def bot() -> Iterator[commands.Bot]:
    patch = pytest.MonkeyPatch()
    # cog_load hooks read the database, so the read helpers answer with nothing
    patch.setattr(database, "get_all", no_rows)
    patch.setattr(database, "get", no_row)
    patch.setattr(main.bot, "wait_until_ready", never_ready)
    # and loops that don't wait ask the web for nothing
    patch.setattr(lyhelpers, "request", no_row)

    loop = asyncio.new_event_loop()

    async def load() -> None:
        for cog in main.cogs:
            try:
                await main.bot.load_extension(f"takina.cogs.{cog}")
            except commands.ExtensionFailed as error:
                if not isinstance(error.original, TakinaMissingEnvironmentVariableError):
                    raise

    async def unload() -> None:
        for extension in list(main.bot.extensions):
            await main.bot.unload_extension(extension)

    try:
        loop.run_until_complete(load())
        yield main.bot
    finally:
        loop.run_until_complete(unload())
        loop.close()
        patch.undo()


def every_command(bot: commands.Bot) -> list[commands.Command]:
    return list(bot.walk_commands())


def check_names(command: commands.Command) -> set[str]:
    return {getattr(check, "__qualname__", repr(check)) for check in command.checks}


def source(command: commands.Command) -> str:
    return inspect.getsource(command.callback)


def test_something_loaded(bot: commands.Bot) -> None:
    assert len(every_command(bot)) > 50


def test_descriptions(bot: commands.Bot) -> None:
    # the help command and the slash picker both show it, and "No description." helps no one
    missing = [
        command.qualified_name
        for command in every_command(bot)
        if not command.hidden and not command.description
    ]
    assert missing == []


def test_guild_assertions_have_guild_checks(bot: commands.Bot) -> None:
    # an assert with no check behind it is an AssertionError in a dm
    unguarded = [
        command.qualified_name
        for command in every_command(bot)
        if "assert ctx.guild is not None" in source(command)
        and not {"guild_only.<locals>.predicate", "sesp_guild_only.<locals>.predicate"}
        & check_names(command)
    ]
    assert unguarded == []


def test_hybrid_subcommands_repeat_group_checks(bot: commands.Bot) -> None:
    # slash invocations never run the group's own checks, so each subcommand needs them too
    lacking = []
    for command in every_command(bot):
        parent = command.parent
        if not isinstance(parent, commands.HybridGroup):
            continue

        needed = check_names(parent) - {"is_user_app.<locals>.predicate"}
        if missing := needed - check_names(command):
            lacking.append(f"{command.qualified_name}: {sorted(missing)}")

    assert lacking == []


def test_owner_commands_hidden(bot: commands.Bot) -> None:
    visible = [
        command.qualified_name
        for command in every_command(bot)
        if "is_owner.<locals>.predicate" in check_names(command) and not command.hidden
    ]
    assert visible == []


def test_no_hand_rolled_error_embeds(bot: commands.Bot) -> None:
    # errors are raised from lyerrors and drawn by core.errors, not built in the command
    offenders = [
        command.qualified_name
        for command in every_command(bot)
        if "ERROR_COLOUR" in source(command) or "emojis.ERROR" in source(command)
    ]
    assert offenders == []


def test_replies_do_not_ping(bot: commands.Bot) -> None:
    offenders = [
        command.qualified_name
        for command in every_command(bot)
        if "mention_author=True" in source(command)
    ]
    assert offenders == []


def test_cogs_have_setup() -> None:
    for cog in main.cogs:
        module = importlib.import_module(f"takina.cogs.{cog}")
        assert inspect.iscoroutinefunction(getattr(module, "setup", None)), cog


def test_aliases_unique(bot: commands.Bot) -> None:
    # discord.py refuses a clash between cogs, but case-insensitive lookups make
    # "Ban" and "ban" the same command, which it does not notice
    seen: dict[str, str] = {}
    clashes = []
    for command in bot.commands:
        for name in [command.name, *command.aliases]:
            key = name.lower()
            if key in seen and seen[key] != command.qualified_name:
                clashes.append(f"{name}: {seen[key]} and {command.qualified_name}")
            seen[key] = command.qualified_name

    assert clashes == []
