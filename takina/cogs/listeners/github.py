import re
from typing import List, Optional
import aiohttp
import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View
from __main__ import EMBED_COLOR


# GitHub API helper function
async def fetch_github_data(url: str) -> Optional[dict]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    except aiohttp.ClientError:
        return None


# Regex patterns
GITHUB_URL_PATTERN = r"https:\/\/github.com\/([A-Za-z0-9-]+)\/([A-Za-z0-9-]+)(\/pull|\/issues)?(#|\/)(?P<pr_id>\d+)"
SHORT_PR_PATTERN = r"##(\d+)"


class GitHubPR:
    """Stores information about a GitHub PR/Issue."""

    def __init__(self, owner: str, repo: str, pr_id: str) -> None:
        self.owner = owner
        self.repo = repo
        self.pr_id = pr_id

    async def fetch_status(self) -> Optional[nextcord.Embed]:
        """Fetches and returns the status of a PR or Issue as a Discord Embed."""
        api_url = (
            f"https://api.github.com/repos/{self.owner}/{self.repo}/issues/{self.pr_id}"
        )
        data = await fetch_github_data(api_url)

        if not data:
            return nextcord.Embed(
                title="Error",
                description=f"Could not fetch information for PR/Issue #{self.pr_id}.",
                color=0xFF0037,
            )

        title = data.get("title", "No title available")
        html_url = data.get("html_url", "")
        state = data.get("state", "Unknown").capitalize()
        color = nextcord.Color.green() if state == "Open" else 0xFF0037

        if data.get("pull_request", {}).get("merged_at"):
            state = "Merged"
            color = nextcord.Color.purple()

        embed = nextcord.Embed(
            title=f"PR/Issue: {self.owner}/{self.repo}#{self.pr_id}",
            description=f"[{title}]({html_url})",
            color=color,
        )
        embed.add_field(name="Status", value=state, inline=True)
        return embed


class GitHub(commands.Cog):
    """Handles GitHub repository and PR/issue linking in Discord."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def handle_pr_embed(self, message: nextcord.Message, pr: GitHubPR):
        """Sends an embed with PR/issue status and a refresh button."""
        embed = await pr.fetch_status()
        if not embed:
            return

        # Add refresh button
        refresh_button = Button(
            label="Refresh Status", style=nextcord.ButtonStyle.primary
        )

        async def refresh_callback(interaction: nextcord.Interaction):
            new_embed = await pr.fetch_status()
            if new_embed:
                await interaction.response.edit_message(embed=new_embed)

        refresh_button.callback = refresh_callback

        view = View(timeout=None)
        view.add_item(refresh_button)
        await message.channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return

        content = message.content
        pr_list: List[GitHubPR] = []

        # Match full GitHub PR/Issue links
        full_match = re.search(GITHUB_URL_PATTERN, content)
        if full_match:
            await message.edit(suppress=True)
            pr_list.append(
                GitHubPR(
                    owner=full_match.group(1),
                    repo=full_match.group(2),
                    pr_id=full_match.group("pr_id"),
                )
            )

        # Match short PR reference for specific repo
        short_pr_match = re.search(SHORT_PR_PATTERN, content)
        if message.guild and message.guild.id == 830872854677422150:
            short_pr_match = re.search(SHORT_PR_PATTERN, content)
            if short_pr_match:
                pr_list.append(
                    GitHubPR(
                        owner="is-a-dev", repo="register", pr_id=short_pr_match.group(1)
                    )
                )
                pass

        # If a PR/Issue was detected, handle the embed
        if pr_list:
            await self.handle_pr_embed(message, pr_list[0])
            return

        # Match repository references 'repo:owner/repo'
        repo_match = re.search(r"repo:([A-Za-z1-9-]+)/([A-Za-z1-9-]+)", content)
        if repo_match:
            await self.handle_repo_embed(
                message, repo_match.group(1), repo_match.group(2)
            )

    async def handle_repo_embed(self, message: nextcord.Message, owner: str, repo: str):
        """Fetches and sends an embed with repository information."""
        repo_url = f"https://api.github.com/repos/{owner}/{repo}"
        repo_data = await fetch_github_data(repo_url)
        if not repo_data:
            await message.channel.send(
                f"Error fetching repository {owner}/{repo}. It may not exist."
            )
            return

        # Build and send the repository embed
        repo_name = repo_data.get("full_name", f"[{owner}/{repo}]")
        description = repo_data.get("description", "No description available.")
        stars = repo_data.get("stargazers_count", 0)
        forks = repo_data.get("forks_count", 0)
        avatar_url = repo_data.get("owner", {}).get("avatar_url", "")
        repo_html_url = repo_data.get("html_url", f"https://github.com/{owner}/{repo}")

        embed = nextcord.Embed(
            title=f"{repo_name}",
            description=f"{description}",
            url=repo_html_url,
            color=EMBED_COLOR,
        )
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="Stars", value=str(stars), inline=True)
        embed.add_field(name="Forks", value=str(forks), inline=True)

        await message.channel.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(GitHub(bot))
