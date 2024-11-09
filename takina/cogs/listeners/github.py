import re
import aiohttp
import nextcord
from typing import Optional
from nextcord.ext import commands
from nextcord.ui import Button, View
from __main__ import EMBED_COLOR

# GitHub API Base URL
GITHUB_API_BASE_URL = "https://api.github.com/repos"

# Updated patterns for GitHub references to include underscores, dots, and numbers
REPO_PATTERN = r"repo:([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)"
ISSUE_PR_PATTERN = r"([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)#(\d+)"

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
    """Helper class to build embeds for GitHub PRs, Issues, and Repos."""

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

    @staticmethod
    def create_repo_embed(data: dict) -> nextcord.Embed:
        """Create an embed for a GitHub repository."""
        repo_name = data.get("full_name", "Unknown Repository")
        description = data.get("description", "No description available.")
        stars = data.get("stargazers_count", 0)
        forks = data.get("forks_count", 0)
        avatar_url = data["owner"]["avatar_url"]

        embed = nextcord.Embed(
            title=repo_name,
            description=description,
            url=data["html_url"],
            color=EMBED_COLOR,
        )
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="Stars", value=stars, inline=True)
        embed.add_field(name="Forks", value=forks, inline=True)
        return embed

class GitHub(commands.Cog):
    """Cog to interact with GitHub links, fetching information on repositories, PRs, and Issues."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def handle_pr_issue_embed(self, message: nextcord.Message, owner: str, repo: str, issue_id: int):
        """Fetches and sends an embed with PR/issue status and a refresh button."""
        api_url = f"{GITHUB_API_BASE_URL}/{owner}/{repo}/issues/{issue_id}"
        data = await fetch_github_data(api_url)

        if not data:
            await message.channel.send(
                embed=nextcord.Embed(
                    description=f":x: Could not fetch information for {owner}/{repo}#{issue_id}.",
                    color=0xFF0037,
                )
            )
            return

        embed = GitHubEmbedBuilder.create_pr_issue_embed(data, owner, repo)
        
        # Add a refresh button to update the PR/issue status
        view = View(timeout=None)
        refresh_button = Button(label="Refresh Status", style=nextcord.ButtonStyle.primary)

        async def refresh_callback(interaction: nextcord.Interaction):
            updated_data = await fetch_github_data(api_url)
            if updated_data:
                new_embed = GitHubEmbedBuilder.create_pr_issue_embed(updated_data, owner, repo)
                await interaction.response.edit_message(embed=new_embed)

        refresh_button.callback = refresh_callback
        view.add_item(refresh_button)

        await message.channel.send(embed=embed, view=view)

    async def handle_repo_embed(self, message: nextcord.Message, owner: str, repo: str):
        """Fetches and sends an embed with repository information."""
        api_url = f"{GITHUB_API_BASE_URL}/{owner}/{repo}"
        data = await fetch_github_data(api_url)

        if not data:
            await message.channel.send(
                embed=nextcord.Embed(
                    description=f":x: Could not fetch repository information for {owner}/{repo}.",
                    color=0xFF0037,
                )
            )
            return

        embed = GitHubEmbedBuilder.create_repo_embed(data)
        await message.channel.send(embed=embed)

@commands.Cog.listener()
async def on_message(self, message: nextcord.Message):
    if message.author.bot:
        return

    content = message.content
    
    # Check for PR/Issue link pattern first
    pr_issue_match = re.search(ISSUE_PR_PATTERN, content)
    if pr_issue_match:
        logging.debug("PR/Issue pattern matched.")
        owner, repo, issue_id = pr_issue_match.groups()
        await self.handle_pr_issue_embed(message, owner, repo, int(issue_id))
        return  # Stop after first match for simplicity

    # Check for repository link pattern
    repo_match = re.search(REPO_PATTERN, content)
    if repo_match:
        logging.debug("Repository pattern matched.")
        owner, repo = repo_match.groups()
        await self.handle_repo_embed(message, owner, repo)
        return  # Stop after first match for simplicity

def setup(bot: commands.Bot):
    bot.add_cog(GitHub(bot))
