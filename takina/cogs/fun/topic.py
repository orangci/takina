import random
import nextcord
from nextcord.ext import commands
from ..libs.topics_list import topics
from __main__ import EMBED_COLOR
from ..libs.oclib import *


class Topic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def topic(self, ctx: commands.Context):
        """Sends a random topic."""
        random_topic = random.choice(topics)
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(description=f"{random_topic} {emoji}", color=EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="topic")
    async def topic_slash(self, interaction: nextcord.Interaction):
        """Sends a random topic."""
        random_topic = random.choice(topics)
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(description=f"{random_topic} {emoji}", color=EMBED_COLOR)
        await interaction.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Topic(bot))
