import nextcord
from nextcord.ext import commands
from __main__ import EMBED_COLOR


class GhostPing(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: nextcord.Message):
        # Ignore messages from bots or messages without mentions
        if message.author.bot or not message.mentions:
            return

        # Filter mentions to exclude the author and any bots
        ghost_pinged_users = [
            user for user in message.mentions if user != message.author and not user.bot
        ]

        # If there are no valid ghost-pinged users, return
        if not ghost_pinged_users:
            return

        # Format the mentions into a single message
        mention_list = ", ".join(user.mention for user in ghost_pinged_users)

        # Create an embed to display the ghost-pinged message
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

        # Send a message notifying each ghost-pinged user
        await message.channel.send(
            content=f"{mention_list}, you were ghost pinged by {message.author.mention}!",
            embed=embed,
        )


def setup(bot):
    bot.add_cog(GhostPing(bot))
