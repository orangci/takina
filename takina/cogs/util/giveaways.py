import nextcord
from nextcord.ext import commands, application_checks
from nextcord import SlashOption
from motor.motor_asyncio import AsyncIOMotorClient
import random
import os
from __main__ import EMBED_COLOR

DB_NAME = "your_db_name"

class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(os.getenv("MONGO")).get_database(DB_NAME)

    @commands.command()
    @commands.is_owner()
    async def cg(self, ctx: commands.Context):
        await self.db.giveaways.drop()
        await ctx.reply("deleted giveaways database owo", mention_author=False)

    @nextcord.slash_command(name="giveaway", description="Giveaway management commands")
    async def giveaway(self, interaction: nextcord.Interaction):
        pass

    @giveaway.subcommand(name="start", description="Start a giveaway")
    @application_checks.has_permissions(manage_events=True)
    async def start(
        self,
        interaction: nextcord.Interaction,
        title: str = SlashOption(description="Title of the giveaway", required=True),
        description: str = SlashOption(description="Description of the giveaway", required=True),
        emoji: str = SlashOption(description="Reaction emoji for the giveaway", required=True)
    ):
        await interaction.response.defer(ephemeral=True)

        # Check if emoji is valid
        # try:
        #     await interaction.message.add_reaction(emoji)
        # except nextcord.InvalidArgument:
        #     embed = nextcord.Embed(
        #         description=f"The emoji '{emoji}' is invalid. Please provide a valid emoji.",
        #         color=EMBED_COLOR
        #     )
        #     await interaction.followup.send(embed=embed, ephemeral=True)
        #     return

        # Check if there's an active giveaway in the current channel
        active_giveaway = await self.db.giveaways.find_one({"channel_id": interaction.channel.id, "active": True})
        if active_giveaway:
            embed = nextcord.Embed(
                description="There is already an active giveaway in this channel. End it before starting a new one.",
                color=EMBED_COLOR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Create and send the giveaway embed
        embed = nextcord.Embed(title=title, description=description, color=EMBED_COLOR)
        embed.set_footer(text="React with the emoji to join!")
        giveaway_message = await interaction.channel.send(embed=embed)
        await giveaway_message.add_reaction(emoji)

        # Save giveaway data in the database
        await self.db.giveaways.insert_one({
            "guild_id": interaction.guild.id,
            "channel_id": interaction.channel.id,
            "message_id": giveaway_message.id,
            "emoji": emoji,
            "active": True
        })

        embed = nextcord.Embed(
            description=f"Giveaway started with title '{title}' and emoji '{emoji}'.",
            color=EMBED_COLOR
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @giveaway.subcommand(name="end", description="End the current giveaway")
    @application_checks.has_permissions(manage_events=True)
    async def end(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Fetch the active giveaway in the current channel
        active_giveaway = await self.db.giveaways.find_one({"channel_id": interaction.channel.id, "active": True})
        if not active_giveaway:
            embed = nextcord.Embed(
                description="No active giveaway found in this channel.",
                color=EMBED_COLOR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Fetch the giveaway message
        channel = interaction.guild.get_channel(active_giveaway["channel_id"])
        giveaway_message = await channel.fetch_message(active_giveaway["message_id"])

        # Find users who reacted with the correct emoji
        users = [user async for user in giveaway_message.reactions[0].users() if not user.bot]
        if not users:
            embed = nextcord.Embed(
                description="No reactions found for the giveaway.",
                color=EMBED_COLOR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Choose a random winner
        winner = random.choice(users)

        # Mark giveaway as ended in the database
        await self.db.giveaways.update_one({"_id": active_giveaway["_id"]}, {"$set": {"active": False}})

        embed = nextcord.Embed(
            title="Giveaway Ended",
            description=f"The winner of the giveaway is {winner.mention}!",
            color=EMBED_COLOR
        )
        await interaction.channel.send(embed=embed)

        await interaction.followup.send("Giveaway ended successfully.", ephemeral=True)

    @giveaway.subcommand(name="reroll", description="Reroll the giveaway winner")
    @application_checks.has_permissions(manage_events=True)
    async def reroll(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Fetch the ended giveaway in the current channel
        giveaway = await self.db.giveaways.find_one({"channel_id": interaction.channel.id, "active": False})
        if not giveaway:
            embed = nextcord.Embed(
                description="No ended giveaway found in this channel.",
                color=EMBED_COLOR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Fetch the giveaway message
        channel = interaction.guild.get_channel(giveaway["channel_id"])
        giveaway_message = await channel.fetch_message(giveaway["message_id"])

        # Find users who reacted with the correct emoji
        users = [user async for user in giveaway_message.reactions[0].users() if not user.bot]
        if not users:
            embed = nextcord.Embed(
                description="No reactions found for the giveaway.",
                color=EMBED_COLOR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Choose a new random winner
        new_winner = random.choice(users)

        embed = nextcord.Embed(
            title="Giveaway Rerolled",
            description=f"The new winner of the giveaway is {new_winner.mention}!",
            color=EMBED_COLOR
        )
        await interaction.channel.send(embed=embed)

        await interaction.followup.send("Giveaway rerolled successfully.", ephemeral=True)


def setup(bot):
    bot.add_cog(Giveaway(bot))
