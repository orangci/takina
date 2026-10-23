# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
"""
Load every extension against a stubbed database and check the command tree builds.

It catches bad decorators, clashing names and slash limits that would otherwise only show at
startup or sync, not whether any command actually works.
"""

from takina.libs.lyerrors import TakinaMissingEnvironmentVariableError
from discord.ext import commands
from takina import database
from typing import Any
import takina.__main__ as main
import asyncio
import pytest


async def no_rows(*args: Any, **kwargs: Any) -> list:
    return []


async def no_row(*args: Any, **kwargs: Any) -> None:
    return None


async def load_everything() -> list[str]:
    loaded = []
    for cog in main.cogs:
        try:
            await main.bot.load_extension(f"takina.cogs.{cog}")
            loaded.append(cog)
        except commands.ExtensionFailed as error:
            # a cog refusing to load without its api key or binary is fine here
            if not isinstance(error.original, TakinaMissingEnvironmentVariableError):
                raise

    return loaded


def walk_options(payload: dict, path: str) -> list[tuple[str, dict]]:
    found = [(path, payload)]
    for option in payload.get("options", []):
        found += walk_options(option, f"{path} {option['name']}")

    return found


def test_extensions_load_and_tree_builds(monkeypatch: pytest.MonkeyPatch) -> None:
    # cog_load hooks read the database, so the read helpers answer with nothing
    monkeypatch.setattr(database, "get_all", no_rows)
    monkeypatch.setattr(database, "get", no_row)

    async def run() -> None:
        assert await load_everything(), "no extension loaded at all"

        # serialising is what sync would send, so this is where discord's limits apply
        payloads = [command.to_dict(main.bot.tree) for command in main.bot.tree.get_commands()]
        assert payloads, "the slash command tree is empty"
        assert len(payloads) <= 100, "discord allows at most 100 global slash commands"

        for payload in payloads:
            for path, entry in walk_options(payload, payload["name"]):
                assert 1 <= len(entry["name"]) <= 32, f"/{path}: name must be 1 to 32 characters"
                assert entry["name"] == entry["name"].lower(), f"/{path}: name must be lowercase"
                if "description" in entry:
                    assert 1 <= len(entry["description"]) <= 100, (
                        f"/{path}: description must be 1 to 100 characters"
                    )

        for extension in list(main.bot.extensions):
            await main.bot.unload_extension(extension)

    asyncio.run(run())
