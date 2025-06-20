# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import application_checks, commands
from ..libs import oclib
import nextcord
import config


class Ban(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ban", aliases=["b"], help="Ban a member from the server.", usage="@member")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: str = None, *, reason: str = "No reason provided"):
        if not member:
            raise commands.UserInputError

        member = oclib.extract_user_id(member, ctx)
        if isinstance(member, nextcord.Embed):
            await ctx.reply(embed=member, mention_author=False)
            return

        can_proceed, message = oclib.perms_check(member, ctx=ctx)
        if not can_proceed:
            await ctx.reply(embed=message, mention_author=False)
            return

        embed = nextcord.Embed(
            description=f"✅ Successfully banned **{member.mention}**. \n\n<:note:1289880498541297685> **Reason:** {reason}\n<:salute:1287038901151862795> **Moderator:** {ctx.author}",
            color=config.EMBED_COLOR,
        )
        dm_embed = nextcord.Embed(
            description=f"You were banned in **{ctx.guild}**. \n\n<:note:1289880498541297685> **Reason:** {reason}", color=config.EMBED_COLOR
        )
        confirmation = oclib.ConfirmationView(ctx=ctx, member=member, action="ban", reason=reason)
        confirmed = await confirmation.prompt()
        if not confirmed:
            return
        try:
            await member.send(embed=dm_embed)
        except Exception:
            embed.set_footer(text="I was unable to DM this user.")
        await member.ban(reason=f"Banned by {ctx.author} for: {reason}")
        await ctx.reply(embed=embed, mention_author=False)

        modlog_cog = self.bot.get_cog("ModLog")
        if modlog_cog:
            await modlog_cog.log_action("ban", member, reason, ctx.author)


class Unban(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="unban", aliases=["pardon", "ub"], help="Unban a member from the server.")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, id: str, *, reason: str = "No reason provided"):
        try:
            id = int(id)
        except Exception:
            embed = nextcord.Embed(color=config.ERROR_COLOR)
            embed.description = ":x: Please provide a valid Discord user ID."
            await ctx.reply(embed=embed, mention_author=False)
            return
        user = await self.bot.fetch_user(int(id)) or await self.bot.fetch_user(id)
        try:
            await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author} for: {reason}")
        except Exception:
            error_embed = nextcord.Embed(description=f":x: **{user.mention}** is not banned.", color=config.ERROR_COLOR)
            await ctx.reply(embed=error_embed, mention_author=False)
            return

        embed = nextcord.Embed(
            description=f"✅ Successfully unbanned **{user.mention}**. \n\n<:note:1289880498541297685> **Reason:** {reason}\n<:salute:1287038901151862795> **Moderator:** {ctx.author}",
            color=config.EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)
        modlog_cog = self.bot.get_cog("ModLog")
        if modlog_cog:
            await modlog_cog.log_action("unban", user, reason, ctx.author, ctx=ctx)

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            error_embed = nextcord.Embed(description=":x: User not found. Please make sure the User ID is correct.", color=config.ERROR_COLOR)
            await ctx.reply(embed=error_embed, mention_author=False)


class BanSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="ban", description="Ban a member from the server.")
    @application_checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(description="The member to ban", required=True),
        reason: str = "No reason provided",
    ):
        await interaction.response.defer()
        can_proceed, message = oclib.perms_check(member, ctx=interaction)
        if not can_proceed:
            await interaction.send(embed=message, ephemeral=True)
            return

        embed = nextcord.Embed(
            description=f"✅ Successfully banned **{member.mention}**. \n\n<:note:1289880498541297685> **Reason:** {reason}\n<:salute:1287038901151862795> **Moderator:** {interaction.user}",
            color=config.EMBED_COLOR,
        )
        dm_embed = nextcord.Embed(
            description=f"You were banned in **{interaction.guild}**. \n\n<:note:1289880498541297685> **Reason:** {reason}", color=config.EMBED_COLOR
        )
        confirmation = oclib.ConfirmationView(ctx=interaction, member=member, action="ban", reason=reason)
        confirmed = await confirmation.prompt()
        if not confirmed:
            return
        try:
            await member.send(embed=dm_embed)
        except Exception:
            embed.set_footer(text="I was unable to DM this user.")
        await member.ban(reason=f"Banned by {interaction.user} for: {reason}")
        await interaction.send(embed=embed)

        modlog_cog = self.bot.get_cog("ModLog")
        if modlog_cog:
            await modlog_cog.log_action("ban", member, reason, interaction.user)


class UnbanSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="unban", description="Unban a member from the server.")
    @application_checks.has_permissions(ban_members=True)
    async def unban(
        self,
        interaction: nextcord.Interaction,
        id: str = nextcord.SlashOption(description="The user ID to unban", required=True),
        reason: str = "No reason provided",
    ):
        await interaction.response.defer()
        try:
            id = int(id)
        except Exception:
            embed = nextcord.Embed(color=config.ERROR_COLOR)
            embed.description = ":x: Please provide a valid Discord user ID."
            await interaction.send(embed=embed, ephemeral=True)
            return
        user = await self.bot.fetch_user(int(id)) or await self.bot.fetch_user(id)
        try:
            await interaction.guild.unban(user, reason=f"Unbanned by {interaction.user} for: {reason}")
        except Exception:
            error_embed = nextcord.Embed(description=f":x: **{user.mention}** is not banned.", color=config.ERROR_COLOR)
            await interaction.send(embed=error_embed, ephemeral=True)
            return

        embed = nextcord.Embed(
            description=f"✅ Successfully unbanned **{user.mention}**. \n\n<:note:1289880498541297685> **Reason:** {reason}\n<:salute:1287038901151862795> **Moderator:** {interaction.user}",
            color=config.EMBED_COLOR,
        )
        await interaction.send(embed=embed)
        modlog_cog = self.bot.get_cog("ModLog")
        if modlog_cog:
            await modlog_cog.log_action("unban", user, reason, interaction.user, ctx=interaction)


def setup(bot):
    bot.add_cog(Ban(bot))
    bot.add_cog(BanSlash(bot))
    bot.add_cog(Unban(bot))
    bot.add_cog(UnbanSlash(bot))
