# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
from ..libs.topics_list import topics
from ..libs import oclib
import nextcord
import random
import config


class Topic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(help="Fetch a random conversational topic.")
    async def topic(self, ctx: commands.Context):
        embed = nextcord.Embed(description=f"{random.choice(topics)} {await oclib.fetch_random_emoji()}", color=config.EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="topic", description="Fetch a random conversational topic.")
    async def slash_topic(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(description=f"{random.choice(topics)} {await oclib.fetch_random_emoji()}", color=config.EMBED_COLOR)
        await interaction.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Topic(bot))
