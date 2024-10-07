import os
import nextcord
from nextcord.ext import commands, application_checks
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
from __main__ import DB_NAME, EMBED_COLOR


class ModLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(os.getenv("MONGO")).get_database(DB_NAME)

    @nextcord.slash_command(description="Manage the modlog settings")
    async def modlog(self, interaction: nextcord.Interaction):
        pass

    @modlog.subcommand(description="Set the modlog channel")
    async def channel(
        self, interaction: nextcord.Interaction, channel: nextcord.TextChannel
    ):
        guild_id = interaction.guild_id

        guild_data = await self.db.modlog_settings.find_one({"guild_id": guild_id})
        if not guild_data:
            guild_data = {
                "guild_id": guild_id,
                "modlog_channel_id": None,
            }

        guild_data["modlog_channel_id"] = channel.id

        await self.db.modlog_settings.update_one(
            {"guild_id": guild_id}, {"$set": guild_data}, upsert=True
        )

        await interaction.response.send_message(
            f"Modlog channel has been set to {channel.mention}.", ephemeral=True
        )

    async def log_action(
        self,
        type: str,
        member: nextcord.Member,
        reason: str,
        moderator: nextcord.Member,
        duration: str = None,
    ):
        guild_id = member.guild.id
        guild_data = await self.db.modlog_settings.find_one({"guild_id": guild_id})
        if not guild_data:
            return

        modlog_channel_id = guild_data.get("modlog_channel_id")
        if not modlog_channel_id:
            print("no modlog channel")
            return

        modlog_channel = self.bot.get_channel(modlog_channel_id)
        if not modlog_channel:
            return

        embed = nextcord.Embed(
            color=EMBED_COLOR,
            timestamp=datetime.datetime.utcnow(),
        )
        if duration:
            embed.add_field(
                name="Action", value=type.capitalize() + f" ({duration})", inline=True
            )
        else:
            embed.add_field(name="Action", value=type.capitalize(), inline=True)
        embed.add_field(name="Case", value="placeholder uwu", inline=True)
        embed.add_field(name="Moderator", value=moderator.mention, inline=True)
        embed.add_field(name="Target", value=member.mention, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_thumbnail(url=member.avatar)
        await modlog_channel.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(ModLog(bot))
