# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import nextcord
import config
from nextcord.ext import application_checks, commands

from ..libs import oclib


class Warnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="warn", help="Warn a member.", usage="@member spamming in #manga")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx: commands.Context, member: str, *, reason: str):
        member = oclib.extract_user_id(member, ctx)
        if isinstance(member, nextcord.Embed):
            await ctx.reply(embed=member, mention_author=False)
            return

        can_proceed, message = oclib.perms_check(member, ctx=ctx)
        if not can_proceed:
            await ctx.reply(embed=message, mention_author=False)
            return

        confirmation = oclib.ConfirmationView(ctx=ctx, member=member, action="warn", reason=reason)
        confirmed = await confirmation.prompt()
        if not confirmed:
            return

        # Send success embed
        embed = nextcord.Embed(
            description=f"✅ Successfully warned **{member.mention}**. \n\n<:note:1289880498541297685> **Reason:** {reason}\n<:salute:1287038901151862795> **Moderator:** {ctx.author}",
            color=config.EMBED_COLOR,
        )
        try:
            dm_embed = nextcord.Embed(
                description=f"You were warned in **{ctx.guild}**. \n\n<:note:1289880498541297685> **Reason:** {reason}", color=config.EMBED_COLOR
            )
            await member.send(embed=dm_embed)
        except nextcord.Forbidden:
            embed.set_footer(text="I was unable to DM this user.")
        await ctx.reply(embed=embed, mention_author=False)

        modlog_cog = self.bot.get_cog("ModLog")
        if modlog_cog:
            await modlog_cog.log_action("warn", member, reason, ctx.author)


class SlashWarnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="warn", description="Warn a member.")
    @application_checks.has_permissions(moderate_members=True)
    async def warn(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(description="The user to warn", required=True),
        reason: str = nextcord.SlashOption(description="The reason for warning the user", required=True),
    ):
        await interaction.response.defer()

        can_proceed, message = oclib.perms_check(member, ctx=interaction)
        if not can_proceed:
            await interaction.send(embed=message, ephemeral=True)
            return

        confirmation = oclib.ConfirmationView(ctx=interaction, member=member, action="warn", reason=reason)
        confirmed = await confirmation.prompt()
        if not confirmed:
            return

        # Send success embed
        embed = nextcord.Embed(
            description=f"✅ Successfully warned **{member.mention}**. \n\n<:note:1289880498541297685> **Reason:** {reason}\n<:salute:1287038901151862795> **Moderator:** {interaction.user}",
            color=config.EMBED_COLOR,
        )
        try:
            dm_embed = nextcord.Embed(
                description=f"You were warned in **{interaction.guild}**. \n\n<:note:1289880498541297685> **Reason:** {reason}",
                color=config.EMBED_COLOR,
            )
            await member.send(embed=dm_embed)
        except nextcord.Forbidden:
            embed.set_footer(text="I was unable to DM this user.")
        await interaction.send(embed=embed)

        modlog_cog = self.bot.get_cog("ModLog")
        if modlog_cog:
            await modlog_cog.log_action("warn", member, reason, interaction.user)


def setup(bot):
    bot.add_cog(Warnings(bot))
    bot.add_cog(SlashWarnings(bot))
