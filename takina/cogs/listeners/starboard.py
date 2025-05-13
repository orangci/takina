# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import nextcord
import config
from motor.motor_asyncio import AsyncIOMotorClient
from nextcord.ext import application_checks, commands
from nextcord.ui import Button, View


class Starboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(config.MONGO_URI).get_database(config.DB_NAME)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: nextcord.RawReactionActionEvent):
        # Fetch the guild info
        guild_id = payload.guild_id
        guild_data = await self.db.starboard_settings.find_one({"guild_id": guild_id})
        if not guild_data:
            return

        # Ensure the channel is whitelisted
        whitelisted_channels = guild_data.get("whitelisted_channels", [])
        if payload.channel_id not in whitelisted_channels:
            return

        # Fetch the starboard channel ID and ensure it exists
        starboard_channel_id = guild_data.get("starboard_channel_id")
        if not starboard_channel_id:
            return

        starboard_channel = self.bot.get_channel(starboard_channel_id)
        if not starboard_channel:
            return

        # Fetch the message details
        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
        message = await channel.fetch_message(payload.message_id)

        # Find the specific reaction the user added
        emoji_reaction = None
        for reaction in message.reactions:
            if str(reaction.emoji) == str(payload.emoji):
                emoji_reaction = reaction
                break

        # fetch the configured minimum reaction count
        minimum_reaction_count = guild_data.get("starboard_minimum_reaction_count")
        # Ensure the emoji reaction has at least the configured number of reactions
        if emoji_reaction and emoji_reaction.count >= minimum_reaction_count:
            # Check if this message is already on the starboard
            existing_star_message = await self.db.starboard.find_one({"message_id": message.id})

            if existing_star_message:
                # Update the starboard message if reactions reach 5 stars or more
                if emoji_reaction.count >= 5:
                    starboard_message_id = existing_star_message.get("starboard_message_id")
                    starboard_message = await starboard_channel.fetch_message(starboard_message_id)
                    if starboard_message:
                        updated_embed, view = self._create_embed(message, emoji_reaction)
                        await starboard_message.edit(embeds=updated_embed, view=view)
            else:
                # Create a new starboard entry
                embed, view = self._create_embed(message, emoji_reaction)
                starboard_message = await starboard_channel.send(embeds=embed, view=view)

                # Save the starboard message ID to the database
                await self.db.starboard.insert_one({"message_id": message.id, "starboard_message_id": starboard_message.id})

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: nextcord.RawReactionActionEvent):
        # When a reaction is removed, update the starboard message
        await self._update_starboard_message(payload)

    async def _update_starboard_message(self, payload: nextcord.RawReactionActionEvent):
        guild_id = payload.guild_id
        guild_data = await self.db.starboard_settings.find_one({"guild_id": guild_id})
        if not guild_data:
            return

        # Ensure the channel is whitelisted
        whitelisted_channels = guild_data.get("whitelisted_channels", [])
        if payload.channel_id not in whitelisted_channels:
            return

        # Fetch the starboard channel ID and ensure it exists
        starboard_channel_id = guild_data.get("starboard_channel_id")
        if not starboard_channel_id:
            return

        starboard_channel = self.bot.get_channel(starboard_channel_id)
        if not starboard_channel:
            return

        # Fetch the message details
        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
        message = await channel.fetch_message(payload.message_id)

        # Check if this message is already on the starboard
        existing_star_message = await self.db.starboard.find_one({"message_id": message.id})

        if not existing_star_message:
            return

        # Find the specific reaction
        emoji_reaction = None
        for reaction in message.reactions:
            if str(reaction.emoji) == str(payload.emoji):
                emoji_reaction = reaction
                break

        if emoji_reaction and emoji_reaction.count >= 5:
            # Fetch the starboard message and update it
            starboard_message_id = existing_star_message.get("starboard_message_id")
            starboard_message = await starboard_channel.fetch_message(starboard_message_id)
            if starboard_message:
                updated_embed, view = self._create_embed(message, emoji_reaction)
                await starboard_message.edit(embeds=updated_embed, view=view)

    @nextcord.slash_command(name="starboard", description="Manage the starboard settings")
    @application_checks.has_permissions(manage_channels=True)
    async def starboard_configure(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = nextcord.SlashOption(
            description="The channel in which you want the bot to send starboard messages in.", required=True
        ),
        reaction_count: int = nextcord.SlashOption(
            description="The minimum required amount of reactions a message needs to be sent to the starboard in your server.", required=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)

        guild_data = await self.db.starboard_settings.find_one({"guild_id": interaction.guild_id})
        if not guild_data:
            guild_data = {"guild_id": interaction.guild_id, "starboard_channel_id": None, "starboard_minimum_reaction_count": 4}

        guild_data["starboard_channel_id"] = channel.id
        guild_data["starboard_minimum_reaction_count"] = reaction_count
        await self.db.starboard_settings.update_one({"guild_id": interaction.guild_id}, {"$set": guild_data}, upsert=True)
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed.description = f"✅ Starboard channel has been set to {channel.mention} and set the minimum reaction count to **{reaction_count}**."
        await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.group(
        name="starboard", invoke_without_command=True, help="Starboard management. Use subcommands: `whitelist`, `list`, `add`, `remove`."
    )
    @commands.has_permissions(manage_channels=True)
    async def starboard(self, ctx: commands.Context):
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed.description = "Please specify a subcommand: `whitelist add`, `whitelist remove`, or `whitelist list`."
        await ctx.reply(embed=embed, mention_author=False)

    @starboard.group(name="whitelist", invoke_without_command=True)
    async def whitelist(self, ctx: commands.Context):
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed.description = "Please specify `add`, `remove`, or `list`."
        await ctx.reply(embed=embed, mention_author=False)

    @whitelist.command(
        name="add", help="Add channels to the list of whitelisted channels which the starboard detects messages from.", usage="channel #channel2"
    )
    async def whitelist_add(self, ctx: commands.Context, *channels: nextcord.TextChannel):
        guild_id = ctx.guild.id
        guild_data = await self.db.starboard_settings.find_one({"guild_id": guild_id})

        if not guild_data:
            guild_data = {"guild_id": guild_id, "whitelisted_channels": []}

        whitelisted_channels = guild_data.get("whitelisted_channels", [])

        added_channels = []
        for channel in channels:
            if channel.id not in whitelisted_channels:
                whitelisted_channels.append(channel.id)
                added_channels.append(channel.mention)

        await self.db.starboard_settings.update_one({"guild_id": guild_id}, {"$set": {"whitelisted_channels": whitelisted_channels}}, upsert=True)
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        if channels:
            embed.description = f"Added to the whitelist: {', '.join(added_channels)}."
        else:
            embed.description = (
                f"You must specify at least one text channel to use this command. Example usage: `starboard whitelist add #{ctx.channel.name}`."
            )
        await ctx.reply(embed=embed, mention_author=False)

    @whitelist.command(
        name="remove",
        help="Remove channels from the list of whitelisted channels which the starboard detects messages from.",
        usage="#channel #channel2",
    )
    async def whitelist_remove(self, ctx: commands.Context, *channels: nextcord.TextChannel):
        guild_id = ctx.guild.id
        guild_data = await self.db.starboard_settings.find_one({"guild_id": guild_id})

        if not guild_data:
            embed = nextcord.Embed(color=config.ERROR_COLOR)
            embed.description = "❌ No channels are whitelisted."
            await ctx.reply(embed=embed, mention_author=False)
            return

        whitelisted_channels = guild_data.get("whitelisted_channels", [])

        removed_channels = []
        for channel in channels:
            if channel.id in whitelisted_channels:
                whitelisted_channels.remove(channel.id)
                removed_channels.append(channel.mention)

        await self.db.starboard_settings.update_one({"guild_id": guild_id}, {"$set": {"whitelisted_channels": whitelisted_channels}}, upsert=True)
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        if channels:
            embed.description = f"Removed from the whitelist: {', '.join(removed_channels)}."
        else:
            embed.description = (
                f"You must specify at least one text channel to use this command. Example usage: `starboard whitelist remove #{ctx.channel.name}`."
            )
        await ctx.reply(embed=embed, mention_author=False)

    @whitelist.command(name="list", help="List all channels in the starboard whitelist.")
    async def whitelist_list(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        guild_data = await self.db.starboard_settings.find_one({"guild_id": guild_id})

        if not guild_data or not guild_data.get("whitelisted_channels"):
            embed = nextcord.Embed(color=config.ERROR_COLOR)
            embed.description = "❌ No channels are whitelisted."
            await ctx.reply(embed=embed, mention_author=False)
            return

        whitelisted_channels = guild_data.get("whitelisted_channels", [])
        channels_list = [ctx.guild.get_channel(ch_id).mention for ch_id in whitelisted_channels if ctx.guild.get_channel(ch_id)]

        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed.description = f"Whitelisted channels: {', '.join(channels_list)}."
        await ctx.reply(embed=embed, mention_author=False)

    def _create_embed(self, message: nextcord.Message, reaction: nextcord.Reaction):
        """Helper function to create the starboard embed."""

        embed = nextcord.Embed(
            title="Starred Message", description=message.content if message.content else "*No text content*\n", color=config.EMBED_COLOR
        )

        embed.set_author(name=message.author.name, icon_url=message.author.avatar.url, url=f"https://discord.com/users/{message.author.id}")

        embed.add_field(name=":sparkles: Reactions", value=f"{reaction.count} {reaction.emoji} reactions", inline=True)

        view = View()
        button = Button(style=nextcord.ButtonStyle.primary, label="Jump to Message", url=message.jump_url)
        view.add_item(button)

        embed.url = message.jump_url
        embed_list = [embed]

        if message.attachments:
            for attachment in message.attachments:
                if "image" in str(attachment.content_type):
                    if not embed.image:
                        embed.set_image(url=attachment.url)
                    else:
                        new_embed = nextcord.Embed(color=config.EMBED_COLOR, url=message.jump_url)
                        new_embed.set_image(url=attachment.url)
                        embed_list.append(new_embed)
        return embed_list, view


def setup(bot: commands.Bot):
    bot.add_cog(Starboard(bot))
