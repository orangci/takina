from __future__ import annotations
import requests  # new import for the API
from ..libs.oclib import *
import nextcord
from nextcord.ext import commands
from config import *


class Roast(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.command(
        name="roast",
        help="Get roasted by the bot. \nUsage: `roast`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def roast(self, ctx: commands.Context):
        try:
            response = requests.get("https://evilinsult.com/generate_insult.php?lang=en&type=json")
            data = response.json()
            insult = data.get("insult", "Couldn't fetch a roast right now.")
        except Exception:
            insult = "Couldn't fetch a roast right now. Try again later."

        embed = nextcord.Embed(
            title=f"Hey {ctx.author.mention}!",
            description=f"{ctx.author.mention} {insult}",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)


class SlashRoast(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @nextcord.slash_command(
        name="roast",
        description="Get roasted by the bot.",
    )
    async def roast(self, interaction: nextcord.Interaction):
        try:
            response = requests.get("https://evilinsult.com/generate_insult.php?lang=en&type=json")
            data = response.json()
            insult = data.get("insult", "Couldn't fetch a roast right now.")
        except Exception:
            insult = "Couldn't fetch a roast right now. Try again later."

        embed = nextcord.Embed(
            title=f"Hey {interaction.user.name}!",
            description=f"{interaction.user.mention} {insult}",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Roast(bot))
    bot.add_cog(SlashRoast(bot))
