import random
import nextcord
from nextcord.ext import commands
from ..libs.topics_list import topics
from __main__ import EMBED_COLOR
from ..libs.oclib import *


class Topic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(help="Fetch a random conversational topic. \nUsage: `topic`.")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def topic(self, ctx: commands.Context):
        embed = nextcord.Embed(
            description=f"{random.choice(topics)} {await fetch_random_emoji()}",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(
        name="topic", description="Fetch a random conversational topic."
    )
    async def slash_topic(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            description=f"{random.choice(topics)} {await fetch_random_emoji()}",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Topic(bot))
