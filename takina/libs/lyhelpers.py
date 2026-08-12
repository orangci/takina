# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from __main__ import bot, start_time
from takina.libs import lyerrors
from discord.ext import commands
from takina import config
import datetime
import discord
import aiohttp
import random
import re


# for requesting data from APIs
async def request(url: str, method: str = "GET", headers: dict | None = None, *args, **kwargs):
    user_agent_header = {"User-Agent": config.USER_AGENT}
    kwargs["headers"] = user_agent_header | (headers or {})

    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, *args, **kwargs) as response:
            if response.status == 404:
                return False

            if response.status >= 400:
                raise lyerrors.TakinaError(
                    f"Error [{response.status}](https://http.cat/{response.status}.png): Failed to reach the requested resource."
                )

            return await response.json()


async def post(url, headers=None, *args, **kwargs):
    if headers:
        kwargs["headers"] = headers

    async with aiohttp.ClientSession() as session:
        async with session.post(url, *args, **kwargs) as response:
            return await response.json()


# for calculating durations, e.g. 1d, 2h, 5s, 34m
def duration_calculator(duration: str, slowmode=False, timeout=False, purge=False) -> int:
    pattern = r"(\d+)([smhdw])"
    match = re.fullmatch(pattern, duration)

    if not match:
        raise lyerrors.TakinaUserInputError("Invalid duration format. Use <number>[s|m|h|d|w].")

    time_value, time_unit = match.groups()
    time_value = int(time_value)

    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "y": 31557600}
    time_value *= multipliers[time_unit]

    return time_value


def reverse_duration_calculator(seconds) -> str:
    if seconds < 0:
        raise ValueError("Duration cannot be negative.")

    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "y": 31557600}

    for unit, value in time_units.items():
        if seconds >= value:
            return f"{seconds // value}{unit}"

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


def chunked[T](items: list[T], size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


async def permissions_check(
    ctx: commands.Context,
    member: discord.Member,
    author_check: bool = True,
    owner_check: bool = False,
    role_check: bool = True,
) -> None:
    if not isinstance(ctx.author, discord.Member) or not ctx.guild:
        raise lyerrors.TakinaError("This command can only be used in a server.")

    if author_check and member == ctx.author:
        raise lyerrors.TakinaPermissionError("You cannot perform this action on yourself.")

    if owner_check and member == ctx.guild.owner:
        raise lyerrors.TakinaPermissionError(
            f"You cannot perform this action on the server owner ({member.mention})."
        )

    if role_check and member.top_role >= ctx.author.top_role:
        raise lyerrors.TakinaPermissionError(
            f"You cannot perform this action on a member ({member.mention}) with a role that is higher than or equal to your own."
        )

    if role_check and ctx.guild.me and member.top_role >= ctx.guild.me.top_role:
        raise lyerrors.TakinaBotPermissionError(
            f"I cannot perform this action on a member ({member.mention}) with a role that is higher than or equal to my own."
        )
