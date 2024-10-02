import nextcord
from nextcord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
from nextcord import SlashOption
from __main__ import DB_NAME, EMBED_COLOR


class Starboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(os.getenv("MONGO")).get_database(DB_NAME)

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

        # Ensure the emoji reaction has at least 4 reactions
        if emoji_reaction and emoji_reaction.count >= 4:
            # Check if this message is already on the starboard
            existing_star_message = await self.db.starboard.find_one(
                {"message_id": message.id}
            )

            if existing_star_message:
                # Do not send the message again if it already exists on the starboard
                return
            else:
                # Create a new starboard entry
                embed = self._create_embed(message, emoji_reaction)
                starboard_message = await starboard_channel.send(embed=embed)

                # Save the starboard message ID to the database
                await self.db.starboard.insert_one(
                    {
                        "message_id": message.id,
                        "starboard_message_id": starboard_message.id,
                    }
                )

    @nextcord.slash_command(description="Manage the starboard settings")
    async def starboard(self, interaction: nextcord.Interaction):
        pass

    @starboard.subcommand(description="Whitelist a channel for starboard tracking")
    async def whitelist(
        self, interaction: nextcord.Interaction, channel: nextcord.TextChannel
    ):
        guild_id = interaction.guild_id

        # Get the current settings or create a new entry
        guild_data = await self.db.starboard_settings.find_one({"guild_id": guild_id})
        if not guild_data:
            guild_data = {
                "guild_id": guild_id,
                "whitelisted_channels": [],
                "starboard_channel_id": None,
            }

        # Add the channel to the whitelist if it's not already there
        if channel.id not in guild_data["whitelisted_channels"]:
            guild_data["whitelisted_channels"].append(channel.id)
            await self.db.starboard_settings.update_one(
                {"guild_id": guild_id}, {"$set": guild_data}, upsert=True
            )
            await interaction.response.send_message(
                f"Channel {channel.mention} has been whitelisted for starboard tracking.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"Channel {channel.mention} is already whitelisted.", ephemeral=True
            )

    @starboard.subcommand(description="Remove a channel from the starboard whitelist")
    async def remove_whitelist(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = SlashOption(
            description="Select a channel to remove from the whitelist",
            required=True,
        ),
    ):
        guild_id = interaction.guild_id

        # Get the current whitelist
        guild_data = await self.db.starboard_settings.find_one({"guild_id": guild_id})
        whitelisted_channels = guild_data.get("whitelisted_channels", [])

        if channel.id not in whitelisted_channels:
            await interaction.response.send_message(
                f"Channel {channel.mention} is not in the whitelist.", ephemeral=True
            )
        else:
            whitelisted_channels.remove(channel.id)
            await self.db.starboard_settings.update_one(
                {"guild_id": guild_id},
                {"$set": {"whitelisted_channels": whitelisted_channels}},
                upsert=True,
            )
            await interaction.response.send_message(
                f"Channel {channel.mention} has been removed from the whitelist.",
                ephemeral=True,
            )

    @remove_whitelist.on_autocomplete("channel")
    async def autocomplete_whitelisted_channels(
        self, interaction: nextcord.Interaction, current: str
    ):
        guild_id = interaction.guild_id
        guild_data = await self.db.starboard_settings.find_one({"guild_id": guild_id})
        whitelisted_channels = guild_data.get("whitelisted_channels", [])

        # Fetch all channels in the guild that are whitelisted
        channels = [
            interaction.guild.get_channel(ch_id) for ch_id in whitelisted_channels
        ]
        return [
            nextcord.SlashOptionChoice(channel.name, str(channel.id))
            for channel in channels
            if channel and current.lower() in channel.name.lower()
        ]

    @starboard.subcommand(description="Set the starboard channel")
    async def channel(
        self, interaction: nextcord.Interaction, channel: nextcord.TextChannel
    ):
        guild_id = interaction.guild_id

        # Get the current settings or create a new entry
        guild_data = await self.db.starboard_settings.find_one({"guild_id": guild_id})
        if not guild_data:
            guild_data = {
                "guild_id": guild_id,
                "whitelisted_channels": [],
                "starboard_channel_id": None,
            }

        # Set the starboard channel
        guild_data["starboard_channel_id"] = channel.id
        await self.db.starboard_settings.update_one(
            {"guild_id": guild_id}, {"$set": guild_data}, upsert=True
        )
        await interaction.response.send_message(
            f"Starboard channel has been set to {channel.mention}.", ephemeral=True
        )

    def _create_embed(self, message: nextcord.Message, reaction: nextcord.Reaction):
        """Helper function to create the starboard embed."""
        embed = nextcord.Embed(
            title="Starred Message",
            description=message.content or "[No Content]",
            color=EMBED_COLOR,
        )
        embed.add_field(name="Author", value=message.author.mention, inline=True)
        embed.add_field(
            name="Link to Message",
            value=f"[Jump to Message]({message.jump_url})",
            inline=True,
        )
        embed.set_footer(
            text=f"Channel: {message.channel.name} | Emoji: {reaction.emoji} | Reactions: {reaction.count}"
        )
        return embed


def setup(bot: commands.Bot):
    bot.add_cog(Starboard(bot))
