# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.core.prefix_command import Prefix
from takina import database, models
from unittest.mock import MagicMock
from discord.ext import commands
from takina.libs import lyerrors
from pathlib import Path
from tests import fakes
from typing import Any
import takina.__main__ as main
import discord
import pytest

COGS = Path(main.__file__).parent / "cogs"


@pytest.fixture
def no_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PREFIX", raising=False)


@pytest.mark.usefixtures("db", "no_env_prefix")
class TestGetPrefix:
    def message(self, guild: Any = None) -> MagicMock:
        return fakes.make_message(
            author=fakes.make_user(), channel=fakes.make_channel(guild), guild=guild
        )

    async def test_default(self) -> None:
        prefixes = await main.get_prefix(main.bot, self.message(fakes.make_guild()))
        assert set(prefixes) == {".", "takina ", "Takina "}

    async def test_dms(self) -> None:
        assert set(await main.get_prefix(main.bot, self.message())) == {".", "takina ", "Takina "}

    async def test_env_prefix_keeps_names(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PREFIX", "!")
        prefixes = await main.get_prefix(main.bot, self.message(fakes.make_guild()))
        assert set(prefixes) == {"!", "takina ", "Takina "}

    async def test_env_prefix_in_dms(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PREFIX", "!")
        assert "!" in await main.get_prefix(main.bot, self.message())

    async def test_custom_prefix(self) -> None:
        guild = fakes.make_guild()
        await database.save(models.PrefixModel(guild_id=guild.id, prefix="r!"))
        prefixes = await main.get_prefix(main.bot, self.message(guild))
        assert set(prefixes) == {"r!", "takina ", "Takina "}
        assert "." not in prefixes

    async def test_custom_prefix_beats_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PREFIX", "!")
        guild = fakes.make_guild()
        await database.save(models.PrefixModel(guild_id=guild.id, prefix="?"))
        assert "?" in await main.get_prefix(main.bot, self.message(guild))

    @pytest.mark.parametrize("custom", ["takina", "t", "Takina", "takina  ", "."])
    async def test_longest_first(self, custom: str) -> None:
        guild = fakes.make_guild()
        await database.save(models.PrefixModel(guild_id=guild.id, prefix=custom))
        prefixes = await main.get_prefix(main.bot, self.message(guild))
        assert [len(prefix) for prefix in prefixes] == sorted(map(len, prefixes), reverse=True)


@pytest.mark.usefixtures("db", "no_env_prefix")
class TestPrefixResolution:
    """What discord.py makes of a message, with the real get_prefix."""

    @pytest.fixture
    def bot(self) -> commands.Bot:
        bot = commands.Bot(
            command_prefix=main.get_prefix, intents=discord.Intents.none(), case_insensitive=True
        )

        @bot.command(name="serverinfo")
        async def serverinfo(ctx: commands.Context) -> None:
            pass

        bot._connection.user = fakes.make_user(name="takina", bot=True)  # type: ignore[assignment]
        return bot

    async def resolve(
        self, bot: commands.Bot, content: str, custom: str | None
    ) -> commands.Context:
        guild = fakes.make_guild()
        if custom is not None:
            await database.save(models.PrefixModel(guild_id=guild.id, prefix=custom))

        message = fakes.make_message(
            author=fakes.make_user(),
            channel=fakes.make_channel(guild),
            guild=guild,
            content=content,
        )
        return await bot.get_context(message)

    @pytest.mark.parametrize(
        ("content", "custom"),
        [
            (".serverinfo", None),
            ("takina serverinfo", None),
            ("Takina serverinfo", None),
            ("r!serverinfo", "r!"),
            ("takina serverinfo", "r!"),
            # #138: a custom "takina" swallowed the "takina " prefix
            ("takina serverinfo", "takina"),
            ("takinaserverinfo", "takina"),
            ("Takina serverinfo", "takina"),
        ],
    )
    async def test_finds_the_command(
        self, bot: commands.Bot, content: str, custom: str | None
    ) -> None:
        ctx = await self.resolve(bot, content, custom)
        assert ctx.command is not None and ctx.command.name == "serverinfo"

    async def test_old_default_gone_with_custom(self, bot: commands.Bot) -> None:
        ctx = await self.resolve(bot, ".serverinfo", "r!")
        assert ctx.command is None


class TestLoadExts:
    def test_finds_every_cog(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ENABLE_SESP_COGS", "yes")
        monkeypatch.delenv("COGS_CATEGORY_BLACKLIST", raising=False)
        found = set(main.load_exts(COGS))

        on_disk = {
            str(path.relative_to(COGS).with_suffix("")).replace("/", ".")
            for path in COGS.rglob("*.py")
        }
        assert found == on_disk
        assert {"core.errors", "mod.ban", "listeners.honeypot", "sesp.awcc.hof"} <= found

    def test_sesp_needs_enabling(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ENABLE_SESP_COGS", raising=False)
        assert not any(cog.startswith("sesp.") for cog in main.load_exts(COGS))

    def test_category_blacklist(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("COGS_CATEGORY_BLACKLIST", " weebism, minecraft ,")
        found = main.load_exts(COGS)
        assert not any(cog.startswith(("weebism.", "minecraft.")) for cog in found)
        assert "mod.ban" in found


@pytest.mark.usefixtures("db")
class TestPrefixCommand:
    async def test_sets_and_changes(self) -> None:
        cog = fakes.make_cog(Prefix)
        guild = fakes.make_guild()
        ctx = fakes.make_ctx(guild=guild)

        await fakes.call(cog.set_prefix, ctx, "r!")
        assert "`r!`" in (fakes.sent_embed(ctx.reply).description or "")
        await fakes.call(cog.set_prefix, ctx, "?")

        rows = await database.get_all(models.PrefixModel)
        assert [(row.guild_id, row.prefix) for row in rows] == [(guild.id, "?")]

    async def test_needs_administrator(self) -> None:
        cog = fakes.make_cog(Prefix)
        guild = fakes.make_guild()
        moderator = fakes.make_member(guild, permissions=discord.Permissions(manage_guild=True))
        with pytest.raises(lyerrors.TakinaPermissionError, match="Administrator"):
            await fakes.run_checks(cog.set_prefix, fakes.make_ctx(guild=guild, author=moderator))
