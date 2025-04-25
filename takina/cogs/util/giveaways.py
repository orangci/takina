# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import random

import emoji as emotelib
import nextcord
import config
from motor.motor_asyncio import AsyncIOMotorClient
from nextcord import SlashOption
from nextcord.ext import application_checks, commands

from ..libs import oclib


async def is_valid_emoji(interaction, emoji: str) -> bool:
    if emoji.startswith("<:") and emoji.endswith(">"):
        emoji_id = emoji.split(":")[2][:-1]
        return (
            nextcord.utils.get(interaction.guild.emojis, id=int(emoji_id)) is not None
        )

    return emoji in emotelib.EMOJI_DATA


class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(config.MONGO_URI).get_database(config.DB_NAME)

    @nextcord.slash_command(name="giveaway", description="Giveaway management commands")
    async def giveaway(self, interaction: nextcord.Interaction):
        pass

    @giveaway.subcommand(name="start", description="Start a giveaway")
    @application_checks.has_permissions(manage_events=True)
    async def start(
        self,
        interaction: nextcord.Interaction,
        title: str = SlashOption(description="Title of the giveaway", required=True),
        description: str = SlashOption(
            description="Description of the giveaway", required=True
        ),
        emoji: str = SlashOption(
            description="Reaction emoji for the giveaway", required=True
        ),
    ):
        await interaction.response.defer(ephemeral=True)

        # Check if there's an active giveaway in the current channel
        active_giveaway = await self.db.giveaways.find_one(
            {"channel_id": interaction.channel.id, "active": True}
        )
        if active_giveaway:
            random_emoji = await oclib.fetch_random_emoji()
            embed = nextcord.Embed(
                description=f"{random_emoji}There is already an active giveaway in this channel. End it before starting a new one.",
                color=config.EMBED_COLOR,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Check if the emoji is a valid standard or custom emoji
        if not await is_valid_emoji(interaction, emoji):
            random_emoji = await oclib.fetch_random_emoji()
            embed = nextcord.Embed(
                description=f"{random_emoji}The emoji you entered is invalid; either it is not an emoji or it is an emoji I do not have access to.",
                color=config.EMBED_COLOR,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Create and send the giveaway embed
        description += f"\n\nReact with {emoji} to join!"
        embed = nextcord.Embed(
            title=title, description=description, color=config.EMBED_COLOR
        )
        giveaway_message = await interaction.channel.send(embed=embed)
        await giveaway_message.add_reaction(emoji)

        # Save giveaway data in the database
        await self.db.giveaways.insert_one(
            {
                "guild_id": interaction.guild.id,
                "channel_id": interaction.channel.id,
                "message_id": giveaway_message.id,
                "emoji": emoji,
                "active": True,
            }
        )

        embed = nextcord.Embed(
            description="✅ Giveaway successfully started.", color=config.EMBED_COLOR
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @giveaway.subcommand(name="end", description="End the current giveaway")
    @application_checks.has_permissions(manage_events=True)
    async def end(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Fetch the active giveaway in the current channel
        active_giveaway = await self.db.giveaways.find_one(
            {"channel_id": interaction.channel.id, "active": True}
        )
        if not active_giveaway:
            random_emoji = await oclib.fetch_random_emoji()
            embed = nextcord.Embed(
                description=f"{random_emoji}No active giveaway found in this channel.",
                color=config.EMBED_COLOR,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Fetch the giveaway message
        channel = interaction.guild.get_channel(active_giveaway["channel_id"])
        giveaway_message = await channel.fetch_message(active_giveaway["message_id"])

        # Find users who reacted with the correct emoji
        users = [
            user async for user in giveaway_message.reactions[0].users() if not user.bot
        ]
        if not users:
            await self.db.giveaways.update_one(
                {"_id": active_giveaway["_id"]}, {"$set": {"active": False}}
            )
            random_emoji = await oclib.fetch_random_emoji()
            embed = nextcord.Embed(
                description="✅ Ended giveaway without a winner; no participants detected.",
                color=config.EMBED_COLOR,
            )
            await interaction.channel.send(embed=embed)
            embed.description = "✅ Giveaway ended successfully."
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Choose a random winner
        winner = random.choice(users)

        # Mark giveaway as ended in the database
        await self.db.giveaways.update_one(
            {"_id": active_giveaway["_id"]}, {"$set": {"active": False}}
        )

        embed = nextcord.Embed(
            title="Giveaway Ended",
            description=f"The winner of the giveaway is {winner.mention}!",
            color=config.EMBED_COLOR,
        )
        await interaction.channel.send(winner.mention, embed=embed)

        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed.description = "✅ Giveaway ended successfully."
        await interaction.followup.send(embed=embed, ephemeral=True)

    @giveaway.subcommand(name="reroll", description="Reroll the giveaway winner")
    @application_checks.has_permissions(manage_events=True)
    async def reroll(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Fetch the ended giveaway in the current channel
        giveaway = await self.db.giveaways.find_one(
            {"channel_id": interaction.channel.id, "active": False}
        )
        if not giveaway:
            random_emoji = await oclib.fetch_random_emoji()
            embed = nextcord.Embed(
                description=f"{random_emoji}No ended giveaway found in this channel.",
                color=config.EMBED_COLOR,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Fetch the giveaway message
        channel = interaction.guild.get_channel(giveaway["channel_id"])
        giveaway_message = await channel.fetch_message(giveaway["message_id"])

        # Find users who reacted with the correct emoji
        users = [
            user async for user in giveaway_message.reactions[0].users() if not user.bot
        ]
        if not users:
            random_emoji = await oclib.fetch_random_emoji()
            embed = nextcord.Embed(
                description=f"{random_emoji}No reactions found for the giveaway.",
                color=config.EMBED_COLOR,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Choose a new random winner
        new_winner = random.choice(users)

        random_emoji = await oclib.fetch_random_emoji()
        embed = nextcord.Embed(
            title="Giveaway Rerolled",
            description=f"{random_emoji}The new winner of the giveaway is {new_winner.mention}!",
            color=config.EMBED_COLOR,
        )
        await interaction.channel.send(embed=embed)

        await interaction.followup.send(
            "✅ Giveaway rerolled successfully.", ephemeral=True
        )


def setup(bot):
    bot.add_cog(Giveaway(bot))
