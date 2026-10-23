# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from discord.ext import commands
from open_meteo import OpenMeteo
from takina import config
import discord

# https://open-meteo.com/en/docs, under "WMO weather interpretation codes"
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class Weather(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_command(
        name="weather", description="Weather information command.", usage="Riyadh Saudi Arabia"
    )
    @lychecks.is_user_app()
    async def weather(self, ctx: commands.Context, *, location: commands.Range[str, 1, 300]):
        await ctx.defer()

        location_data = await lyhelpers.geocode(location)
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

        # i had to google this btw
        # you'd think i would remember from when we learnt this
        # in middle school, but nah
        temperature_f = weather.temperature * (9 / 5) + 32
        conditions = WEATHER_CODES.get(
            weather.weather_code, f"Unknown (code {weather.weather_code})"
        )

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{await lyhelpers.fetch_random_emoji()} Weather in **{lyhelpers.truncate(location_data.address, 200)}**\n"
        embed.description += f"\n> **Conditions**: {conditions}"
        embed.description += (
            f"\n> **Current Temperature**: {weather.temperature:.1f}°C / {temperature_f:.1f}°F"
        )
        embed.description += f"\n> **Elevation**: {int(forecast.elevation):,} metres"
        embed.description += f"\n> **Wind Speed**: {weather.wind_speed:,} km/h"
        embed.description += f"\n> **Wind Direction**: {weather.wind_direction:,}°"
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Weather(bot))
