# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyhelpers, lymodlog
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
# discord takes at most ten files per message
MAX_EVIDENCE_FILES = 10

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

    async def fetch_evidence_files(self, message: discord.Message) -> list[discord.File]:
        # attachment urls die with the message, so the files are fetched before the purge
        assert message.guild is not None
        budget = message.guild.filesize_limit
        files: list[discord.File] = []

        for attachment in message.attachments[:MAX_EVIDENCE_FILES]:
            if attachment.size > budget:
                continue

            try:
                # spoilered, as honeypot catches are often scams or worse
                files.append(await attachment.to_file(spoiler=True))
            except discord.HTTPException as error:
                logger.warning(f"honeypot could not fetch attachment {attachment.id}: {error}")
                continue

            budget -= attachment.size

        return files

    async def post_evidence(
        self, log_message: discord.Message, message: discord.Message, files: list[discord.File]
    ) -> None:
        content = discord.utils.escape_markdown(message.content) or "*No text.*"
        skipped = len(message.attachments) - len(files)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        embed.description = lyhelpers.truncate(
            f"{config.emojis.NOTE} **Caught message** in {message.channel.mention}:\n{content}",
            4096,
        )
        if skipped:
            embed.set_footer(text=f"{skipped} attachment(s) could not be kept.")

        try:
            await log_message.reply(embed=embed, files=files, mention_author=False)
        except discord.HTTPException as error:
            logger.warning(f"honeypot could not post evidence in {log_message.channel.id}: {error}")

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

        files = await self.fetch_evidence_files(message)
        await self.delete_recent_messages(member)

        if not (moderator := self._bot.user):
            return

        log_message = await lymodlog.log_action(
            message.guild, "mute", [member], reason, moderator, "4w"
        )
        if log_message is not None:
            await self.post_evidence(log_message, message, files)

    @commands.hybrid_group(
        name="honeypot", description="Configure the honeypot channel.", invoke_without_command=True
    )
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def honeypot(self, ctx: commands.Context) -> None:
        await ctx.send_help(ctx.command)

    @honeypot.command(
        name="set", description="Moved to /settings guild honeypot.", usage="#channel"
    )
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def honeypot_set(self, ctx: commands.Context, channel: discord.TextChannel) -> None:
        await lyhelpers.invoke_moved(ctx, "settings guild honeypot", channel=channel)

    @honeypot.command(name="disable", description="Moved to /settings guild disable.")
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def honeypot_disable(self, ctx: commands.Context) -> None:
        await lyhelpers.invoke_moved(ctx, "settings guild disable", feature="honeypot")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Honeypot(bot))
