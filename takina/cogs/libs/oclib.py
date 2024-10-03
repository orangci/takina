import re
import nextcord
from nextcord.ext import commands
import aiohttp
import datetime
from nextcord.ui import Button, View
import os

EMBED_COLOR = os.getenv("EMBED_COLOR")

start_time = datetime.datetime.utcnow()


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
    role_check: bool = True,
):
    # Check if member is valid
    if not isinstance(member, nextcord.Member) or member is None:
        return False, "Member not found."

    if isinstance(ctx, commands.Context):
        author = ctx.author
    elif isinstance(ctx, nextcord.Interaction):
        author = ctx.user
    else:
        return False, "Invalid context."

    # Toggle for self-action check
    if author_check and member == author:
        return False, "You cannot perform this action on yourself."

    # Toggle for server owner check
    if owner_check and member == ctx.guild.owner:
        return False, "You cannot perform this action on the server owner."

    # Toggle for role hierarchy checks
    if role_check:
        if member.top_role >= author.top_role:
            return (
                False,
                "You cannot perform this action on someone with a higher or equal role than yours.",
            )

        if member.top_role >= ctx.guild.me.top_role:
            return (
                False,
                "I can't perform this action on someone with a higher or equal role than mine.",
            )

    return True, None


# uptime checker
async def uptime_fetcher():
    global start_time
    current_time = datetime.datetime.utcnow()
    uptime_duration = current_time - start_time

    # Format the uptime duration
    days, seconds = uptime_duration.days, uptime_duration.seconds
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    return uptime_str


# confirmation embed for moderation things
class ConfirmationView(View):
    def __init__(
        self,
        ctx: commands.Context or nextcord.Interaction,
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

    # Confirm
    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green)
    async def confirm(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
        self.result = True
        await interaction.message.delete()
        self.stop()

    # Cancel
    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red)
    async def cancel(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
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
            return False, "Invalid context."

        await self.wait()

        if self.result is None:
            for child in self.children:
                child.disabled = True
            timeout_embed = nextcord.Embed(
                description=f"{self.action.capitalize()} cancelled; timed out.",
                color=EMBED_COLOR,
            )
            await self.message.edit(embed=timeout_embed, view=None)

        return self.result
