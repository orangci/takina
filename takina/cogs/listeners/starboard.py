import nextcord
from nextcord.ext import commands, application_checks
from motor.motor_asyncio import AsyncIOMotorClient
import os
from nextcord import SlashOption
from __main__ import DB_NAME, EMBED_COLOR


class Starboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(os.getenv("MONGO")).get_database(DB_NAME)
        self.starboard_messages = {}

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: nextcord.RawReactionActionEvent):
        # Fetch the guild info
        guild_id = payload.guild_id
        guild_data = await self.db.starboard_settings.find_one({"guild_id": guild_id})
        if not guild_data:
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
                # Update the starboard message if reactions reach 5 stars or more
                if emoji_reaction.count >= 5:
                    starboard_message_id = existing_star_message.get("starboard_message_id")
                    starboard_message = await starboard_channel.fetch_message(starboard_message_id)
                    if starboard_message:
                        updated_embed = self._create_embed(message, emoji_reaction)
                        await starboard_message.edit(embed=updated_embed)
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

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: nextcord.RawReactionActionEvent):
        # When a reaction is removed, update the starboard message
        await self._update_starboard_message(payload)

    async def _update_starboard_message(self, payload: nextcord.RawReactionActionEvent):
        guild_id = payload.guild_id
        guild_data = await self.db.starboard_settings.find_one({"guild_id": guild_id})
        if not guild_data:
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
        existing_star_message = await self.db.starboard.find_one(
            {"message_id": message.id}
        )

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
                updated_embed = self._create_embed(message, emoji_reaction)
                await starboard_message.edit(embed=updated_embed)

    @nextcord.slash_command(description="Manage the starboard settings")
    async def starboard(self, interaction: nextcord.Interaction):
        pass

    @starboard.subcommand(description="Set the starboard channel")
    async def channel(
        self, interaction: nextcord.Interaction, channel: nextcord.TextChannel
    ):
        guild_id = interaction.guild_id

        await interaction.response.defer(ephemeral=True)

        guild_data = await self.db.starboard_settings.find_one({"guild_id": guild_id})
        if not guild_data:
            guild_data = {"guild_id": guild_id, "starboard_channel_id": None}

        guild_data["starboard_channel_id"] = channel.id
        await self.db.starboard_settings.update_one(
            {"guild_id": guild_id}, {"$set": guild_data}, upsert=True
        )
        await interaction.followup.send(
            f"Starboard channel has been set to {channel.mention}.", ephemeral=True
        )


    def _create_embed(self, message: nextcord.Message, reaction: nextcord.Reaction):
        """Helper function to create the starboard embed."""
        embed = nextcord.Embed(
            title="Starred Message",
            description=f"[Jump to Message]({message.jump_url})\n\n" + message.content
            or f"[Jump to Message]({message.jump_url})\n\n"
            + "Image / Other Media / No Content",
            color=EMBED_COLOR,
        )
        embed.add_field(name="👤 Author", value=message.author.mention, inline=True)
        embed.add_field(
            name=":hash: Channel",
            value=message.channel.mention,
            inline=True,
        )
        embed.add_field(name="Reaction", value=f"{reaction.count} {reaction.emoji} reactions", inline=True)
        return embed


def setup(bot: commands.Bot):
    bot.add_cog(Starboard(bot))
