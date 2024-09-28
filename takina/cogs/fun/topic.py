import random
import nextcord
from nextcord.ext import commands
from cogs.libs.topics_list import topics


class Topic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def topic(self, ctx: commands.Context):
        """Sends a random topic from the predefined list."""
        random_topic = random.choice(topics)
        await ctx.reply(random_topic, mention_author=False)
        
    @nextcord.slash_command(name="topic")
    async def topic_slash(self, interaction: nextcord.Interaction):
        """Sends a random topic from the predefined list."""
        random_topic = random.choice(topics)
        await ctx.send(random_topic)


def setup(bot: commands.Bot):
    bot.add_cog(Topic(bot))
