import re
import nextcord
from nextcord.ext import commands
import aiohttp
from datetime import timedelta

# for those commands where you can mention a user either by mentioning them, using their ID, their username, or displayname
def extract_user_id(
    member_str: str, ctx: commands.Context or nextcord.Interaction
) -> nextcord.Member:
    match = re.match(r"<@!?(\d+)>", member_str)
    if match:
        user_id = int(match.group(1))
        return ctx.guild.get_member(user_id)

    if member_str.isdigit():
        user_id = int(member_str)
        return ctx.guild.get_member(user_id)

    member = nextcord.utils.get(
        ctx.guild.members, name=member_str
    ) or nextcord.utils.get(ctx.guild.members, display_name=member_str)

    return member

# for requesting data from APIs
async def request(url, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request("GET", url, *args, **kwargs) as response:
            return await response.json()

# for calculating durations, e.g. 1d, 2h, 5s, 34m
def duration_calculator(duration: str) -> int:
    pattern = r"(\d+)([d|h|m|s])"
    match = re.fullmatch(pattern, duration)
    if not match:
        return None

    time_value, time_unit = match.groups()
    time_value = int(time_value)

    if time_unit == "d":
        return time_value * 86400
    elif time_unit == "h":
        return time_value * 3600
    elif time_unit == "m":
        return time_value * 60
    elif time_unit == "s":
        return time_value * 1
    else:
        return None

# for checking perms of a command
def perms_check(
    member: nextcord.Member = None,
    *,
    ctx: commands.Context or nextcord.Interaction,
    author_check: bool = True,
    owner_check: bool = True,
    role_check: bool = True
):
    # Check if member is valid
    if not isinstance(member, nextcord.Member) or member is None:
        return False, "Member not found."

    # Toggle for self-action check
    if author_check and member == ctx.author:
        return False, "You cannot perform this action on yourself."

    # Toggle for server owner check
    if owner_check and member == ctx.guild.owner:
        return False, "You cannot perform this action on the server owner."

    # Toggle for role hierarchy checks
    if role_check:
        if member.top_role >= ctx.author.top_role:
            return False, "You cannot perform this action on someone with a higher or equal role than yours."

        if member.top_role >= ctx.guild.me.top_role:
            return False, "I can't perform this action on someone with a higher or equal role than mine."

    return True, None


# hax
def is_haxxor():
    async def predicate(ctx: commands.Context):
        haxxors = [961063229168164864, 992915737129787602]
        if await ctx.bot.is_owner(ctx.author) or ctx.author.id in haxxors:
            return True
        return False
    return commands.check(predicate)