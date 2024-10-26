import nextcord
from nextcord.ext import commands
from __main__ import EMBED_COLOR


class GhostPing(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: nextcord.Message):
        # Ignore bot messages and messages without mentions
        if message.author.bot or not message.mentions:
            return

        for mentioned_user in message.mentions:
            embed = nextcord.Embed(
                description=message.content or "*No text content*",
                color=EMBED_COLOR,
                timestamp=message.created_at,
            )
            embed.set_author(
                name=f"{message.author.display_name}",
                icon_url=message.author.avatar.url,
            )
            embed.set_footer(text=f"Deleted in #{message.channel.name}")

            await message.channel.send(
                content=f"{mentioned_user.mention}, you were ghost pinged by {message.author.mention}!",
                embed=embed,
            )


def setup(bot):
    bot.add_cog(GhostPing(bot))
