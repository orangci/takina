import re
import nextcord
from nextcord.ext import commands
import aiohttp
from typing import Optional
from nextcord.ui import Button, View
from .lib import *

GITHUB_URL_PATTERN = r"https:\/\/github.com\/([A-Za-z0-9-]+)\/([A-Za-z0-9-]+)(\/pull|\/issues)?(#|\/)(?P<pr_id>\d+)"
SHORT_PR_PATTERN = r"##(\d+)"


class PRChannelMessageCleaner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.guild.id != SERVER_ID:
            return
        if message.author.bot:
            return

        if message.channel.id != PR_CHANNEL_ID:
            return

        if any(role.id == STAFF_ROLE_ID for role in message.author.roles):
            return

        if re.search(GITHUB_URL_PATTERN, message.content) or re.search(
            SHORT_PR_PATTERN, message.content
        ):
            return

        await message.delete()


# GitHub API Base URL
GITHUB_API_BASE_URL = "https://api.github.com/repos"

# Repository details (specifically for is-a-dev/register repo)
OWNER = "is-a-dev"
REPO = "register"

# Pattern for ##<number> (e.g., ##123 or ##1234)
ISSUE_PR_PATTERN = r"##(\d+)"


# Utility to fetch GitHub data
async def fetch_github_data(url: str) -> Optional[dict]:
    """Fetch data from GitHub API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
    except aiohttp.ClientError:
        pass
    return None


class GitHubEmbedBuilder:
    """Helper class to build embeds for GitHub PRs, Issues."""

    @staticmethod
    def create_pr_issue_embed(data: dict, owner: str, repo: str) -> nextcord.Embed:
        """Create an embed for a GitHub PR/Issue."""
        pr_id = data["number"]
        title = data["title"]
        html_url = data["html_url"]
        state = data["state"].capitalize()
        color = nextcord.Color.green() if state == "Open" else nextcord.Color.red()
        if data.get("pull_request", {}).get("merged_at"):
            state = "Merged"
            color = nextcord.Color.purple()

        embed = nextcord.Embed(
            title=f"{owner}/{repo}#{pr_id}",
            description=f"[{title}]({html_url})",
            color=color,
        )
        embed.add_field(name="Status", value=state, inline=True)
        return embed


class GitHubTwo(commands.Cog):
    """Cog to interact with GitHub PRs and Issues, fetching information for is-a-dev/register repo."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def handle_pr_issue_embed(self, message: nextcord.Message, issue_id: int):
        """Fetches and sends an embed for PR/issue in the is-a-dev/register repo."""
        api_url = f"{GITHUB_API_BASE_URL}/{OWNER}/{REPO}/issues/{issue_id}"
        data = await fetch_github_data(api_url)

        if not data:
            await message.channel.send(
                embed=nextcord.Embed(
                    title="Error",
                    description=f"Could not fetch information for {OWNER}/{REPO}#{issue_id}.",
                    color=ERROR_COLOR,
                )
            )
            return

        embed = GitHubEmbedBuilder.create_pr_issue_embed(data, OWNER, REPO)

        # Add a refresh button to update the PR/issue status
        view = View(timeout=None)
        refresh_button = Button(
            label="Refresh Status", style=nextcord.ButtonStyle.primary
        )

        async def refresh_callback(interaction: nextcord.Interaction):
            updated_data = await fetch_github_data(api_url)
            if updated_data:
                new_embed = GitHubEmbedBuilder.create_pr_issue_embed(
                    updated_data, OWNER, REPO
                )
                await interaction.response.edit_message(embed=new_embed)

        refresh_button.callback = refresh_callback
        view.add_item(refresh_button)

        await message.channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.guild.id != SERVER_ID:
            return
        if message.author.bot:
            return

        content = message.content
        match = re.search(ISSUE_PR_PATTERN, content)
        if match:
            issue_id = match.group(1)
            await message.edit(suppress=True)
            await self.handle_pr_issue_embed(message, int(issue_id))


def setup(bot: commands.Bot):
    bot.add_cog(GitHubTwo(bot))
    bot.add_cog(PRChannelMessageCleaner(bot))
