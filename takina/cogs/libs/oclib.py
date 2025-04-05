from nextcord.ext import commands
from nextcord.ui import View
import os, random, re, nextcord, aiohttp, datetime
from config import *
from __main__ import start_time, bot


# for those commands where you can mention a user either by mentioning them, using their ID, their username, or displayname
def extract_user_id(
    member_str: str, ctx: commands.Context | nextcord.Interaction
) -> nextcord.Member:
    match = re.match(r"<@!?(\d+)>", member_str)
    if match:
        user_id = int(match.group(1))
        return ctx.guild.get_member(user_id)

    if member_str.isdigit():
        user_id = int(member_str)
        return ctx.guild.get_member(user_id)

    member = nextcord.utils.get(
        ctx.guild.members,
        name=member_str,
    ) or nextcord.utils.get(ctx.guild.members, display_name=member_str)
    if member:
        return member

    partial_matches = [
        member
        for member in ctx.guild.members
        if member.display_name.lower().startswith(member_str.lower())
        or member.display_name.lower().find(member_str.lower()) != -1
    ]
    if partial_matches:
        if len(partial_matches) == 1:
            return partial_matches[0]
        else:
            member = None

    if not member:
        error_embed = nextcord.Embed(
            color=ERROR_COLOR,
        )
        error_embed.description = ":x: User not found. Please provide a valid username, display name, mention, or user ID."
        return error_embed


# for requesting data from APIs
async def request(url, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request("GET", url, *args, **kwargs) as response:
            return await response.json()


# for calculating durations, e.g. 1d, 2h, 5s, 34m
def duration_calculator(
    duration: str, slowmode=False, timeout=False, purge=False
) -> int:
    pattern = r"(\d+)([s|m|h|d|w])"
    match = re.fullmatch(pattern, duration)
    error_embed = nextcord.Embed(
        color=ERROR_COLOR,
    )
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
        return nextcord.Embed(
            description=":x: The duration you've specified is too long. The maximum timeout length you may set is 28 days.",
            color=ERROR_COLOR,
        )

    if slowmode and time_value > 21600:
        return nextcord.Embed(
            description=":x: The duration you've specified is too long. The maximum slowmode you may set is six hours.",
            color=ERROR_COLOR,
        )

    if purge and time_value > 1209600:
        return nextcord.Embed(
            description=":x: You may only purge messages within the last two weeks.",
            color=ERROR_COLOR,
        )

    if purge and time_value < 0:
        return nextcord.Embed(
            description=":x: You must specify a time period within which to purge messages.",
            color=ERROR_COLOR,
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


# for checking perms of a command
def perms_check(
    member: nextcord.Member = None,
    *,
    ctx: commands.Context | nextcord.Interaction,
    author_check: bool = True,
    owner_check: bool = False,
    role_check: bool = True,
):
    # Check if member is valid
    if not isinstance(member, nextcord.Member) or member is None:
        return False, nextcord.Embed(
            description=":x: Member not found.", color=ERROR_COLOR
        )

    if isinstance(ctx, commands.Context):
        author = ctx.author
    elif isinstance(ctx, nextcord.Interaction):
        author = ctx.user
    else:
        return False, nextcord.Embed(
            description=":x: Invalid context.", color=ERROR_COLOR
        )

    # Toggle for self-action check
    if author_check and member == author:
        return False, nextcord.Embed(
            description=":x: You cannot perform this action on yourself.",
            color=ERROR_COLOR,
        )

    # Toggle for server owner check
    if owner_check and member == ctx.guild.owner:
        return False, nextcord.Embed(
            description=":x: You cannot perform this action on the server owner.",
            color=ERROR_COLOR,
        )

    # Toggle for role hierarchy checks
    if role_check:
        if member.top_role >= author.top_role:
            return (
                False,
                nextcord.Embed(
                    description=":x: You cannot perform this action on someone with a higher or equal role than yours.",
                    color=ERROR_COLOR,
                ),
            )

        if member.top_role >= ctx.guild.me.top_role:
            return (
                False,
                nextcord.Embed(
                    description=":x: I cannot perform this action on someone with a higher or equal role than mine.",
                    color=ERROR_COLOR,
                ),
            )

    return True, None


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


class ConfirmationView(View):
    def __init__(
        self,
        ctx: commands.Context | nextcord.Interaction,
        member: nextcord.Member,
        action: str,
        reason: str,
        duration: str = None,
    ):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.member = member
        self.action = action
        self.reason = reason
        self.duration = duration
        self.result = None
        self.message = None
        self.initiating_user = (
            ctx.author if isinstance(ctx, commands.Context) else ctx.user
        )

    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green)
    async def confirm(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
        if interaction.user != self.initiating_user:
            return

        self.result = True
        await interaction.message.delete()
        self.stop()

    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red)
    async def cancel(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
        if interaction.user != self.initiating_user:
            return

        self.result = False
        await self.disable_buttons(interaction)
        self.stop()

    async def disable_buttons(self, interaction: nextcord.Interaction):
        if self.result:
            new_embed = nextcord.Embed(
                description=f"{self.action.capitalize()} confirmed.", color=EMBED_COLOR
            )
        else:
            new_embed = nextcord.Embed(
                description=f"{self.action.capitalize()} cancelled.", color=EMBED_COLOR
            )

        await interaction.message.edit(embed=new_embed, view=None)

    async def prompt(self):
        embed = nextcord.Embed(
            title=f"Confirm {self.action.capitalize()}",
            description=f"Are you sure you want to {self.action} {self.member.mention}?",
            color=EMBED_COLOR,
        )
        if isinstance(self.ctx, commands.Context):
            self.message = await self.ctx.reply(
                embed=embed, view=self, mention_author=False
            )
        elif isinstance(self.ctx, nextcord.Interaction):
            self.message = await self.ctx.send(embed=embed, view=self)
        else:
            return False, ":x: Invalid context."

        await self.wait()

        if self.result is None:
            for child in self.children:
                child.disabled = True
            timeout_embed = nextcord.Embed(
                description=f"{self.action.capitalize()} cancelled; timed out.",
                color=EMBED_COLOR,
            )
            self.result = False
            await self.message.edit(embed=timeout_embed, view=None)

        return self.result


async def fetch_random_emoji() -> str:
    random_emoji = random.choice(await bot.fetch_application_emojis())
    return "" if not random_emoji else str(random_emoji) + " "
