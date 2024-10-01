import nextcord
from nextcord.ext import commands
import asyncio
import re
from datetime import timedelta
from __main__ import BOT_NAME, EMBED_COLOR
from ..libs.oclib import *


class Ban(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        member: str = None,
        *,
        reason: str = "No reason provided",
    ):
        member = extract_user_id(member, ctx)
        if not isinstance(member, nextcord.Member):
            await ctx.reply(
                "Member not found. Please provide a valid username, display name, mention, or user ID.",
                mention_author=False,
            )
            return
        if not member:
            await ctx.reply(
                "Please mention a member to ban. Usage: `ban @member [reason]`.",
                mention_author=False,
            )
            return

        if member == ctx.author:
            await ctx.reply("You can't ban yourself.", mention_author=False)
            return

        if member == ctx.guild.owner:
            await ctx.reply("You can't ban the server owner.", mention_author=False)
            return

        if member.top_role >= ctx.author.top_role:
            await ctx.reply(
                "You can't ban members with a higher or equal role than yours.",
                mention_author=False,
            )
            return

        if member.top_role >= ctx.guild.me.top_role:
            await ctx.reply(
                "I can't ban members with a higher or equal role than mine.",
                mention_author=False,
            )
            return

        try:
            await member.ban(reason=reason)
            embed = nextcord.Embed(
                description=f"✅ Successfully banned **{member.name}**.",
                color=EMBED_COLOR,
            )
            await ctx.reply(embed=embed, mention_author=False)
        except nextcord.Forbidden:
            await ctx.reply(
                "I don't have permission to ban this member.", mention_author=False
            )
        except nextcord.HTTPException:
            await ctx.reply(
                "An error occurred while trying to ban the member.",
                mention_author=False,
            )


class Unban(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="unban", aliases=["pardon"])
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, id: str):
        user = await self.bot.fetch_user(int(id)) or await self.bot.fetch_user(id)
        await ctx.guild.unban(user)
        embed = nextcord.Embed(
            description="✅  " + f"Successfully unbanned **{user}**.", color=EMBED_COLOR
        )
        await ctx.reply(embed=embed, mention_author=False)

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.reply(
                "User not found. Please make sure the User ID is correct.",
                mention_author=False,
            )


class BanSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="ban", description="Ban a member from the server.")
    @commands.has_permissions(ban_members=True)
    async def ban(
        self,
        ctx: nextcord.Interaction,
        member: nextcord.Member = None,
        reason: str = "No reason provided",
    ):
        if not member:
            await ctx.response.send_message(
                "Please mention a member to ban. Usage: `ban @member [reason]`.",
                ephemeral=True,
            )
            return

        if member == ctx.user:
            await ctx.response.send_message("You can't ban yourself.", ephemeral=True)
            return

        if member == ctx.guild.owner:
            await ctx.response.send_message(
                "You can't ban the server owner.", ephemeral=True
            )
            return

        if member.top_role >= ctx.user.top_role:
            await ctx.response.send_message(
                "You can't ban members with a higher or equal role than yours.",
                ephemeral=True,
            )
            return

        if member.top_role >= ctx.guild.me.top_role:
            await ctx.response.send_message(
                "I can't ban members with a higher or equal role than mine.",
                ephemeral=True,
            )
            return

        try:
            await member.ban(reason=reason)
            embed = nextcord.Embed(
                description=f"✅ Successfully banned **{member.name}**.",
                color=EMBED_COLOR,
            )
            await ctx.response.send_message(embed=embed)
        except nextcord.Forbidden:
            await ctx.response.send_message(
                "I don't have permission to ban this member.", ephemeral=True
            )
        except nextcord.HTTPException:
            await ctx.response.send_message(
                "An error occurred while trying to ban the member.", ephemeral=True
            )


class UnbanSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="unban", description="Unban a member from the server.")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: nextcord.Interaction, id: str):
        try:
            user = await self.bot.fetch_user(int(id))
            await ctx.guild.unban(user)
            embed = nextcord.Embed(
                description="✅ Successfully unbanned **{user}**.", color=EMBED_COLOR
            )
            await ctx.response.send_message(embed=embed)
        except nextcord.NotFound:
            await ctx.response.send_message(
                "User not found. Please make sure the User ID is correct.",
                ephemeral=True,
            )


def setup(bot):
    bot.add_cog(Ban(bot))
    bot.add_cog(BanSlash(bot))
    bot.add_cog(Unban(bot))
    bot.add_cog(UnbanSlash(bot))
