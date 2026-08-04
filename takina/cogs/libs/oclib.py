from __main__ import bot, start_time
import discord
import datetime
import aiohttp
import random
import config
import re


# for requesting data from APIs
async def request(url, headers=None, *args, **kwargs):
    if headers:
        kwargs["headers"] = headers

    async with aiohttp.ClientSession() as session:
        async with session.request("GET", url, *args, **kwargs) as response:
            return await response.json()


async def post(url, headers=None, *args, **kwargs):
    if headers:
        kwargs["headers"] = headers

    async with aiohttp.ClientSession() as session:
        async with session.post(url, *args, **kwargs) as response:
            return await response.json()


# for calculating durations, e.g. 1d, 2h, 5s, 34m
def duration_calculator(
    duration: str, slowmode=False, timeout=False, purge=False
) -> int | discord.Embed:
    pattern = r"(\d+)([s|m|h|d|w])"
    match = re.fullmatch(pattern, duration)
    error_embed = discord.Embed(color=config.ERROR_COLOR)
    if timeout:
        error_embed.description = (
            ":x: Invalid duration format. Use <number>[s|m|h|d|w]."
        )
    if slowmode:
        error_embed.description = ":x: Invalid duration format. Use <number>[s|m|h]."

    if not match:
        return error_embed

    time_value, time_unit = match.groups()
    time_value = int(time_value)

    if time_unit == "s":
        time_value *= 1
    elif time_unit == "m":
        time_value *= 60
    elif time_unit == "h":
        time_value *= 3600
    elif time_unit == "d":
        time_value *= 86400
    elif time_unit == "w":
        time_value *= 604800
    else:
        return error_embed

    if timeout and time_value > 2419200:
        return discord.Embed(
            description=":x: The duration you've specified is too long. The maximum timeout length you may set is 28 days.",
            color=config.ERROR_COLOR,
        )

    if slowmode and time_value > 21600:
        return discord.Embed(
            description=":x: The duration you've specified is too long. The maximum slowmode you may set is six hours.",
            color=config.ERROR_COLOR,
        )

    if purge and time_value > 1209600:
        return discord.Embed(
            description=":x: You may only purge messages within the last two weeks.",
            color=config.ERROR_COLOR,
        )

    if purge and time_value < 0:
        return discord.Embed(
            description=":x: You must specify a time period within which to purge messages.",
            color=config.ERROR_COLOR,
        )

    return time_value


def reverse_duration_calculator(seconds) -> str:
    if seconds < 0:
        raise ValueError("Duration cannot be negative.")

    time_units = [
        ("w", 604800),  # weeks
        ("d", 86400),  # days
        ("h", 3600),  # hours
        ("m", 60),  # minutes
        ("s", 1),  # seconds
    ]

    for unit, value in time_units:
        if seconds >= value:
            time_value = seconds // value
            return f"{time_value}{unit}"

    return f"{seconds}s"  # Default to seconds if less than 1 minute


# uptime checker
async def uptime_fetcher():
    global start_time
    current_time = datetime.datetime.now(datetime.UTC)
    uptime_duration = current_time - start_time

    # Format the uptime duration
    days, seconds = uptime_duration.days, uptime_duration.seconds
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    return uptime_str


async def fetch_random_emoji() -> str:
    emojis = await bot.fetch_application_emojis()
    if not emojis:
        return ""
    random_emoji = random.choice(emojis)
    return "" if not random_emoji else str(random_emoji) + " "


def get_ordinal(n: int) -> str:
    """Helper function to return the ordinal representation of a number."""
    suffix = ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"]
    if 10 <= n % 100 <= 20:
        return "th"
    else:
        return suffix[n % 10]


def randint_from_seed(
    seed: str | int, array: list | None = None, minimum: int = 1, maximum: int = 10
) -> int:
    """Based on a string (the 'seed'), produce a random integer. Apparently this is called a deterministic pseudorandom value."""
    if array:
        return array[random.Random(seed).randint(0, len(array) - 1)]
    else:
        return random.Random(seed).randint(minimum, maximum)
