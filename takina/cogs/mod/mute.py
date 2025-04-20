# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import nextcord
from nextcord.ext import application_checks, commands
from datetime import timedelta
from config import *
from ..libs.oclib import *


class Mute(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="mute",
        help="Timeout a member. \nUsage: `mute <member> <duration> <reason>`.",
        aliases=["timeout"],
    )
    @commands.has_permissions(moderate_members=True)
    async def mute(
        self, ctx, member: str, duration: str, *, reason: str = "No reason provided"
    ):
        timeout_duration = duration_calculator(duration, timeout=True)
        if isinstance(timeout_duration, nextcord.Embed):
            await ctx.reply(embed=timeout_duration, mention_author=False)
            return

        member = extract_user_id(member, ctx)
        if isinstance(member, nextcord.Embed):
            await ctx.reply(embed=member, mention_author=False)
            return

        can_proceed, message = perms_check(member, ctx=ctx)
        if not can_proceed:
            await ctx.reply(embed=message, mention_author=False)
            return

        confirmation = ConfirmationView(
            ctx=ctx, member=member, action="mute", reason=reason, duration=duration
        )
        confirmed = await confirmation.prompt()
        if not confirmed:
            return

        # Apply the timeout
        await member.timeout(
            timeout=nextcord.utils.utcnow() + timedelta(seconds=timeout_duration),
            reason=f"Muted by {ctx.author} for: {reason}",
        )

        # Send success embed
        embed = nextcord.Embed(
            description=f"✅ Successfully muted **{member.mention}** for {duration}. \n\n<:note:1289880498541297685> **Reason:** {reason}\n<:salute:1287038901151862795> **Moderator:** {ctx.author}",
            color=EMBED_COLOR,
        )
        try:
            dm_embed = nextcord.Embed(
                description=f"You were muted in **{ctx.guild}** for {duration}. \n\n<:note:1289880498541297685> **Reason:** {reason}",
                color=EMBED_COLOR,
            )
            await member.send(embed=dm_embed)
        except nextcord.Forbidden:
            embed.set_footer(text="I was unable to DM this user.")
        await ctx.reply(embed=embed, mention_author=False)

        modlog_cog = self.bot.get_cog("ModLog")
        if modlog_cog:
            await modlog_cog.log_action("mute", member, reason, ctx.author, duration)


class Unmute(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="unmute",
        help="Unmute a member. \nUsage: `unmute <member> <reason>`.",
    )
    @commands.has_permissions(moderate_members=True)
    async def unmute(
        self, ctx: commands.Context, member: str, *, reason: str = "No reason provided"
    ):
        member = extract_user_id(member, ctx)
        if isinstance(member, nextcord.Embed):
            await ctx.reply(embed=member, mention_author=False)
            return

        can_proceed, message = perms_check(member, ctx=ctx)
        if not can_proceed:
            await ctx.reply(embed=message, mention_author=False)
            return

        await member.timeout(None, reason=f"Unmuted by {ctx.author} for: {reason}")
        embed = nextcord.Embed(
            description=f"✅ Successfully unmuted **{member.mention}**. \n\n<:note:1289880498541297685> **Reason:** {reason}\n<:salute:1287038901151862795> **Moderator:** {ctx.author}",
            color=EMBED_COLOR,
        )
        dm_embed = nextcord.Embed(
            description=f"You were unmuted in **{ctx.guild}**. \n\n<:note:1289880498541297685> **Reason:** {reason}",
            color=EMBED_COLOR,
        )
        try:
            await member.send(embed=dm_embed)
        except Exception as e:
            embed.set_footer(text="I was unable to DM this user.")
        await ctx.reply(embed=embed, mention_author=False)

        modlog_cog = self.bot.get_cog("ModLog")
        if modlog_cog:
            await modlog_cog.log_action("unmute", member, reason, ctx.author)


class MuteSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(
        name="mute", description="Timeout a member for a specified duration."
    )
    @application_checks.has_permissions(moderate_members=True)
    async def mute(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(
            description="The user to mute", required=True
        ),
        duration: str = nextcord.SlashOption(
            description="The duration of time to mute the user for", required=True
        ),
        reason: str = "No reason provided",
    ):
        await interaction.response.defer()
        timeout_duration = duration_calculator(duration, timeout=True)
        can_proceed, message = perms_check(member, ctx=interaction)
        if not can_proceed:
            await interaction.send(embed=message, ephemeral=True)
            return

        confirmation = ConfirmationView(
            ctx=interaction,
            member=member,
            action="mute",
            reason=reason,
            duration=duration,
        )
        confirmed = await confirmation.prompt()
        if not confirmed:
            return

        await member.timeout(
            timeout=nextcord.utils.utcnow() + timedelta(seconds=timeout_duration),
            reason=f"Muted by {interaction.user} for: {reason}",
        )
        embed = nextcord.Embed(
            description=f"✅ Successfully muted **{member.mention}** for {duration}. \n\n<:note:1289880498541297685> **Reason:** {reason}\n<:salute:1287038901151862795> **Moderator:** {interaction.user}",
            color=EMBED_COLOR,
        )
        dm_embed = nextcord.Embed(
            description=f"You were muted in **{interaction.guild}** for {duration}. \n\n<:note:1289880498541297685> **Reason:** {reason}",
            color=EMBED_COLOR,
        )
        try:
            await member.send(embed=dm_embed)
        except Exception as e:
            embed.set_footer(text="I was unable to DM this user.")
        await interaction.send(embed=embed)

        modlog_cog = self.bot.get_cog("ModLog")
        if modlog_cog:
            await modlog_cog.log_action(
                "mute", member, reason, interaction.user, duration
            )


class UnmuteSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="unmute", description="Unmute a member.")
    @application_checks.has_permissions(moderate_members=True)
    async def unmute(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(
            description="The user to unmute", required=True
        ),
        reason: str = "No reason provided",
    ):
        await interaction.response.defer()
        can_proceed, message = perms_check(member, ctx=interaction)
        if not can_proceed:
            await interaction.send(embed=message, ephemeral=True)
            return

        await member.timeout(
            None, reason=f"Unmuted by {interaction.user} for: {reason}"
        )
        embed = nextcord.Embed(
            description=f"✅ Successfully unmuted **{member.mention}**. \n\n<:note:1289880498541297685> **Reason:** {reason}\n<:salute:1287038901151862795> **Moderator:** {interaction.user}",
            color=EMBED_COLOR,
        )
        dm_embed = nextcord.Embed(
            description=f"You were unmuted in **{interaction.guild}**. \n\n<:note:1289880498541297685> **Reason:** {reason}",
            color=EMBED_COLOR,
        )
        try:
            await member.send(embed=dm_embed)
        except Exception as e:
            embed.set_footer(text="I was unable to DM this user.")
        await interaction.send(embed=embed)

        modlog_cog = self.bot.get_cog("ModLog")
        if modlog_cog:
            await modlog_cog.log_action("unmute", member, reason, interaction.user)


def setup(bot):
    bot.add_cog(Mute(bot))
    bot.add_cog(Unmute(bot))
    bot.add_cog(MuteSlash(bot))
    bot.add_cog(UnmuteSlash(bot))
