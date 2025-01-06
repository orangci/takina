import nextcord
from motor.motor_asyncio import AsyncIOMotorClient
import os
from nextcord.ext import commands
from config import *
from .lib import *


class Counting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(MONGO_URI).get_database(DB_NAME)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.guild.id != SERVER_ID:
            return

        counting_channel = self.bot.get_channel(COUNTING_CHANNEL_ID)

        if message.channel.id != COUNTING_CHANNEL_ID:
            return

        # Get the last message count from the database
        current_count = await self.db.counting.find_one(
            {"channel_id": COUNTING_CHANNEL_ID}
        )

        if not current_count:
            await self.db.counting.insert_one(
                {"channel_id": COUNTING_CHANNEL_ID, "count": 0}
            )
            current_count = {"count": 0}

        last_number = current_count["count"]

        # Check if the message content is the next number
        try:
            next_number = int(message.content)
            if next_number == last_number + 1:
                await self.db.counting.update_one(
                    {"channel_id": COUNTING_CHANNEL_ID},
                    {"$set": {"count": next_number}},
                )

            else:
                await message.delete()

        except ValueError:
            await message.delete()

    @commands.command()
    @is_in_guild()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def count(self, ctx: commands.Context):
        """Fetches and displays the current count from the database."""

        current_count = await self.db.counting.find_one(
            {"channel_id": COUNTING_CHANNEL_ID}
        )

        if not current_count:
            await ctx.reply("The count has not started yet!", mention_author=False)
            return

        count = current_count["count"]

        await ctx.reply(f"The current count is: {count}", mention_author=False)

    @commands.command()
    @is_in_guild()
    @commands.is_owner()
    async def set_count(self, ctx: commands.Context, count: int):
        """Allows bot owner to set the current count in the counting channel."""

        await self.db.counting.update_one(
            {"channel_id": COUNTING_CHANNEL_ID}, {"$set": {"count": count}}
        )
        await ctx.reply(f"The count has been set to {count}.", mention_author=False)


def setup(bot: commands.Bot):
    bot.add_cog(Counting(bot))
