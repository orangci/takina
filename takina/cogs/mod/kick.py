import nextcord
from nextcord.ext import application_checks, commands
import asyncio
import re
from datetime import timedelta
from __main__ import BOT_NAME, EMBED_COLOR
from ..libs.oclib import *


class Kick(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(
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
            description=f"✅ Successfully kicked **{member.name}**. Reason: {reason}",
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
        await member.kick(reason=reason)
        await ctx.reply(embed=embed, mention_author=False)


class KickSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="kick", description="Kick a member from the server.")
    @application_checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(
            description="The user to kick", required=True
        ),
        reason: str = "No reason provided",
    ):
        can_proceed, message = perms_check(member, ctx=interaction)
        if not can_proceed:
            await interaction.send(message, ephemeral=True)
            return

        embed = nextcord.Embed(
            description=f"✅ Successfully kicked **{member.name}**. Reason: {reason}",
            color=EMBED_COLOR,
        )
        dm_embed = nextcord.Embed(
            description=f"You were banned in **{interaction.guild}**. Reason: {reason}",
            color=EMBED_COLOR,
        )
        try:
            await member.send(embed=dm_embed)
        except nextcord.Forbidden:
            embed.set_footer(text="I was unable to DM this user.")
        await member.kick(reason=reason)
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(Kick(bot))
    bot.add_cog(KickSlash(bot))
