# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.models import StarboardMessageModel, StarboardSettingsModel
from takina.libs import lychecks, lyerrors, lyhelpers
from discord.ui import Button, View
from takina import config, database
from discord.ext import commands
from contextlib import suppress
import asyncio
import discord
import weakref


# discord's limit per message
MAX_EMBEDS = 10

type StarrableChannel = discord.TextChannel | discord.Thread


def is_public_source(
    channel: StarrableChannel,
    starboard_channel: discord.TextChannel,
    settings: StarboardSettingsModel,
) -> bool:
    if channel.is_nsfw() and not starboard_channel.is_nsfw():
        return False

    # threads are whitelisted through their parent channel
    channel_id = channel.parent_id if isinstance(channel, discord.Thread) else channel.id
    if settings.whitelisted_channel_ids:
        # whitelisting a channel opts it in, private or not
        return channel_id in settings.whitelisted_channel_ids

    if isinstance(channel, discord.Thread) and channel.is_private():
        return False

    return channel.permissions_for(channel.guild.default_role).read_messages


class Starboard(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot
        # one lock per starred message, so concurrent reactions cannot post it twice;
        # weak values drop each lock once no reaction is waiting on it
        self._locks: weakref.WeakValueDictionary[int, asyncio.Lock] = weakref.WeakValueDictionary()

    async def _get_settings(self, guild_id: int) -> StarboardSettingsModel | None:
        return await database.get(StarboardSettingsModel, guild_id=guild_id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await self._update_starboard(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        await self._update_starboard(payload)

    async def _update_starboard(self, payload: discord.RawReactionActionEvent) -> None:
        if not payload.guild_id or (guild := self._bot.get_guild(payload.guild_id)) is None:
            return

        settings = await self._get_settings(payload.guild_id)
        if not settings or not settings.starboard_channel_id:
            return

        starboard_channel = guild.get_channel(settings.starboard_channel_id)
        if not isinstance(starboard_channel, discord.TextChannel):
            return

        channel = guild.get_channel_or_thread(payload.channel_id)
        if not isinstance(channel, discord.TextChannel | discord.Thread):
            return

        if not is_public_source(channel, starboard_channel, settings):
            return

        lock = self._locks.get(payload.message_id)
        if lock is None:
            lock = self._locks[payload.message_id] = asyncio.Lock()

        async with lock:
            await self._sync_message(payload, channel, starboard_channel, settings)

    async def _sync_message(
        self,
        payload: discord.RawReactionActionEvent,
        channel: StarrableChannel,
        starboard_channel: discord.TextChannel,
        settings: StarboardSettingsModel,
    ) -> None:
        # discord.py keeps reactions current on cached messages, which saves a fetch per reaction
        message = discord.utils.get(self._bot.cached_messages, id=payload.message_id)
        if message is None:
            try:
                message = await channel.fetch_message(payload.message_id)
            except discord.NotFound:
                return

        if message.author.bot:
            return

        # any emoji counts, so judge by the most popular one rather than the one just changed
        reaction = max(message.reactions, key=lambda reaction: reaction.count, default=None)
        reaction_count = reaction.count if reaction else 0
        if reaction is not None and reaction_count >= settings.minimum_reaction_count:
            # starring your own message does not count; only worth asking once it could matter
            async for user in reaction.users():
                if user.id == message.author.id:
                    reaction_count -= 1
                    break

        existing = await database.get(StarboardMessageModel, message_id=message.id)

        if reaction is None or reaction_count < settings.minimum_reaction_count:
            if existing is None:
                return

            with suppress(discord.NotFound, discord.Forbidden):
                await starboard_channel.get_partial_message(existing.starboard_message_id).delete()

            await database.delete(existing)
            return

        embeds, view = self._create_embed(message, reaction, reaction_count)
        if existing is not None:
            try:
                await starboard_channel.get_partial_message(existing.starboard_message_id).edit(
                    embeds=embeds, view=view
                )
                return
            except discord.NotFound:
                # the starboard post was deleted by hand, so post it again
                await database.delete(existing)

        starboard_message = await starboard_channel.send(embeds=embeds, view=view)
        await database.save(
            StarboardMessageModel(message_id=message.id, starboard_message_id=starboard_message.id)
        )

    # permissions sit on each subcommand only, as slash never runs the group's checks, and the
    # moved ones need manage_guild where the whitelist needs manage_channels
    @commands.hybrid_group(
        name="starboard", description="Configure the starboard.", invoke_without_command=True
    )
    @lychecks.guild_only()
    async def starboard(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @starboard.command(
        name="settings", description="Moved to /settings guild starboard.", usage="#channel 4"
    )
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def starboard_settings(
        self, ctx: commands.Context, channel: discord.TextChannel, reaction_count: int
    ) -> None:
        await lyhelpers.invoke_moved(
            ctx, "settings guild starboard", channel=channel, reaction_count=reaction_count
        )

    @starboard.command(name="disable", description="Moved to /settings guild disable.")
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def starboard_disable(self, ctx: commands.Context) -> None:
        await lyhelpers.invoke_moved(ctx, "settings guild disable", feature="starboard")

    @starboard.group(
        name="whitelist",
        description="Manage starboard whitelisted channels.",
        invoke_without_command=True,
    )
    @lychecks.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def starboard_whitelist(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @starboard_whitelist.command(
        name="add",
        description="Add channels to the starboard whitelist.",
        usage="#channel #channel2",
    )
    @lychecks.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def whitelist_add(
        self, ctx: commands.Context, channels: commands.Greedy[discord.TextChannel]
    ) -> None:
        assert ctx.guild is not None

        if not channels:
            raise lyerrors.TakinaUserInputError("You must specify at least one text channel.")

        settings = await database.get_or_create(StarboardSettingsModel, guild_id=ctx.guild.id)

        added_channels = []
        for channel in channels:
            if channel.id not in settings.whitelisted_channel_ids:
                settings.whitelisted_channel_ids.append(channel.id)
                added_channels.append(channel.mention)

        if not added_channels:
            raise lyerrors.TakinaError("All specified channels are already whitelisted.")

        await database.save(settings)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = (
            f"{config.emojis.SUCCESS} Added to the whitelist: {', '.join(added_channels)}."
        )
        await ctx.reply(embed=embed, mention_author=False)

    @starboard_whitelist.command(
        name="remove",
        description="Remove channels from the starboard whitelist.",
        usage="#channel #channel2",
    )
    @lychecks.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def whitelist_remove(
        self, ctx: commands.Context, channels: commands.Greedy[discord.TextChannel]
    ) -> None:
        assert ctx.guild is not None

        if not channels:
            raise lyerrors.TakinaUserInputError("You must specify at least one text channel.")

        settings = await self._get_settings(ctx.guild.id)
        if settings is None or not settings.whitelisted_channel_ids:
            raise lyerrors.TakinaError("No channels are whitelisted.")

        removed_channels = []
        for channel in channels:
            if channel.id in settings.whitelisted_channel_ids:
                settings.whitelisted_channel_ids.remove(channel.id)
                removed_channels.append(channel.mention)

        if not removed_channels:
            raise lyerrors.TakinaError("None of the specified channels are whitelisted.")

        await database.save(settings)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = (
            f"{config.emojis.SUCCESS} Removed from the whitelist: {', '.join(removed_channels)}."
        )
        await ctx.reply(embed=embed, mention_author=False)

    @starboard_whitelist.command(
        name="list", description="List all starboard whitelisted channels."
    )
    @lychecks.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def whitelist_list(self, ctx: commands.Context) -> None:
        assert ctx.guild is not None

        settings = await self._get_settings(ctx.guild.id)
        if settings is None or not settings.whitelisted_channel_ids:
            raise lyerrors.TakinaError("No channels are whitelisted.")

        channels = [
            channel.mention
            for channel_id in settings.whitelisted_channel_ids
            if (channel := ctx.guild.get_channel(channel_id)) is not None
        ]

        if not channels:
            raise lyerrors.TakinaError("None of the whitelisted channels could be found.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.NOTE} **Whitelisted channels**: {', '.join(channels)}"
        await ctx.reply(embed=embed, mention_author=False)

    @staticmethod
    def _create_embed(
        message: discord.Message, reaction: discord.Reaction, reaction_count: int
    ) -> tuple[list[discord.Embed], View]:
        embed = discord.Embed(
            title="Starred Message", colour=config.EMBED_COLOUR, url=message.jump_url
        )
        embed.description = message.content or "*No text content*"
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url,
            url=f"https://discord.com/users/{message.author.id}",
        )

        embed.add_field(
            name=":star: Reactions",
            value=f"{reaction_count:,} {reaction.emoji} reaction{'s' if reaction_count > 1 else ''}",
            inline=True,
        )

        view = View()
        view.add_item(
            Button(style=discord.ButtonStyle.primary, label="Jump to Message", url=message.jump_url)
        )

        # images sharing the jump url show up as one gallery under the first embed
        image_urls = [
            attachment.url
            for attachment in message.attachments
            if attachment.content_type and attachment.content_type.startswith("image/")
        ]
        image_urls += [
            source.thumbnail.url or source.url
            for source in message.embeds
            if source.type in ("image", "gifv") and (source.thumbnail.url or source.url)
        ]
        image_urls += [sticker.url for sticker in message.stickers]

        embeds = [embed]
        for image_url in image_urls:
            if not embed.image.url:
                embed.set_image(url=image_url)
            else:
                image_embed = discord.Embed(colour=config.EMBED_COLOUR, url=message.jump_url)
                image_embed.set_image(url=image_url)
                embeds.append(image_embed)

        embeds += [source for source in message.embeds if source.type == "rich"]

        return embeds[:MAX_EMBEDS], view


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Starboard(bot))
