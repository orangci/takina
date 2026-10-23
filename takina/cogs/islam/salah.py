# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from discord.ext import commands
from takina import config
import discord


class Salawat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_command(
        description="Fetch a list of the Islāmic prayer times in the specified location.",
        aliases=["salah", "prayer_times", "prayer", "prayers"],
        usage="Riyadh Saudi Arabia",
    )
    @lychecks.is_user_app()
    async def salawat(self, ctx: commands.Context, *, location_name: commands.Range[str, 1, 300]):
        await ctx.defer()

        response = await lyhelpers.request(
            "https://api.aladhan.com/v1/timingsByAddress", params={"address": location_name}
        )

        data = response.get("data")
        if not isinstance(data, dict) or not (prayer_times := data.get("timings")):
            # errors come back with a message in data instead of timings
            raise lyerrors.TakinaNotFoundError("Prayer times for that location could not be found.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = lyhelpers.truncate(f"Islāmic Prayer Times for {location_name.title()}", 256)
        embed.description = "\n".join(
            f"> **{prayer}**: {prayer_times.get(prayer, 'Unknown')}"
            for prayer in ("Fajr", "Dhuhr", "Asr", "Maghrib", "Isha")
        )

        if timezone := data.get("meta", {}).get("timezone"):
            embed.set_footer(text=f"Times are in {timezone}, the timezone of that location.")
        else:
            embed.set_footer(
                text="Please note that these times are in the timezone of the location specified, not your timezone."
            )

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Salawat(bot))
