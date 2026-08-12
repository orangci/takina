from takina.models import StarboardMessageModel, StarboardSettingsModel
from takina.libs import lychecks, lyerrors
from discord.ui import Button, View
from takina import config, database
from discord.ext import commands
import discord


class Starboard(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    async def _get_settings(self, guild_id: int) -> StarboardSettingsModel | None:
        return await database.get(StarboardSettingsModel, guild_id=guild_id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await self._update_starboard(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        await self._update_starboard(payload)

    async def _update_starboard(self, payload: discord.RawReactionActionEvent) -> None:
        if not payload.guild_id:
            return

        settings = await self._get_settings(payload.guild_id)
        if not settings or not settings.starboard_channel_id:
            return

        # checks if the message is in the whitelist
        # but only if there IS a whitelist
        if (
            settings.whitelisted_channel_ids
            and payload.channel_id not in settings.whitelisted_channel_ids
        ):
            return

        starboard_channel = self._bot.get_channel(settings.starboard_channel_id)
        if not isinstance(starboard_channel, discord.TextChannel):
            return

        channel = self._bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        reaction = next(
            (
                reaction
                for reaction in message.reactions
                if str(reaction.emoji) == str(payload.emoji)
            ),
            None,
        )

        reaction_count = reaction.count if reaction else 0
        existing = await database.get(StarboardMessageModel, message_id=message.id)

        if reaction_count < settings.minimum_reaction_count:
            if existing is None:
                return

            try:
                starboard_message = await starboard_channel.fetch_message(
                    existing.starboard_message_id
                )
            except discord.NotFound:
                starboard_message = None

            if starboard_message is not None:
                await starboard_message.delete()

            await database.delete(existing)
            return

        if reaction is None:
            return

        embeds, view = self._create_embed(message, reaction)
        if existing is not None:
            try:
                starboard_message = await starboard_channel.fetch_message(
                    existing.starboard_message_id
                )
            except discord.NotFound:
                starboard_message = None

            if starboard_message is None:
                await database.delete(existing)
            else:
                await starboard_message.edit(embeds=embeds, view=view)
                return

        starboard_message = await starboard_channel.send(embeds=embeds, view=view)
        await database.save(
            StarboardMessageModel(message_id=message.id, starboard_message_id=starboard_message.id)
        )

    @commands.hybrid_group(
        name="starboard", description="Configure the starboard.", invoke_without_command=True
    )
    @lychecks.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def starboard(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @starboard.command(
        name="settings",
        description="Configure the starboard channel and reaction threshold.",
        usage="#channel 4",
    )
    async def starboard_settings(
        self, ctx: commands.Context, channel: discord.TextChannel, reaction_count: int
    ) -> None:
        assert ctx.guild is not None

        if reaction_count < 1:
            raise lyerrors.TakinaUserInputError("The minimum reaction count must be at least 1.")

        settings = await self._get_settings(ctx.guild.id)
        if settings is None:
            settings = StarboardSettingsModel(
                guild_id=ctx.guild.id,
                starboard_channel_id=channel.id,
                minimum_reaction_count=reaction_count,
            )
        else:
            settings.starboard_channel_id = channel.id
            settings.minimum_reaction_count = reaction_count
        await database.save(settings)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = (
            f"{config.emojis.SUCCESS} Starboard channel has been set to {channel.mention}."
        )
        embed.description += f"\n{config.emojis.NOTE} **Minimum reactions**: {reaction_count:,}"
        await ctx.send(embed=embed)

    @starboard.group(
        name="whitelist",
        description="Manage starboard whitelisted channels.",
        invoke_without_command=True,
    )
    async def starboard_whitelist(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @starboard_whitelist.command(
        name="add",
        description="Add channels to the starboard whitelist.",
        usage="#channel #channel2",
    )
    async def whitelist_add(
        self, ctx: commands.Context, channels: commands.Greedy[discord.TextChannel]
    ) -> None:
        assert ctx.guild is not None

        if not channels:
            raise lyerrors.TakinaUserInputError("You must specify at least one text channel.")

        settings = await self._get_settings(ctx.guild.id)
        if settings is None:
            settings = StarboardSettingsModel(guild_id=ctx.guild.id)

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
        message: discord.Message, reaction: discord.Reaction
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
            value=f"{reaction.count:,} {reaction.emoji} reaction{'s' if reaction.count > 1 else ''}",
            inline=True,
        )

        view = View()
        view.add_item(
            Button(style=discord.ButtonStyle.primary, label="Jump to Message", url=message.jump_url)
        )

        embeds = [embed]
        for attachment in message.attachments:
            if not attachment.content_type or not attachment.content_type.startswith("image/"):
                continue

            if not embed.image.url:
                embed.set_image(url=attachment.url)
            else:
                attachment_embed = discord.Embed(colour=config.EMBED_COLOUR, url=message.jump_url)
                attachment_embed.set_image(url=attachment.url)
                embeds.append(attachment_embed)

        return embeds, view


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Starboard(bot))
