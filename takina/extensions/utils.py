import re
from nextcord.ext import commands
import nextcord

MODERATOR_ROLE_ID = 830875873027817484

def extract_user_id(mention: str) -> str:
    match = re.match(r'<@!?(\d+)>', mention)
    if match:
        return match.group(1)
    return None


class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot: commands.Bot = bot
    
    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Ping the bot."""
        latency = round(self._bot.latency * 1000)
        await ctx.reply(f"Success! Takina is awake. Ping: {latency}ms", mention_author=False)

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
            await ctx.reply(message, mention_author=False)
        else:
            await ctx.reply("Please provide a message and channel to use this command.", mention_author=False)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int):
        """Purges a specified number of messages."""

        # Ensure the number is a positive integer
        if amount <= 0:
            await ctx.reply("Please specify a positive number of messages to purge.", mention_author=False)
            return

        deleted = await ctx.channel.purge(limit=amount)
        await ctx.reply(f"Successfully purged {len(deleted)} messages.", delete_after=3, mention_author=False)

    @commands.command(aliases=["setnick"])
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx: commands.Context, member: str = None, *, nickname: str = None):
        if member is None:
            member = ctx.author
        else:
            user_id = extract_user_id(member)
            if user_id:
                member = ctx.guild.get_member(int(user_id))
            else:
                member = nextcord.utils.get(ctx.guild.members, name=member) or nextcord.utils.get(ctx.guild.members, display_name=member)

        if member is None:
            await ctx.reply("Member not found. Please provide a valid username or display name.", mention_author=False)
            return
        if not member:
            await ctx.reply("Please mention a member to change their nickname. Usage: `nick @member [nickname]`", mention_author=False)
            return

        if member == ctx.author:
            await ctx.reply("You can't change your own nickname using this command.", mention_author=False)
            return

        if member == ctx.guild.owner:
            await ctx.reply("You can't change the server owner's nickname.", mention_author=False)
            return

        if member.top_role >= ctx.author.top_role:
            await ctx.reply("You can't change the nickname of someone with a higher or equal role than yours.", mention_author=False)
            return

        if member.top_role >= ctx.guild.me.top_role:
            await ctx.reply("I can't change the nickname of someone with a higher or equal role than mine.", mention_author=False)
            return

        if not nickname:
            nickname = member.name

        try:
            await member.edit(nick=nickname)
            await ctx.reply(f"**{member.name}**'s nickname has been changed to **{nickname}**.", mention_author=False)
        except nextcord.Forbidden:
            await ctx.reply("I don't have permission to change this member's nickname.", mention_author=False)
        except nextcord.HTTPException:
            await ctx.reply("An error occurred while trying to change the nickname.", mention_author=False)

def setup(bot: commands.Bot):
    bot.add_cog(Utils(bot))
