# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
from ..libs.oclib import *
from config import *
import nextcord


class Roasts(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.command(
        name="roast",
        help="Get roasted by the bot. \nUsage: `roast <user>`.",
    )
    async def roast(self, ctx: commands.Context, target: str = None):
        embed = nextcord.Embed(color=EMBED_COLOR)
        try:
            response = await request(
                "https://evilinsult.com/generate_insult.php?lang=en&type=json"
            )
            embed.description = await fetch_random_emoji() + response.get("insult")
        except Exception:
            embed.description = ":x: Failed to fetch a roast. Try again later!"

        target = ctx.author if not target else target
        if not isinstance(target, nextcord.Member):
            target = extract_user_id(target, ctx)
            if isinstance(target, nextcord.Embed):
                await ctx.reply(embed=target, mention_author=False)
                return

        await ctx.reply(target.mention, embed=embed, mention_author=False)

    @nextcord.slash_command(
        name="roast",
        description="Get roasted by the bot.",
    )
    async def slash_roast(
        self,
        interaction: nextcord.Interaction,
        target: nextcord.Member = nextcord.SlashOption(
            description="The user you would like to roast", required=False
        ),
    ):
        embed = nextcord.Embed(color=EMBED_COLOR)
        try:
            response = await request(
                "https://evilinsult.com/generate_insult.php?lang=en&type=json"
            )
            embed.description = await fetch_random_emoji() + response.get("insult")
        except Exception:
            embed.description = ":x: Failed to fetch a roast. Try again later!"

        target = interaction.user if not target else target
        await interaction.send(target.mention, embed=embed)


def setup(bot):
    bot.add_cog(Roasts(bot))
