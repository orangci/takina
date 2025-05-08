# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import nextcord
import config
from motor.motor_asyncio import AsyncIOMotorClient
from nextcord.ext import application_checks, commands


class Prefix(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(config.MONGO_URI).get_database(config.DB_NAME)

    @nextcord.slash_command(name="prefix", description=f"Set a custom prefix for {config.BOT_NAME}")
    @application_checks.has_permissions(administrator=True)
    async def set_prefix(self, interaction: nextcord.Interaction, new_prefix: str):
        guild_id = interaction.guild.id

        await self.db.prefixes.update_one({"guild_id": guild_id}, {"$set": {"prefix": new_prefix}}, upsert=True)
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed.description = f"✅ Prefix updated to: `{new_prefix}`"
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(Prefix(bot))
