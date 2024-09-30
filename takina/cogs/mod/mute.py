import nextcord
from nextcord.ext import commands
import asyncio
import re
from datetime import timedelta
from __main__ import BOT_NAME, EMBED_COLOR
from ..lib.oclib import *

class Mute(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: str, duration: str):
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
        
        member = extract_user_id(member, ctx)
        if not isinstance(member, nextcord.Member):
            await ctx.reply("Member not found. Please provide a valid username, display name, mention, or user ID.", mention_author=False)
            return
        
        try:
            await member.timeout(timeout=nextcord.utils.utcnow() + timedelta(seconds=timeout_duration), reason=f"Muted by {ctx.author} for {duration}.")
            embed = nextcord.Embed(description=f"✅ Successfully muted **{member.name}** for {duration}.", color=EMBED_COLOR)
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
    async def unmute(self, ctx: commands.Context, member: str):
        member = extract_user_id(member, ctx)
        if not member:
            await ctx.reply("Please mention a member to unmute. Usage: `unmute @member`.", mention_author=False)
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
            await member.timeout(None, reason=f"{BOT_NAME}: Unmuted by moderator")
            embed = nextcord.Embed(description=f"✅ Successfully unmuted **{member.name}**.", color=EMBED_COLOR)
            await ctx.reply(embed=embed, mention_author=False)
        except nextcord.Forbidden:
            await ctx.reply("I don't have permission to unmute this member.", mention_author=False)
        except nextcord.HTTPException:
            await ctx.reply("An error occurred while trying to unmute this member.", mention_author=False)

class MuteSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="mute", description="Mute a member for a specified duration.")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx: nextcord.Interaction, member: nextcord.Member, duration: str):
        pattern = r'(\d+)([d|h|m])'
        match = re.fullmatch(pattern, duration)

        if not match:
            await ctx.response.send_message("Invalid duration format. Use <number>[d|h|m].", ephemeral=True)
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
            await member.timeout(timeout=nextcord.utils.utcnow() + timedelta(seconds=timeout_duration), reason=f"Muted by {ctx.user} for {duration}.")
            embed = nextcord.Embed(description=f"✅ Successfully muted **{member.name}** for {duration}.", color=EMBED_COLOR)
            await ctx.response.send_message(embed=embed, ephemeral=False)
        except nextcord.Forbidden:
            await ctx.response.send_message("I do not have permission to mute this member.", ephemeral=True)
        except Exception as e:
            await ctx.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

class UnmuteSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="unmute", description="Unmute a member.")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx: nextcord.Interaction, member: nextcord.Member = None):
        if not member:
            await ctx.response.send_message("Please mention a member to unmute. Usage: `unmute @member`.", ephemeral=True)
            return

        if member == ctx.guild.owner:
            await ctx.response.send_message("You can't unmute the server owner.", ephemeral=True)
            return

        if member.top_role >= ctx.user.top_role:
            await ctx.response.send_message("You can't unmute members with a higher or equal role than yours.", ephemeral=True)
            return

        if member.top_role >= ctx.guild.me.top_role:
            await ctx.response.send_message("I can't unmute members with a higher or equal role than mine.", ephemeral=True)
            return

        try:
            await member.timeout(None, reason=f"{BOT_NAME}: Unmuted by moderator")
            embed = nextcord.Embed(description=f"✅ Successfully unmuted **{member.name}**.", color=EMBED_COLOR)
            await ctx.response.send_message(embed=embed, ephemeral=False)
        except nextcord.Forbidden:
            await ctx.response.send_message("I don't have permission to unmute this member.", ephemeral=True)
        except nextcord.HTTPException:
            await ctx.response.send_message("An error occurred while trying to unmute this member.", ephemeral=True)

def setup(bot):
    bot.add_cog(Mute(bot))
    bot.add_cog(Unmute(bot))
    bot.add_cog(MuteSlash(bot))
    bot.add_cog(UnmuteSlash(bot))