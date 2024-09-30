import nextcord
from nextcord.ext import commands
import asyncio
import re
from datetime import timedelta
from __main__ import BOT_NAME, EMBED_COLOR
from ..lib.oclib import *

class Kick(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: str = None, *, reason: str = "No reason provided"):
        member = extract_user_id(member, ctx)
        if not member:
            await ctx.reply("Please mention a member to kick. Usage: `kick @member [reason]`.", mention_author=False)
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
            embed = nextcord.Embed(description=f"✅ Successfully kicked **{member.name}**.", color=EMBED_COLOR)
            await ctx.reply(embed=embed, mention_author=False)
        except nextcord.Forbidden:
            await ctx.reply("I don't have permission to kick this member.", mention_author=False)
        except nextcord.HTTPException:
            await ctx.reply("An error occurred while trying to kick the member.", mention_author=False)

class KickSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="kick", description="Kick a member from the server.")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: nextcord.Interaction, member: nextcord.Member = None, reason: str = "No reason provided"):
        if not member:
            await ctx.response.send_message("Please mention a member to kick. Usage: `kick @member [reason]`.", ephemeral=True)
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
            embed = nextcord.Embed(description=f"✅ Successfully kicked **{member.name}**.", color=EMBED_COLOR)
            await ctx.response.send_message(embed=embed, ephemeral=False)
        except nextcord.Forbidden:
            await ctx.response.send_message("I don't have permission to kick this member.", ephemeral=True)
        except nextcord.HTTPException:
            await ctx.response.send_message("An error occurred while trying to kick the member.", ephemeral=True)

def setup(bot):
    bot.add_cog(Kick(bot))
    bot.add_cog(KickSlash(bot))