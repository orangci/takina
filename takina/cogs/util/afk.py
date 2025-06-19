# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import application_checks, commands
from motor.motor_asyncio import AsyncIOMotorClient
from nextcord import SlashOption
from ..libs import oclib
import nextcord
import config


class AFK(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(config.MONGO_URI).get_database(config.DB_NAME)

    async def set_afk_status(self, user_id: int, reason: str):
        """Sets a user's AFK status in the database."""
        await self.db.afk.update_one({"user_id": user_id}, {"$set": {"reason": reason}}, upsert=True)

    async def remove_afk_status(self, user_id: int):
        """Removes a user's AFK status from the database."""
        await self.db.afk.delete_one({"user_id": user_id})

    async def get_afk_status(self, user_id: int):
        """Gets a user's AFK status from the database."""
        user_data = await self.db.afk.find_one({"user_id": user_id})
        return user_data.get("reason") if user_data else None

    @commands.command(
        name="afk", help=f"Toggle AFK status. When AFK, {config.BOT_NAME} will notify others if they mention you.", usage="watching anime"
    )
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK"):
        user_id = ctx.author.id
        current_status = await self.get_afk_status(user_id)

        if current_status:
            # Remove AFK status
            await self.remove_afk_status(user_id)
            return
        else:
            # Set AFK status
            await self.set_afk_status(user_id, reason)
            embed = nextcord.Embed(
                description=f"{await oclib.fetch_random_emoji()}{ctx.author.mention} is now AFK: {reason}", color=config.EMBED_COLOR
            )
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="afk", description=f"Toggle AFK status. When AFK, {config.BOT_NAME} will notify others if they mention you.")
    @application_checks.has_permissions(send_messages=True)
    async def afk_slash(self, interaction: nextcord.Interaction, reason: str = SlashOption(description="Reason for going AFK", required=False)):
        await interaction.response.defer()
        user_id = interaction.user.id
        current_status = await self.get_afk_status(user_id)

        if current_status:
            # Remove AFK status
            await self.remove_afk_status(user_id)
            embed = nextcord.Embed(description=f"{await oclib.fetch_random_emoji()}You are no longer AFK.", color=config.EMBED_COLOR)
        else:
            # Set AFK status
            await self.set_afk_status(user_id, reason)
            embed = nextcord.Embed(
                description=f"{await oclib.fetch_random_emoji()}{interaction.user.mention} is now AFK: {reason}", color=config.EMBED_COLOR
            )
        await interaction.send(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return

        # Check if the author is AFK and remove if so
        current_status = await self.get_afk_status(message.author.id)
        if current_status:
            await self.remove_afk_status(message.author.id)
            embed = nextcord.Embed(description=f"{await oclib.fetch_random_emoji()}You are no longer AFK.", color=config.EMBED_COLOR)
            await message.channel.send(embed=embed, delete_after=5)

        # Notify mentions about AFK users
        for user in message.mentions:
            afk_message = await self.get_afk_status(user.id)
            if afk_message:
                embed = nextcord.Embed(
                    description=f"{await oclib.fetch_random_emoji()}{user.mention} is currently AFK: {afk_message}", color=config.EMBED_COLOR
                )
                await message.channel.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(AFK(bot))
