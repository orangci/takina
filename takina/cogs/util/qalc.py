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
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        return None

    return stdout.decode().strip()


class Qalc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["calc", "calculate", "qalculate", "qc"], help="Mathematical calculation evaluation.", usage="6 * 7")
    async def qalc(self, ctx: commands.Context, *, calculation: str):
        result = await qalc(calculation)
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        if not result:
            embed.description = ":x: Invalid expression."
            embed.color = config.ERROR_COLOR
        else:
            embed.description = f"{await oclib.fetch_random_emoji()} {result}"
        await ctx.reply(embed=embed, mention_author=False)
        pass

    @nextcord.slash_command(name="calculate", description="Mathematical calculation evaluation.")
    async def slash_qalc(
        self,
        interaction: nextcord.Interaction,
        *,
        calculation: str = nextcord.SlashOption(description="The mathematical calculation to evaluate.", required=True),
    ):
        await interaction.response.defer()
        result = await qalc(calculation)
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        if not result:
            embed.description = ":x: Invalid expression."
            embed.color = config.ERROR_COLOR
        else:
            embed.description = f"{await oclib.fetch_random_emoji()} {result}"
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    if shutil.which("qalc") is None and not os.getenv("NIXOS_INSTANCE"):
        print("Skipping loading of util.qalc, as libqalculate is not installed/available on the system.")
        return
    bot.add_cog(Qalc(bot))
