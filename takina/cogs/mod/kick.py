# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import application_checks, commands
from ..libs import oclib
import nextcord
import config


class Kick(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="kick", help="Kick a member from the server.", usage="@member")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: str = None, *, reason: str = "No reason provided"):
        member = oclib.extract_user_id(member, ctx)
        if isinstance(member, nextcord.Embed):
            await ctx.reply(embed=member, mention_author=False)
            return

        can_proceed, message = oclib.perms_check(member, ctx=ctx)
        if not can_proceed:
            await ctx.reply(embed=message, mention_author=False)
            return

        embed = nextcord.Embed(
            description=f"✅ Successfully kicked **{member.mention}**. \n\n<:note:1289880498541297685> **Reason:** {reason}\n<:salute:1287038901151862795> **Moderator:** {ctx.author}",
            color=config.EMBED_COLOR,
        )
        dm_embed = nextcord.Embed(
            description=f"You were banned in **{ctx.guild}**. \n\n<:note:1289880498541297685> **Reason:** {reason}", color=config.EMBED_COLOR
        )
        confirmation = oclib.ConfirmationView(ctx=ctx, member=member, action="kick", reason=reason)
        confirmed = await confirmation.prompt()
        if not confirmed:
            return
        try:
            await member.send(embed=dm_embed)
        except Exception:
            embed.set_footer(text="I was unable to DM this user.")
        await member.kick(reason=f"Kicked by {ctx.author} for: {reason}")
        await ctx.reply(embed=embed, mention_author=False)

        modlog_cog = self.bot.get_cog("ModLog")
        if modlog_cog:
            await modlog_cog.log_action("kick", member, reason, ctx.author)


class KickSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="kick", description="Kick a member from the server.")
    @application_checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(description="The user to kick", required=True),
        reason: str = "No reason provided",
    ):
        await interaction.response.defer()
        can_proceed, message = oclib.perms_check(member, ctx=interaction)
        if not can_proceed:
            await interaction.send(embed=message, ephemeral=True)
            return

        embed = nextcord.Embed(
            description=f"✅ Successfully kicked **{member.mention}**. \n\n<:note:1289880498541297685> **Reason:** {reason}\n<:salute:1287038901151862795> **Moderator:** {interaction.user}",
            color=config.EMBED_COLOR,
        )
        dm_embed = nextcord.Embed(
            description=f"You were banned in **{interaction.guild}**. \n\n<:note:1289880498541297685> **Reason:** {reason}", color=config.EMBED_COLOR
        )

        confirmation = oclib.ConfirmationView(ctx=interaction, member=member, action="kick", reason=reason)
        confirmed = await confirmation.prompt()
        if not confirmed:
            return
        try:
            await member.send(embed=dm_embed)
        except Exception:
            embed.set_footer(text="I was unable to DM this user.")
        await member.kick(reason=f"Kicked by {interaction.user} for: {reason}")
        await interaction.send(embed=embed)

        modlog_cog = self.bot.get_cog("ModLog")
        if modlog_cog:
            await modlog_cog.log_action("kick", member, reason, interaction.user)


def setup(bot):
    bot.add_cog(Kick(bot))
    bot.add_cog(KickSlash(bot))
