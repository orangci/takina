import nextcord
from nextcord.ext import application_checks, commands
import asyncio
import re
from datetime import timedelta
from __main__ import BOT_NAME, EMBED_COLOR
from ..libs.oclib import *


class Mute(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: str, duration: str):
        timeout_duration = duration_calculator(duration)
        if timeout_duration is None:
            await ctx.reply(
                "Invalid duration format. Use <number>[d|h|m].", mention_author=False
            )
            return

        member = extract_user_id(member, ctx)
        if not isinstance(member, nextcord.Member):
            await ctx.reply(
                "Member not found. Please provide a valid username, display name, mention, or user ID.",
                mention_author=False,
            )
            return

        await member.timeout(
            timeout=nextcord.utils.utcnow() + timedelta(seconds=timeout_duration),
            reason=f"Muted by {ctx.author} for {duration}.",
        )
        embed = nextcord.Embed(
            description=f"✅ Successfully muted **{member.name}** for {duration}.",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)


class Unmute(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx: commands.Context, member: str):
        member = extract_user_id(member, ctx)
        if not member:
            await ctx.reply(
                "Please mention a member to unmute. Usage: `unmute @member`.",
                mention_author=False,
            )
            return

        if member == ctx.guild.owner:
            await ctx.reply("You can't unmute the server owner.", mention_author=False)
            return

        if member.top_role >= ctx.author.top_role:
            await ctx.reply(
                "You can't unmute members with a higher or equal role than yours.",
                mention_author=False,
            )
            return

        if member.top_role >= ctx.guild.me.top_role:
            await ctx.reply(
                "I can't unmute members with a higher or equal role than mine.",
                mention_author=False,
            )
            return

        await member.timeout(None, reason=f"{BOT_NAME}: Unmuted by moderator")
        embed = nextcord.Embed(
            description=f"✅ Successfully unmuted **{member.name}**.",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)


class MuteSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(
        name="mute", description="Mute a member for a specified duration."
    )
    @application_checks.has_permissions(moderate_members=True)
    async def mute(
        self, interaction: nextcord.Interaction, member: nextcord.Member, duration: str
    ):
        pattern = r"(\d+)([d|h|m])"
        match = re.fullmatch(pattern, duration)

        if not match:
            await interaction.send(
                "Invalid duration format. Use <number>[d|h|m].", ephemeral=True
            )
            return

        time_value, time_unit = match.groups()
        time_value = int(time_value)

        # Convert duration to seconds
        if time_unit == "d":
            timeout_duration = time_value * 86400  # Days to seconds
        elif time_unit == "h":
            timeout_duration = time_value * 3600  # Hours to seconds
        elif time_unit == "m":
            timeout_duration = time_value * 60  # Minutes to seconds

        await member.timeout(
            timeout=nextcord.utils.utcnow() + timedelta(seconds=timeout_duration),
            reason=f"Muted by {ctx.user} for {duration}.",
        )
        embed = nextcord.Embed(
            description=f"✅ Successfully muted **{member.name}** for {duration}.",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed)


class UnmuteSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="unmute", description="Unmute a member.")
    @application_checks.has_permissions(moderate_members=True)
    async def unmute(
        self, interaction: nextcord.Interaction, member: nextcord.Member = None
    ):
        if not member:
            await interaction.send(
                "Please mention a member to unmute. Usage: `unmute @member`.",
                ephemeral=True,
            )
            return

        if member == ctx.guild.owner:
            await interaction.send("You can't unmute the server owner.", ephemeral=True)
            return

        if member.top_role >= ctx.user.top_role:
            await interaction.send(
                "You can't unmute members with a higher or equal role than yours.",
                ephemeral=True,
            )
            return

        if member.top_role >= ctx.guild.me.top_role:
            await interaction.send(
                "I can't unmute members with a higher or equal role than mine.",
                ephemeral=True,
            )
            return

        await member.timeout(None, reason=f"{BOT_NAME}: Unmuted by moderator")
        embed = nextcord.Embed(
            description=f"✅ Successfully unmuted **{member.name}**.",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(Mute(bot))
    bot.add_cog(Unmute(bot))
    bot.add_cog(MuteSlash(bot))
    bot.add_cog(UnmuteSlash(bot))
