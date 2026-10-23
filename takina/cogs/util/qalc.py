# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors, lyhelpers, lychecks
from discord.ext import commands
from takina import config
import unicodedata
import asyncio
import discord
import shutil
import os
import re


QALC_PACKAGE = os.getenv("QALC") or shutil.which("qalc")

# qalc functions that reach outside the calculator: command runs programs, load and export
# read and write files, plot spawns gnuplot, save writes definitions to disk, and function
# evaluates a string, which char and concatenate can assemble into any of the others
BLOCKED_FUNCTIONS = ("command", "load", "export", "plot", "save", "function", "char", "concatenate")

# no path, so command can't find programs by name, no token in /proc/self/environ,
# and the C locale, so qalc's translated function names stay off
QALC_ENVIRONMENT = {"LC_ALL": "C", "PATH": "", "HOME": os.getenv("HOME", "/var/empty")}


def blocked_function(expression: str) -> str | None:
    # qalc ignores case, and anything between letters could split a name past a plain match
    letters = re.sub(r"[^a-z]", "", unicodedata.normalize("NFKC", expression).casefold())
    return next((name for name in BLOCKED_FUNCTIONS if name in letters), None)


class Qalc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def qalc_expression(self, expr: str) -> str | None:
        assert QALC_PACKAGE is not None
        # -- so an expression starting with - is not read as an option
        proc = await asyncio.create_subprocess_exec(
            QALC_PACKAGE,
            "-t",
            "--",
            expr,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=QALC_ENVIRONMENT,
        )

        try:
            stdout, _ = await proc.communicate()
        except asyncio.CancelledError:
            if proc.returncode is None:
                proc.kill()
            await proc.wait()
            raise

        if proc.returncode != 0:
            return None

        return stdout.decode().strip()

    @commands.hybrid_command(
        name="qalc",
        aliases=["calc", "calculate", "qalculate", "qc", "calculator"],
        description="Mathematical calculation evaluation.",
        usage="6 * 7",
    )
    @lychecks.is_user_app()
    async def qalc(self, ctx: commands.Context, *, calculation: str):
        if name := blocked_function(calculation):
            raise lyerrors.TakinaUserInputError(f"The `{name}` function is not available.")

        await ctx.defer()

        try:
            async with asyncio.timeout(config.QALC_TIMEOUT):
                result = await self.qalc_expression(calculation)
        except TimeoutError:
            raise lyerrors.TakinaError("Calculation timed out.")

        if not result:
            raise lyerrors.TakinaUserInputError("Invalid expression.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = lyhelpers.truncate(
            f"{await lyhelpers.fetch_random_emoji()} {result}", 4096
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    if QALC_PACKAGE is None:
        raise lyerrors.TakinaMissingEnvironmentVariableError(
            "Libqalculate is not installed/available on the system."
        )

    await bot.add_cog(Qalc(bot))
