# SPDX-License-Identifier: AGPL-3.0-or-later
import nextcord
from motor.motor_asyncio import AsyncIOMotorClient
import os
from nextcord.ext import commands
from config import *
from .libs.lib import *
from ...libs.oclib import *


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

    @commands.command(
        help="Fetches and displays the current count in the counting channel."
    )
    @is_in_guild()
    async def count(self, ctx: commands.Context):

        current_count = await self.db.counting.find_one(
            {"channel_id": COUNTING_CHANNEL_ID}
        )

        if not current_count:
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = ":x: The count has not started yet!"
            await ctx.reply(embed=embed, mention_author=False)
            return

        count = current_count["count"]

        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = f"{await fetch_random_emoji()}The current count is: {count}"
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        help="Set the count of the counting channel. Usage: `set_count <number>`.",
        aliases=["setcount"],
    )
    @is_in_guild()
    @commands.is_owner()
    async def set_count(self, ctx: commands.Context, count: int):
        """Allows bot owner to set the current count in the counting channel."""

        await self.db.counting.update_one(
            {"channel_id": COUNTING_CHANNEL_ID}, {"$set": {"count": count}}
        )

        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = f"✅ The count has been set to {count}."
        await ctx.reply(embed=embed, mention_author=False)


def setup(bot: commands.Bot):
    bot.add_cog(Counting(bot))
