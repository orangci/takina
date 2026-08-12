from takina.models import GuildSettingsModel
from takina.libs import lyerrors, lychecks
from takina import config, database
from discord.ext import commands
import discord


class Reports(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_group(
        name="report", description="Report something to the server's moderation team."
    )
    @lychecks.guild_only()
    async def report(self, ctx: commands.Context) -> None:
        pass

    @report.command(
        name="channel", description="Set the channel where reports will be sent.", usage="#channel"
    )
    @commands.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def report_channel(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        notification_role: discord.Role | None = None,
    ) -> None:
        assert ctx.guild is not None

        settings = await database.get(GuildSettingsModel, guild_id=ctx.guild.id)
        if not settings:
            settings = GuildSettingsModel(
                guild_id=ctx.guild.id,
                reports_channel_id=channel.id,
                reports_notification_role_id=notification_role.id if notification_role else None,
            )
        else:
            settings.reports_channel_id = channel.id
        await database.save(settings)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = (
            f"{config.emojis.SUCCESS} Successfully set the reports channel to {channel.mention}."
        )
        await ctx.send(embed=embed, ephemeral=True)

    @report.command(
        name="member",
        description="Report a member to the server's moderation team.",
        usage="@member reason",
    )
    @lychecks.guild_only()
    async def report_member(
        self, ctx: commands.Context, member: discord.Member, *, reason: str
    ) -> None:
        assert ctx.guild is not None

        settings = await database.get(GuildSettingsModel, guild_id=ctx.guild.id)
        if settings is None or not settings.reports_channel_id:
            raise lyerrors.TakinaError(
                "The reports system has not been configured for this server. Ask an administrator to run `/report channel`."
            )

        reports_channel = self._bot.get_channel(settings.reports_channel_id)
        if not isinstance(reports_channel, discord.TextChannel):
            raise lyerrors.TakinaError("The configured reports channel could not be found.")

        incident_channel = ctx.channel
        if not isinstance(incident_channel, discord.TextChannel):
            raise lyerrors.TakinaError("The incident channel could not be determined.")

        embed = discord.Embed(title="New Report", colour=config.EMBED_COLOUR)
        embed.description = (
            f"A new report has been submitted about {member.mention} by {ctx.author.mention}."
        )
        embed.add_field(name=f"{config.emojis.NOTE} Reason", value=reason, inline=True)
        embed.add_field(name="👤 Subject", value=member.mention, inline=True)
        embed.set_footer(text=f"Reported by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        await reports_channel.send(
            f"<@&{settings.reports_notification_role_id}>",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Report successfully submitted."
        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reports(bot))
