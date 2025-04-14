import nextcord, geopy
from nextcord.ext import commands
from config import *
from ..libs.oclib import *
from geopy.extra.rate_limiter import RateLimiter
from open_meteo import OpenMeteo


async def find_weather(location: str):
    embed = nextcord.Embed(color=EMBED_COLOR)
    if len(location) > 300:
        embed.color = ERROR_COLOR
        embed.description = ":x: The location specified was not recognized."

    async with geopy.geocoders.Photon(
        user_agent="takina", adapter_factory=geopy.adapters.AioHTTPAdapter
    ) as geolocator:
        geocode = geopy.extra.rate_limiter.AsyncRateLimiter(
            geolocator.geocode, min_delay_seconds=1
        )
        location_data = await geocode(location)

    if location_data:
        async with OpenMeteo() as open_meteo:
            forecast = await open_meteo.forecast(
                latitude=location_data.latitude,
                longitude=location_data.longitude,
                current_weather=True,
            )

        embed.title = f"Weather Report for {location.capitalize()}"
        embed.description = ""
        weather = forecast.current_weather

        embed.description += f"\n**Current Temperature**: {weather.temperature}°C / {weather.temperature * (9/5) + 32}°F"
        embed.description += f"\n**Elevation**: {int(forecast.elevation)} metres"
        embed.description += f"\n**Wind Speed**: {weather.wind_speed} km/h"
        embed.description += f"\n**Wind Direction**: {weather.wind_direction}°"
        embed.description += f"\n**Weather Code**: {weather.weather_code}"
        return embed
    else:
        embed.color = ERROR_COLOR
        embed.description = ":x: The location specified was not recognized."
        return embed


class Weather(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        help="Weather information command. Usage: `weather Riyadh Saudi Arabia`.",
    )
    async def weather(self, ctx: commands.Context, *, location: str):
        embed = await find_weather(location)
        await ctx.reply(embed=embed, mention_author=False)
        pass


class SlashWeather(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="weather", description="Weather information command.")
    async def weather(
        self,
        interaction: nextcord.Interaction,
        *,
        location: str = nextcord.SlashOption(
            description="The location to fetch weather information on.", required=True
        ),
    ):
        await interaction.response.defer()
        embed = await find_weather(location)
        await interaction.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Weather(bot))
    bot.add_cog(SlashWeather(bot))
