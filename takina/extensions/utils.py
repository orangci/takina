import re
from nextcord.ext import commands
import nextcord

MODERATOR_ROLE_ID = 830875873027817484


class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot: commands.Bot = bot

    @commands.command()
    @commands.has_role(MODERATOR_ROLE_ID)
    async def send(
        self,
        ctx: commands.Context,
        channel: nextcord.TextChannel = None,
        *,
        message: str,
    ):
        """Send a message as Anna."""
        if channel and message:
            await channel.send(message)
        elif message:
            await ctx.send(message)
        else:
            await ctx.send("Please provide a message and channel to use this command.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int):
        """Purges a specified number of messages."""

        # Ensure the number is a positive integer
        if amount <= 0:
            await ctx.send("Please specify a positive number of messages to purge.")
            return

        # Perform the purge
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"Successfully purged {len(deleted)} messages.", delete_after=3)


def setup(bot: commands.Bot):
    bot.add_cog(Utils(bot))
