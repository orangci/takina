# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyhelpers
from discord.ext import commands
from takina import config
import discord


class Salawat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @lychecks.is_user_app()
    @commands.hybrid_command(
        description="Fetch a list of the Islāmic prayer times in the specified location.",
        aliases=["salah", "prayer_times", "prayer", "prayers"],
        usage="Riyadh Saudi Arabia",
    )
    async def salawat(self, ctx: commands.Context, location_name: str):
        response = await lyhelpers.request(
            "https://api.aladhan.com/v1/timingsByAddress", params={"address": location_name}
        )

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = f"Islāmic Prayer Times for {location_name.title()}"

        prayer_times = response["data"]["timings"]
        embed.description = "\n".join(
            f"> **{prayer}**: {prayer_times[prayer]}"
            for prayer in ("Fajr", "Dhuhr", "Asr", "Maghrib", "Isha")
        )
        embed.set_footer(
            text="Please note that these times are in the timezone of the location specified, not your timezone."
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Salawat(bot))
