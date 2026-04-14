import nextcord
from motor.motor_asyncio import AsyncIOMotorClient
from nextcord.ext import application_checks, commands
import config


class Honeypot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(config.MONGO_URI).get_database(config.DB_NAME)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Fetch the guild info
        guild_id = message.guild.id
        guild_data = await self.db.honeypot_settings.find_one({"guild_id": guild_id})
        if not guild_data:
            return

        # Fetch the honeypot channel ID and ensure it exists
        honeypot_channel_id = guild_data.get("honeypot_channel_id")
        if not honeypot_channel_id:
            return

        honeypot_channel = self.bot.get_channel(honeypot_channel_id)
        if not honeypot_channel:
            return

        # Fetch the message details
        channel = self.bot.get_channel(message.channel)
        if not channel:
            return

        member = message.author

        if message.channel.id == honeypot_channel_id:
            embed = nextcord.Embed(
                description=f"You were banned in **{message.guild.name}**. \n\n<:note:1289880498541297685> **Reason:** You triggered our honeypot system, which usually means that your account got hacked.",
                color=config.EMBED_COLOR,
            )
            await nextcord.Member.send(embed=embed)
            await member.ban(reason=f"Banned for triggering the honeypot system.")
            modlog_cog = self.bot.get_cog("ModLog")
            if modlog_cog:
                await modlog_cog.log_action("ban", member, reason=f"Banned by automod for triggering the honeypot system.", moderator = message.guild.get_member(self.bot.application_id))

    @nextcord.slash_command(name="honeypot", description="Command to setup a honeypot channel")
    @application_checks.has_permissions(manage_guild=True)
    async def honeypot_configure(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = nextcord.SlashOption(description="The channel in which you want the bot to use for the honeypot"),
    ):
        await interaction.response.defer(ephemeral=True)

        guild_data = await self.db.honeypot_settings.find_one({"guild_id": interaction.guild_id})
        if not guild_data:
            guild_data = {"guild_id": interaction.guild_id, "honeypot_channel_id": None}

        guild_data["honeypot_channel_id"] = channel.id
        await self.db.honeypot_settings.update_one({"guild_id": interaction.guild_id}, {"$set": guild_data}, upsert=True)
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed.description = f"✅ Honeypot channel has been set to {channel.mention}."
        await interaction.followup.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(Honeypot(bot))
