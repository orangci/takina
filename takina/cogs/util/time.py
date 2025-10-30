# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from geopy.extra import rate_limiter
from nextcord.ext import commands
import datetime
import nextcord
import config
import tzfpy
import geopy
import pytz


async def find_time(location: str):
    embed = nextcord.Embed(color=config.EMBED_COLOR)
    if len(location) > 300:
        embed.color = config.ERROR_COLOR
        embed.description = ":x: The location name you specified is too long. Please enter a shorter name."

    async with geopy.geocoders.Nominatim(user_agent=config.BOT_NAME, adapter_factory=geopy.adapters.AioHTTPAdapter) as geolocator:
        geocode = rate_limiter.AsyncRateLimiter(geolocator.geocode, min_delay_seconds=1)
        location_data = await geocode(location)

    if location_data:
        timezone = tzfpy.get_tz(location_data.longitude, location_data.latitude)
        local_tz = pytz.timezone(timezone)
        local_time = datetime.datetime.now(local_tz)
        formatted_time = local_time.strftime("%H:%M (%I:%M %p)")

        embed.description = f"The current time in {timezone} is {formatted_time}."
        return embed
    else:
        embed.color = config.ERROR_COLOR
        embed.description = ":x: The location specified was not recognized."
        return embed


class Time(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["timezone"], help="Timezone utility command.", usage="Riyadh Saudi Arabia")
    async def time(self, ctx: commands.Context, *, location: str):
        embed = await find_time(location)
        await ctx.reply(embed=embed, mention_author=False)
        pass


class SlashTime(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="time", description="Timezone utility command.")
    async def time(
        self,
        interaction: nextcord.Interaction,
        *,
        location: str = nextcord.SlashOption(description="The location to fetch time information on.", required=True),
    ):
        await interaction.response.defer()
        embed = await find_time(location)
        await interaction.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Time(bot))
    bot.add_cog(SlashTime(bot))
