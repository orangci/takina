# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers, lymodlog
from takina.models import GuildSettingsModel
from takina import config, database
from collections import defaultdict
from discord.ext import commands
from datetime import timedelta
import logging
import discord

logger = logging.getLogger("takina.honeypot")

HONEYPOT_TIMEOUT = timedelta(weeks=4)
# how far back the member's messages are cleared
PURGE_WINDOW = timedelta(minutes=10)

type PurgeableChannel = discord.TextChannel | discord.Thread | discord.VoiceChannel


class Honeypot(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    async def delete_recent_messages(self, member: discord.Member) -> None:
        # the message cache instead of every channel's history, so big servers stay quick
        cutoff = discord.utils.utcnow() - PURGE_WINDOW
        by_channel: defaultdict[PurgeableChannel, list[discord.Message]] = defaultdict(list)

        for message in self._bot.cached_messages:
            if (
                message.author.id == member.id
                and message.guild == member.guild
                and message.created_at >= cutoff
                and isinstance(
                    message.channel, discord.TextChannel | discord.Thread | discord.VoiceChannel
                )
            ):
                by_channel[message.channel].append(message)

        for channel, messages in by_channel.items():
            for chunk in lyhelpers.chunked(messages, 100):
                try:
                    await channel.delete_messages(chunk, reason="Honeypot triggered.")
                except discord.HTTPException as error:
                    logger.warning(f"honeypot could not purge {channel.id}: {error}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        settings = await database.get(GuildSettingsModel, guild_id=message.guild.id)
        if not settings or not settings.honeypot_channel_id:
            return

        if message.channel.id != settings.honeypot_channel_id:
            return

        member = message.author
        if not isinstance(member, discord.Member):
            return

        reason = "Muted for triggering the honeypot system."
        try:
            await member.timeout(HONEYPOT_TIMEOUT, reason=reason)
        except discord.Forbidden:
            # admins and members above the bot, often staff testing the honeypot
            logger.warning(f"honeypot could not timeout {member.id} in {message.guild.id}")
            return

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"You were muted in **{message.guild.name}** for 4 weeks."
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: You have been automatically muted by the honeypot system."

        try:
            await member.send(embed=embed)
        except discord.HTTPException:
            pass

        await self.delete_recent_messages(member)

        if moderator := self._bot.user:
            await lymodlog.log_action(message.guild, "mute", [member], reason, moderator, "4w")

    @commands.hybrid_group(
        name="honeypot", description="Configure the honeypot channel.", invoke_without_command=True
    )
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def honeypot(self, ctx: commands.Context) -> None:
        await ctx.send_help(ctx.command)

    @honeypot.command(
        name="set",
        description="Mute anyone who posts in this channel, and clear their recent messages.",
        usage="#channel",
    )
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def honeypot_set(self, ctx: commands.Context, channel: discord.TextChannel) -> None:
        assert ctx.guild is not None

        settings = await database.get_or_create(GuildSettingsModel, guild_id=ctx.guild.id)
        settings.honeypot_channel_id = channel.id
        await database.save(settings)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Honeypot channel has been set to {channel.mention}. Please remember to give me permissions to manage messages and to timeout members."

        await ctx.reply(embed=embed, mention_author=False)

    @honeypot.command(name="disable", description="Turn the honeypot off.")
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def honeypot_disable(self, ctx: commands.Context) -> None:
        assert ctx.guild is not None

        settings = await database.get(GuildSettingsModel, guild_id=ctx.guild.id)
        if settings is None or settings.honeypot_channel_id is None:
            raise lyerrors.TakinaError("The honeypot is not set up in this server.")

        settings.honeypot_channel_id = None
        await database.save(settings)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} The honeypot has been disabled."

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Honeypot(bot))
