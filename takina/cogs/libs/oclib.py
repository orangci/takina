import re
import nextcord
from nextcord.ext import commands
import aiohttp


def extract_user_id(member_str: str, ctx: commands.Context) -> nextcord.Member:
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


async def request(url, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request("GET", url, *args, **kwargs) as response:
            return await response.json()
