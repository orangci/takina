import nextcord, geopy, datetime, tzfpy, pytz
from nextcord.ext import commands
from config import *
from ..libs.oclib import *
from geopy.extra.rate_limiter import RateLimiter


async def find_time(location: str):
    embed = nextcord.Embed(color=EMBED_COLOR)
    if len(location) > 300:
        embed.color = ERROR_COLOR
        embed.description = ":x: The location name you specified is too long. Please enter a shorter name."

    async with geopy.geocoders.Photon(
        user_agent=BOT_NAME, adapter_factory=geopy.adapters.AioHTTPAdapter
    ) as geolocator:
        geocode = geopy.extra.rate_limiter.AsyncRateLimiter(
            geolocator.geocode, min_delay_seconds=1
        )
        location_data = await geocode(location)

    if location_data:
        timezone = tzfpy.get_tz(location_data.longitude, location_data.latitude)
        local_tz = pytz.timezone(timezone)
        local_time = datetime.datetime.now(local_tz)
        formatted_time = local_time.strftime("%H.%M (%I.%M %p)")

        embed.description = f"The current time in {timezone} is {formatted_time}."
        return embed
    else:
        embed.color = ERROR_COLOR
        embed.description = ":x: The location specified was not recognized."
        return embed


class Time(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases=["timezone"],
        help="Timezone utility command. Usage: `time Riyadh Saudi Arabia`.",
    )
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
        location: str = nextcord.SlashOption(
            description="The location to fetch time information on.", required=True
        ),
    ):
        await interaction.response.defer()
        embed = await find_time(location)
        await interaction.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Time(bot))
    bot.add_cog(SlashTime(bot))
