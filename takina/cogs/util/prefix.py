import os
import nextcord
from nextcord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from __main__ import DB_NAME

class Prefix(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(os.getenv("MONGO")).get_database(DB_NAME)

    @nextcord.slash_command(name="prefix", description="Set a custom prefix for Takina")
    async def set_prefix(self, interaction: nextcord.Interaction, new_prefix: str):
        guild_id = interaction.guild.id
        
        await self.db.prefixes.update_one(
            {"guild_id": guild_id},
            {"$set": {"prefix": new_prefix}},
            upsert=True
        )

        await interaction.response.send_message(f"Prefix updated to: `{new_prefix}`", ephemeral=True)

def setup(bot):
    bot.add_cog(Prefix(bot))
