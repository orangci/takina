# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
from ..libs import oclib
import nextcord
import asyncio
import shutil
import config
import os

qalc_package = os.getenv("QALC")


async def qalc(expr: str):
    proc = await asyncio.create_subprocess_exec(qalc_package, "-t", expr, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    try:
        stdout, stderr = await proc.communicate()
    except asyncio.CancelledError:
        if proc.returncode is None:
            proc.kill()
        await proc.wait()
        raise

    if proc.returncode != 0:
        return None

    return stdout.decode().strip()


async def qalc_embed(expr: str):
    embed = nextcord.Embed(color=config.EMBED_COLOR)

    try:
        async with asyncio.timeout(config.QALC_TIMEOUT):
            result = await qalc(expr)

        if not result:
            embed.description = ":x: Invalid expression."
            embed.color = config.ERROR_COLOR
        else:
            embed.description = f"{await oclib.fetch_random_emoji()} {result}"
    except TimeoutError:
        embed.color = config.ERROR_COLOR
        embed.description = ":x: Calculation timed out."

    return embed


class Qalc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["calc", "calculate", "qalculate", "qc"], help="Mathematical calculation evaluation.", usage="6 * 7")
    async def qalc(self, ctx: commands.Context, *, calculation: str):
        await ctx.reply(embed=await qalc_embed(calculation), mention_author=False)

    @nextcord.slash_command(name="calculate", description="Mathematical calculation evaluation.")
    async def slash_qalc(
        self,
        interaction: nextcord.Interaction,
        *,
        calculation: str = nextcord.SlashOption(description="The mathematical calculation to evaluate.", required=True),
    ):
        await interaction.response.defer()
        await interaction.send(embed=await qalc_embed(calculation), ephemeral=True)


def setup(bot: commands.Bot):
    if shutil.which("qalc") is None and not config.NIXOS_INSTANCE:
        print("Skipping loading of util.qalc, as libqalculate is not installed/available on the system.")
        return
    bot.add_cog(Qalc(bot))
