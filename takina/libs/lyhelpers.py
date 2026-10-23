# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from collections.abc import Iterator
from takina.libs import lyerrors
from discord.ext import commands
from takina import config
from typing import TYPE_CHECKING, Any
import datetime
import discord
import aiohttp
import random
import re

if TYPE_CHECKING:
    from takina.__main__ import Bot

_bot: "Bot | None" = None
_application_emojis: list[discord.Emoji] | None = None


def setup(bot: "Bot") -> None:
    # called by __main__ at startup, and again by .rx after reloading this module
    global _bot
    _bot = bot


def get_bot() -> "Bot":
    if _bot is None:
        raise RuntimeError("lyhelpers.setup(bot) has not been called.")

    return _bot


# for requesting data from APIs
async def request(
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    disable_json: bool = False,
    *args,
    not_found: str = "That could not be found.",
    with_headers: bool = False,
    **kwargs,
) -> Any:
    """
    Fetch a url, returning its json (or text with `disable_json`), and with `with_headers`,
    a `(body, headers)` tuple for apis that put counts or pagination in headers.
    """
    bot = get_bot()
    if not bot.http_session:
        raise RuntimeError("Client HTTP session has not been initialised.")

    user_agent_header = {"User-Agent": config.USER_AGENT}
    kwargs["headers"] = user_agent_header | (headers or {})
    # without a timeout, a hung api leaves the command thinking forever
    kwargs.setdefault("timeout", aiohttp.ClientTimeout(total=10))

    async with bot.http_session.request(method, url, *args, **kwargs) as response:
        if response.status == 404:
            raise lyerrors.TakinaNotFoundError(not_found)

        if not response.ok:
            raise lyerrors.TakinaError(
                f"Error [{response.status}](https://http.cat/{response.status}.png): {response.reason}."
            )

        if disable_json:
            body = await response.text()
        else:
            try:
                body = await response.json()
            except aiohttp.ContentTypeError as error:
                raise lyerrors.TakinaError(
                    "The service returned something other than JSON."
                ) from error

        return (body, response.headers) if with_headers else body


# largest first, which reverse_duration_calculator relies on
DURATION_UNITS = {"y": 31557600, "w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1}


def duration_calculator(duration: str) -> int:
    # accepts "90m", "1h30m" and "1h 30m", the last being what reverse_duration_calculator prints
    compact = duration.replace(" ", "").lower()
    parts = re.findall(r"(\d+)([ywdhms])", compact)

    if not parts or "".join(amount + unit for amount, unit in parts) != compact:
        raise lyerrors.TakinaUserInputError(
            "Invalid duration format. Use something like `1h30m`, with the units s, m, h, d, w and y."
        )

    return sum(int(amount) * DURATION_UNITS[unit] for amount, unit in parts)


def reverse_duration_calculator(seconds: int) -> str:
    if seconds < 0:
        raise ValueError("Duration cannot be negative.")

    if seconds == 0:
        return "0s"

    # largest first, so 5400 becomes "1h 30m" rather than "5400s"
    parts: list[str] = []
    for unit, value in DURATION_UNITS.items():
        amount, seconds = divmod(seconds, value)
        if amount:
            parts.append(f"{amount}{unit}")

    return " ".join(parts)


# uptime checker
def uptime_fetcher() -> str:
    current_time = datetime.datetime.now(datetime.UTC)
    uptime_duration = current_time - get_bot().start_time

    # Format the uptime duration
    days, seconds = uptime_duration.days, uptime_duration.seconds
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    return uptime_str


async def fetch_random_emoji() -> str:
    # fetched once; new application emojis show up after a restart or .rx
    global _application_emojis
    if _application_emojis is None:
        _application_emojis = await get_bot().fetch_application_emojis()

    if not _application_emojis:
        return ""

    return f"{random.choice(_application_emojis)} "


def get_ordinal(n: int) -> str:
    """Helper function to return the ordinal representation of a number."""
    suffix = ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"]
    if 11 <= n % 100 <= 13:
        return "th"
    else:
        return suffix[n % 10]


def randint_from_seed(
    seed: str | int, array: list | None = None, minimum: int = 1, maximum: int = 10
) -> Any:
    """Based on a string (the 'seed'), produce a random integer. Apparently this is called a deterministic pseudorandom value."""
    if array:
        return array[random.Random(seed).randint(0, len(array) - 1)]
    else:
        return random.Random(seed).randint(minimum, maximum)


def chunked[T](items: list[T], size: int) -> Iterator[list[T]]:
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

    # the owner outranks everyone in discord regardless of roles
    if role_check and ctx.author != ctx.guild.owner and member.top_role >= ctx.author.top_role:
        raise lyerrors.TakinaPermissionError(
            f"You cannot perform this action on a member ({member.mention}) with a role that is higher than or equal to your own."
        )

    if role_check and ctx.guild.me and member.top_role >= ctx.guild.me.top_role:
        raise lyerrors.TakinaBotPermissionError(
            f"I cannot perform this action on a member ({member.mention}) with a role that is higher than or equal to my own."
        )


async def invoke_moved(ctx: commands.Context, qualified_name: str, **kwargs: Any) -> None:
    """
    Run a command from its new home, so the old one keeps working as an alias.

    Example:
        await lyhelpers.invoke_moved(ctx, "settings guild honeypot", channel=channel)
    """
    command = ctx.bot.get_command(qualified_name)
    if command is None:
        raise lyerrors.TakinaDisabledError(f"`{qualified_name}` is not available right now.")

    # invoke skips the new command's checks, so the old command keeps its own
    await ctx.invoke(command, **kwargs)


def truncate(text: str, limit: int) -> str:
    # discord rejects oversized embeds outright, so long text is cut instead
    if len(text) <= limit:
        return text

    return text[: limit - 1].rstrip() + "…"


async def fetch_member_count(guild: discord.Guild) -> int:
    # without the members intent, guild.member_count is only as fresh as the last connect
    fetched = await get_bot().fetch_guild(guild.id, with_counts=True)
    return fetched.approximate_member_count or guild.member_count or 0
