from pymongo import AsyncMongoClient
from nextcord.ext import application_checks, commands
import datetime as dt
import nextcord
import config


class Honeypot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncMongoClient(host=config.MONGO_URI).get_database(config.DB_NAME)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Fetch the guild info
        guild_id = message.guild.id
        guild_data = await self.db.honeypot_settings.find_one({"guild_id": guild_id})

        # Fetch the honeypot channel ID and ensure it exists
        honeypot_channel_id = guild_data.get("honeypot_channel_id")

        # honeypot_channel = self.bot.get_channel(honeypot_channel_id)

        # Fetch the message details
        # channel = self.bot.get_channel(message.channel)

        member = message.author
        timeout = dt.timedelta(weeks=4)

        if message.channel.id == honeypot_channel_id:
            await member.timeout(reason="Muted for triggering the honeypot system.", timeout=timeout)
            embed = nextcord.Embed(
                description=f"You were muted in **{message.guild.name}**. \n\n<:note:1289880498541297685> **Reason:** You triggered our honeypot system, which usually means that your account got hacked. Please contact the server moderators to appeal your mute.",
                color=config.EMBED_COLOR,
            )
            await member.send(embed=embed)
            for channel in message.guild.text_channels:
                try:
                    await channel.purge(
                        before=dt.datetime.now(),
                        after=dt.datetime.now() - dt.timedelta(minutes=10),
                        check=lambda x: x.author.id == message.author.id,
                        oldest_first=False,
                        bulk=True,
                    )
                except nextcord.Forbidden:
                    pass
            modlog_cog = self.bot.get_cog("ModLog")
            if modlog_cog:
                await modlog_cog.log_action(
                    "mute",
                    member,
                    reason="Muted for triggering the honeypot system.",
                    moderator=message.guild.get_member(self.bot.application_id),
                    duration="4w",
                )

    @nextcord.slash_command(name="honeypot", description="Honeypot channel setup")
    @application_checks.has_permissions(manage_guild=True)
    async def honeypot_configure(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = nextcord.SlashOption(
            description="The channel in which you want the bot to use for the honeypot", required=True
        ),
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
