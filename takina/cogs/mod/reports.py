# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors, lychecks, lyhelpers, lymodlog
from takina.models import GuildSettingsModel
from takina import config, database
from discord.ext import commands
import discord


class Reports(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_group(
        name="report",
        description="Report something to the server's moderation team.",
        invoke_without_command=True,
    )
    @lychecks.guild_only()
    async def report(self, ctx: commands.Context) -> None:
        await ctx.send_help(ctx.command)

    @report.command(
        name="channel", description="Moved to /settings guild reports.", usage="#channel"
    )
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def report_channel(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        notification_role: discord.Role | None = None,
    ) -> None:
        await lyhelpers.invoke_moved(
            ctx, "settings guild reports", channel=channel, notification_role=notification_role
        )

    @report.command(
        name="member",
        description="Report a member to the server's moderation team.",
        usage="@member reason",
    )
    @lychecks.guild_only()
    @lychecks.slash_only()
    @lychecks.cooldown(1, 60)
    async def report_member(
        self, ctx: commands.Context, member: discord.Member, *, reason: lymodlog.Reason
    ) -> None:
        assert ctx.guild is not None

        if member == ctx.author:
            raise lyerrors.TakinaUserInputError("You cannot report yourself.")

        settings = await database.get(GuildSettingsModel, guild_id=ctx.guild.id)
        if settings is None or not settings.reports_channel_id:
            raise lyerrors.TakinaError(
                "The reports system has not been configured for this server. Ask an administrator to run `/settings guild reports`."
            )

        reports_channel = self._bot.get_channel(settings.reports_channel_id)
        if not isinstance(reports_channel, discord.TextChannel):
            raise lyerrors.TakinaError("The configured reports channel could not be found.")

        embed = discord.Embed(title="New Report", colour=config.EMBED_COLOUR)
        embed.description = (
            f"A new report has been submitted about {member.mention} by {ctx.author.mention}."
        )
        embed.add_field(name=f"{config.emojis.NOTE} Reason", value=reason, inline=True)
        embed.add_field(name="👤 Subject", value=member.mention, inline=True)
        embed.add_field(name="📍 Channel", value=ctx.channel.jump_url, inline=True)
        embed.set_footer(text=f"Reported by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        role_id = settings.reports_notification_role_id
        await reports_channel.send(
            f"<@&{role_id}>" if role_id else None,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=False, roles=[discord.Object(role_id)] if role_id else False
            ),
        )
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Report successfully submitted."
        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reports(bot))
