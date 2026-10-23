# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from discord.ext import commands
from zoneinfo import ZoneInfo
from datetime import datetime
from takina import config
import discord
import tzfpy


class Time(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_command(
        name="time",
        aliases=["timezone"],
        description="Timezone utility command.",
        usage="Riyadh Saudi Arabia",
    )
    @lychecks.is_user_app()
    async def time(self, ctx: commands.Context, *, location: commands.Range[str, 1, 300]):
        await ctx.defer()

        location_data = await lyhelpers.geocode(location)
        if not location_data:
            raise lyerrors.TakinaNotFoundError("The location specified was not recognized.")

        timezone = tzfpy.get_tz(location_data.longitude, location_data.latitude)
        if timezone is None:
            raise lyerrors.TakinaNotFoundError(
                "A timezone could not be determined for that location."
            )

        local_time = datetime.now(ZoneInfo(timezone))
        formatted_time = local_time.strftime("%H:%M (%I:%M %p)")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"The current time in {timezone} is {formatted_time}."
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Time(bot))
