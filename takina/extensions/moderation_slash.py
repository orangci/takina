import nextcord
from nextcord.ext import commands
import re
from datetime import timedelta

class BanSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="ban", description="Ban a member from the server.")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: nextcord.Interaction, member: nextcord.Member = None, reason: str = "No reason provided"):
        if not member:
            await ctx.response.send_message("Please mention a member to ban. Usage: `/ban @member [reason]`", ephemeral=True)
            return

        if member == ctx.user:
            await ctx.response.send_message("You can't ban yourself.", ephemeral=True)
            return

        if member == ctx.guild.owner:
            await ctx.response.send_message("You can't ban the server owner.", ephemeral=True)
            return

        if member.top_role >= ctx.user.top_role:
            await ctx.response.send_message("You can't ban members with a higher or equal role than yours.", ephemeral=True)
            return

        if member.top_role >= ctx.guild.me.top_role:
            await ctx.response.send_message("I can't ban members with a higher or equal role than mine.", ephemeral=True)
            return

        try:
            await member.ban(reason=reason)
            embed = nextcord.Embed(description=f"✅ Successfully banned **{member.name}**.", color=0x2F52A3)
            await ctx.response.send_message(embed=embed, ephemeral=False)
        except nextcord.Forbidden:
            await ctx.response.send_message("I don't have permission to ban this member.", ephemeral=True)
        except nextcord.HTTPException:
            await ctx.response.send_message("An error occurred while trying to ban the member.", ephemeral=True)

class UnbanSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="unban", description="Unban a member from the server.")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: nextcord.Interaction, id: str):
        try:
            user = await self.bot.fetch_user(int(id))
            await ctx.guild.unban(user)
            embed = nextcord.Embed(description="✅ Successfully unbanned **{user}**.", color=0x2F52A3)
            await ctx.response.send_message(embed=embed, ephemeral=False)
        except nextcord.NotFound:
            await ctx.response.send_message("User not found. Please make sure the User ID is correct.", ephemeral=True)

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
            embed = nextcord.Embed(description=f"✅ Successfully muted **{member.name}** for {duration}.", color=0x2F52A3)
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
            await ctx.response.send_message("Please mention a member to unmute. Usage: `/unmute @member`", ephemeral=True)
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
            await member.timeout(None, reason="Takina: Unmuted by moderator")
            embed = nextcord.Embed(description=f"✅ Successfully unmuted **{member.name}**.", color=0x2F52A3)
            await ctx.response.send_message(embed=embed, ephemeral=False)
        except nextcord.Forbidden:
            await ctx.response.send_message("I don't have permission to unmute this member.", ephemeral=True)
        except nextcord.HTTPException:
            await ctx.response.send_message("An error occurred while trying to unmute this member.", ephemeral=True)

class KickSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="kick", description="Kick a member from the server.")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: nextcord.Interaction, member: nextcord.Member = None, reason: str = "No reason provided"):
        if not member:
            await ctx.response.send_message("Please mention a member to kick. Usage: `/kick @member [reason]`", ephemeral=True)
            return

        if member == ctx.user:
            await ctx.response.send_message("You can't kick yourself.", ephemeral=True)
            return

        if member == ctx.guild.owner:
            await ctx.response.send_message("You can't kick the server owner.", ephemeral=True)
            return

        if member.top_role >= ctx.user.top_role:
            await ctx.response.send_message("You can't kick members with a higher or equal role than yours.", ephemeral=True)
            return

        if member.top_role >= ctx.guild.me.top_role:
            await ctx.response.send_message("I can't kick members with a higher or equal role than mine.", ephemeral=True)
            return

        try:
            await member.kick(reason=reason)
            embed = nextcord.Embed(description=f"✅ Successfully kicked **{member.name}**.", color=0x2F52A3)
            await ctx.response.send_message(embed=embed, ephemeral=False)
        except nextcord.Forbidden:
            await ctx.response.send_message("I don't have permission to kick this member.", ephemeral=True)
        except nextcord.HTTPException:
            await ctx.response.send_message("An error occurred while trying to kick the member.", ephemeral=True)

def setup(bot):
    bot.add_cog(KickSlash(bot))
    bot.add_cog(BanSlash(bot))
    bot.add_cog(UnbanSlash(bot))
    bot.add_cog(MuteSlash(bot))
    bot.add_cog(UnmuteSlash(bot))
