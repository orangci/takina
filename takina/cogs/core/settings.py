# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.models import GuildSettingsModel, StarboardSettingsModel
from takina.libs import lychecks, lyerrors
from takina import config, database
from discord.ext import commands
from typing import Literal
import discord

Feature = Literal["modlog", "honeypot", "reports", "starboard"]

FEATURE_NAMES: dict[str, str] = {
    "modlog": "The modlog",
    "honeypot": "The honeypot",
    "reports": "Reports",
    "starboard": "The starboard",
}


def channel_mention(channel_id: int | None) -> str:
    return f"<#{channel_id}>" if channel_id else "Not set"


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def reply(self, ctx: commands.Context, description: str) -> None:
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} {description}"
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_group(
        name="settings", description="Configure Takina.", invoke_without_command=True
    )
    async def settings(self, ctx: commands.Context):
        await ctx.send_help(ctx.command)

    # every subcommand repeats its checks, as slash subcommands never run the group's own
    @settings.group(
        name="guild",
        aliases=["server"],
        description="Show or change this server's settings.",
        invoke_without_command=True,
    )
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def guild_settings(self, ctx: commands.Context):
        await self.show_guild_settings(ctx)

    # slash cannot invoke a group itself, so the overview needs its own subcommand there
    @guild_settings.command(name="show", description="Show this server's settings.")
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def show(self, ctx: commands.Context):
        await self.show_guild_settings(ctx)

    async def show_guild_settings(self, ctx: commands.Context) -> None:
        assert ctx.guild is not None

        settings = await database.get(GuildSettingsModel, guild_id=ctx.guild.id)
        settings = settings or GuildSettingsModel(guild_id=ctx.guild.id)
        starboard = await database.get(StarboardSettingsModel, guild_id=ctx.guild.id)

        reports = channel_mention(settings.reports_channel_id)
        if settings.reports_channel_id and settings.reports_notification_role_id:
            reports += f", pings <@&{settings.reports_notification_role_id}>"

        if starboard and starboard.starboard_channel_id:
            starboard_text = f"<#{starboard.starboard_channel_id}>, {starboard.minimum_reaction_count:,} reactions"
        else:
            starboard_text = "Not set"

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.NOTE} Settings for **{ctx.guild.name}**\n"
        embed.description += (
            f"\n> **Modlog channel**: {channel_mention(settings.modlog_channel_id)}"
        )
        embed.description += (
            f"\n> **Honeypot channel**: {channel_mention(settings.honeypot_channel_id)}"
        )
        embed.description += f"\n> **Reports channel**: {reports}"
        embed.description += f"\n> **Starboard**: {starboard_text}"
        embed.description += (
            f"\n> **GitHub previews**: {'On' if settings.github_previews else 'Off'}"
        )
        await ctx.reply(embed=embed, mention_author=False)

    @guild_settings.command(
        name="modlog-channel",
        description="Set the channel where moderation actions are logged.",
        usage="#mod-log",
    )
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def modlog_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        assert ctx.guild is not None

        settings = await database.get_or_create(GuildSettingsModel, guild_id=ctx.guild.id)
        settings.modlog_channel_id = channel.id
        await database.save(settings)

        await self.reply(ctx, f"Modlog channel has been set to {channel.mention}.")

    @guild_settings.command(
        name="honeypot",
        description="Mute anyone who posts in this channel, and clear their recent messages.",
        usage="#free-nitro",
    )
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def honeypot(self, ctx: commands.Context, channel: discord.TextChannel):
        assert ctx.guild is not None

        settings = await database.get_or_create(GuildSettingsModel, guild_id=ctx.guild.id)
        settings.honeypot_channel_id = channel.id
        await database.save(settings)

        await self.reply(
            ctx,
            f"Honeypot channel has been set to {channel.mention}. Please remember to give me permissions to manage messages and to timeout members.",
        )

    @guild_settings.command(
        name="reports",
        description="Set the channel where reports are sent, and optionally a role to ping.",
        usage="#reports @Moderators",
    )
    @lychecks.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def reports(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        notification_role: discord.Role | None = None,
    ):
        assert ctx.guild is not None

        settings = await database.get_or_create(GuildSettingsModel, guild_id=ctx.guild.id)
        settings.reports_channel_id = channel.id
        if notification_role is not None:
            settings.reports_notification_role_id = notification_role.id
        await database.save(settings)

        await self.reply(ctx, f"Successfully set the reports channel to {channel.mention}.")

    @guild_settings.command(
        name="starboard",
        description="Set the starboard channel and how many reactions a message needs.",
        usage="#starboard 4",
    )
    @lychecks.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def starboard(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        reaction_count: commands.Range[int, 1],
    ):
        assert ctx.guild is not None

        settings = await database.get_or_create(StarboardSettingsModel, guild_id=ctx.guild.id)
        settings.starboard_channel_id = channel.id
        settings.minimum_reaction_count = reaction_count
        await database.save(settings)

        await self.reply(
            ctx,
            f"Starboard channel has been set to {channel.mention}.\n{config.emojis.NOTE} **Minimum reactions**: {reaction_count:,}",
        )

    @guild_settings.command(
        name="github-previews",
        description="Preview GitHub repositories, issues and pull requests mentioned in chat.",
        usage="False",
    )
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def github_previews(self, ctx: commands.Context, enabled: bool):
        assert ctx.guild is not None

        settings = await database.get_or_create(GuildSettingsModel, guild_id=ctx.guild.id)
        settings.github_previews = enabled
        await database.save(settings)

        await self.reply(ctx, f"GitHub previews are now {'on' if enabled else 'off'}.")

    @guild_settings.command(name="disable", description="Turn a feature off.", usage="honeypot")
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def disable(self, ctx: commands.Context, feature: Feature):
        assert ctx.guild is not None

        if feature == "starboard":
            starboard = await database.get(StarboardSettingsModel, guild_id=ctx.guild.id)
            if starboard is None or starboard.starboard_channel_id is None:
                raise lyerrors.TakinaError("The starboard is not set up in this server.")

            # the threshold and whitelist stay, so setting it up again picks them back up
            starboard.starboard_channel_id = None
            await database.save(starboard)
        else:
            column = f"{feature}_channel_id"
            settings = await database.get(GuildSettingsModel, guild_id=ctx.guild.id)
            if settings is None or getattr(settings, column) is None:
                raise lyerrors.TakinaError(
                    f"{FEATURE_NAMES[feature]} is not set up in this server."
                )

            setattr(settings, column, None)
            await database.save(settings)

        await self.reply(ctx, f"{FEATURE_NAMES[feature]} has been disabled.")

    @settings.command(name="user", description="Manage user settings.")
    @lychecks.is_user_app()
    async def user_settings(self, ctx: commands.Context):
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.NOTE} User settings are not available yet. Stay tuned!"
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot))
