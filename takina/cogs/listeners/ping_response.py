import nextcord
from nextcord.ext import commands
from __main__ import EMBED_COLOR
import os

PREFIX = os.getenv("PREFIX")


class PingResponse(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if self.bot.user.mentioned_in(message) and not message.author.bot:
            embed = nextcord.Embed(
                description=f"Hi {message.author.mention}, my prefix is `{PREFIX}`",
                color=EMBED_COLOR,
            )
            await message.reply(embed=embed, mention_author=False)


def setup(bot: commands.Bot):
    bot.add_cog(PingResponse(bot))
