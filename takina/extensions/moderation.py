import nextcord
from nextcord.ext import commands
import asyncio
import re
from datetime import timedelta

class Ban(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: nextcord.Member = None, *, reason: str = "No reason provided"):
        if not member:
            await ctx.reply("Please mention a member to ban. Usage: `ban @member [reason]`", mention_author=False)
            return

        if member == ctx.author:
            await ctx.reply("You can't ban yourself.", mention_author=False)
            return

        if member == ctx.guild.owner:
            await ctx.reply("You can't ban the server owner.", mention_author=False)
            return

        if member.top_role >= ctx.author.top_role:
            await ctx.reply("You can't ban members with a higher or equal role than yours.", mention_author=False)
            return

        if member.top_role >= ctx.guild.me.top_role:
            await ctx.reply("I can't ban members with a higher or equal role than mine.", mention_author=False)
            return

        try:
            await member.ban(reason=reason)
            embed = nextcord.Embed(description=f"✅ Successfully banned **{member.name}**.", color=0x2F52A3)
            await ctx.reply(embed=embed, mention_author=False)
        except nextcord.Forbidden:
            await ctx.reply("I don't have permission to ban this member.", mention_author=False)
        except nextcord.HTTPException:
            await ctx.reply("An error occurred while trying to ban the member.", mention_author=False)

class Unban(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="unban", aliases=["pardon"])
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, id: str) :
        user = await self.bot.fetch_user(int(id)) or await self.bot.fetch_user(id)
        await ctx.guild.unban(user)
        embed = nextcord.Embed(description="✅  "+f"Successfully unbanned **{user}**.", color=0x2F52A3)
        await ctx.reply(embed=embed, mention_author=False)
    
    @unban.error    
    async def unban_error(self, ctx, error):    
        if isinstance(error, commands.BadArgument):
            await ctx.reply("User not found. Please make sure the User ID is correct.", mention_author=False)

class Mute(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: nextcord.Member, duration: str):
        pattern = r'(\d+)([d|h|m])'
        match = re.fullmatch(pattern, duration)

        if not match:
            await ctx.reply("Invalid duration format. Use <number>[d|h|m].", mention_author=False)
            return
        
        time_value, time_unit = match.groups()
        time_value = int(time_value)

        # Convert duration to seconds
        if time_unit == 'd':
            timeout_duration = time_value * 86400  # Days to seconds
        elif time_unit == 'h':
            timeout_duration = time_value * 3600  # Hours to seconds
        elif time_unit == 'm':
            timeout_duration = time_value * 60  # Minutes to seconds

        try:
            await member.timeout(timeout=nextcord.utils.utcnow() + timedelta(seconds=timeout_duration), reason=f"Muted by {ctx.author} for {duration}.")
            embed = nextcord.Embed(description=f"✅ Successfully muted **{member.name}** for {duration}.", color=0x2F52A3)
            await ctx.reply(embed=embed, mention_author=False)
        except nextcord.Forbidden:
            await ctx.reply("I do not have permission to mute this member.", mention_author=False)
        except Exception as e:
            await ctx.reply(f"An error occurred: {str(e)}", mention_author=False)

class Unmute(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx: commands.Context, member: nextcord.Member = None):
        if not member:
            await ctx.reply("Please mention a member to unmute. Usage: `unmute @member`", mention_author=False)
            return

        if member == ctx.guild.owner:
            await ctx.reply("You can't unmute the server owner.", mention_author=False)
            return

        if member.top_role >= ctx.author.top_role:
            await ctx.reply("You can't unmute members with a higher or equal role than yours.", mention_author=False)
            return

        if member.top_role >= ctx.guild.me.top_role:
            await ctx.reply("I can't unmute members with a higher or equal role than mine.", mention_author=False)
            return

        try:
            await member.timeout(None, reason="Takina: Unmuted by moderator")
            embed = nextcord.Embed(description=f"✅ Successfully unmuted **{member.name}**.", color=0x2F52A3)
            await ctx.reply(embed=embed, mention_author=False)
        except nextcord.Forbidden:
            await ctx.reply("I don't have permission to unmute this member.", mention_author=False)
        except nextcord.HTTPException:
            await ctx.reply("An error occurred while trying to unmute this member.", mention_author=False)


class Kick(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: nextcord.Member = None, *, reason: str = "No reason provided"):
        if not member:
            await ctx.reply("Please mention a member to kick. Usage: `kick @member [reason]`", mention_author=False)
            return

        if member == ctx.author:
            await ctx.reply("You can't kick yourself.", mention_author=False)
            return

        if member == ctx.guild.owner:
            await ctx.reply("You can't kick the server owner.", mention_author=False)
            return

        if member.top_role >= ctx.author.top_role:
            await ctx.reply("You can't kick members with a higher or equal role than yours.", mention_author=False)
            return

        if member.top_role >= ctx.guild.me.top_role:
            await ctx.reply("I can't kick members with a higher or equal role than mine.", mention_author=False)
            return

        try:
            await member.kick(reason=reason)
            embed = nextcord.Embed(description=f"✅ Successfully kicked **{member.name}**.", color=0x2F52A3)
            await ctx.reply(embed=embed, mention_author=False)
        except nextcord.Forbidden:
            await ctx.reply("I don't have permission to kick this member.", mention_author=False)
        except nextcord.HTTPException:
            await ctx.reply("An error occurred while trying to kick the member.", mention_author=False)

def setup(bot):
    bot.add_cog(Kick(bot))
    bot.add_cog(Ban(bot))
    bot.add_cog(Unban(bot))
    bot.add_cog(Mute(bot))
    bot.add_cog(Unmute(bot))