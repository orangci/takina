# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors
from geopy.adapters import AioHTTPAdapter
from geopy.extra import rate_limiter
from discord.ext import commands
from open_meteo import OpenMeteo
from takina import config
import discord
import geopy


class Weather(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_command(
        name="weather", description="Weather information command.", usage="Riyadh Saudi Arabia"
    )
    @lychecks.is_user_app()
    async def weather(self, ctx: commands.Context, *, location: str):
        if len(location) > 300:
            raise lyerrors.TakinaUserInputError(
                "The location name specified is too long. Please enter a shorter location."
            )

        async with geopy.geocoders.Nominatim(
            user_agent=config.BOT_NAME, adapter_factory=AioHTTPAdapter
        ) as geolocator:
            geocode = rate_limiter.AsyncRateLimiter(geolocator.geocode, min_delay_seconds=1)
            location_data = await geocode(location)

        if not location_data:
            raise lyerrors.TakinaNotFoundError("The location specified was not recognized.")

        async with OpenMeteo() as open_meteo:
            forecast = await open_meteo.forecast(
                latitude=location_data.latitude,
                longitude=location_data.longitude,
                current_weather=True,
            )

        weather = forecast.current_weather
        if not weather:
            raise lyerrors.TakinaNotFoundError(
                "No forecast found for the current weather in that location."
            )

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = f"Weather Report for {location.capitalize()}"
        embed.description = ""

        # i had to google this btw
        # you'd think i would remember from when we learnt this
        # in middle school, but nah
        temperature_f = weather.temperature * (9 / 5) + 32

        embed.description += (
            f"\n> **Current Temperature**: {weather.temperature}°C / {temperature_f}°F"
        )
        embed.description += f"\n> **Elevation**: {int(forecast.elevation):,} metres"
        embed.description += f"\n> **Wind Speed**: {weather.wind_speed:,} km/h"
        embed.description += f"\n> **Wind Direction**: {weather.wind_direction:,}°"
        embed.description += f"\n> **Weather Code**: {weather.weather_code:,}"
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Weather(bot))
