import nextcord
from nextcord.ext import application_checks, commands
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
        can_proceed, message = perms_check(member, ctx=ctx)
        if not can_proceed:
            await ctx.reply(message, mention_author=False)
            return

        embed = nextcord.Embed(
            description=f"✅ Successfully banned **{member.name}**. Reason: {reason}",
            color=EMBED_COLOR,
        )
        dm_embed = nextcord.Embed(
            description=f"You were banned in **{ctx.guild}**. Reason: {reason}",
            color=EMBED_COLOR,
        )
        try:
            await member.send(embed=dm_embed)
        except nextcord.Forbidden:
            embed.set_footer(text="I was unable to DM this user.")
        await member.ban(reason=reason)
        await ctx.reply(embed=embed, mention_author=False)


class Unban(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="unban", aliases=["pardon"])
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, id: str, reason: str = "No reason provided"):
        user = await self.bot.fetch_user(int(id)) or await self.bot.fetch_user(id)
        await ctx.guild.unban(user)
        embed = nextcord.Embed(
            description=f"✅ Successfully unbanned **{user}**. Reason: {reason}",
            color=EMBED_COLOR,
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
    @application_checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(
            description="The member to ban", required=True
        ),
        reason: str = "No reason provided",
    ):
        can_proceed, message = perms_check(member, ctx=interaction)
        if not can_proceed:
            await interaction.send(message, ephemeral=True)
            return

        embed = nextcord.Embed(
            description=f"✅ Successfully banned **{member.name}**. Reason: {reason}",
            color=EMBED_COLOR,
        )
        dm_embed = nextcord.Embed(
            description=f"You were banned in **{ctx.guild}**. Reason: {reason}",
            color=EMBED_COLOR,
        )
        try:
            await member.send(embed=dm_embed)
        except nextcord.Forbidden:
            embed.set_footer(text="I was unable to DM this user.")
        await member.ban(reason=reason)
        await interaction.send(embed=embed)


class UnbanSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="unban", description="Unban a member from the server.")
    @application_checks.has_permissions(ban_members=True)
    async def unban(
        self,
        interaction: nextcord.Interaction,
        id: int = nextcord.SlashOption(
            description="The user ID to unban", required=True
        ),
        reason: str = "No reason provided",
    ):
        try:
            user = await self.bot.fetch_user(id)
            await interaction.guild.unban(user)
            embed = nextcord.Embed(
                description=f"✅ Successfully unbanned **{user}**. Reason: {reason}",
                color=EMBED_COLOR,
            )
            await interaction.send(embed=embed)
        except nextcord.NotFound:
            await interaction.send(
                "User not found. Please make sure the User ID is correct.",
                ephemeral=True,
            )


def setup(bot):
    bot.add_cog(Ban(bot))
    bot.add_cog(BanSlash(bot))
    bot.add_cog(Unban(bot))
    bot.add_cog(UnbanSlash(bot))
