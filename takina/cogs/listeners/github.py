# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import re
import nextcord
from nextcord.ext import commands
from nextcord import ui
from config import *
from typing import Optional
from ..libs.oclib import request
from datetime import datetime

GITHUB_BASE_URL = "https://api.github.com"

REPO_PATTERN = re.compile(r"repo:([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")
PR_ISSUE_PATTERN = re.compile(r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)#(\d+)")


def format_timestamp(iso_timestamp: str) -> str:
    dt = datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    day_suffix = (
        "th"
        if 11 <= dt.day <= 13
        else {1: "st", 2: "nd", 3: "rd"}.get(dt.day % 10, "th")
    )
    formatted_time = dt.strftime(f"%B {dt.day}{day_suffix}, %Y at %H:%M")
    return formatted_time


class GitHubCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_github_data(self, url: str) -> Optional[dict]:
        """Fetch JSON data from the GitHub API."""
        try:
            return await request(url)
        except Exception as e:
            print(f"Error fetching GitHub data: {e}")
            return None

    def build_repo_embed(self, repo_data: dict) -> nextcord.Embed:
        """Build an embed for repository details."""
        return (
            nextcord.Embed(
                title=f"{repo_data['full_name']} - GitHub Repository",
                description=repo_data.get("description", "No description available."),
                color=EMBED_COLOR,
                url=repo_data["html_url"],
            )
            .add_field(name="Stars", value=repo_data["stargazers_count"])
            .add_field(name="Forks", value=repo_data["forks_count"])
            .set_thumbnail(url=repo_data["owner"]["avatar_url"])
        )

    def build_pr_issue_embed(self, pr_data: dict, is_issue: bool) -> nextcord.Embed:
        """Build an embed for PR/Issue details."""
        color = (
            nextcord.Color.green()
            if pr_data["state"] == "open"
            else nextcord.Color.red()
        )
        color = (
            nextcord.Color.purple()
            if pr_data.get("pull_request", {}).get("merged_at")
            else color
        )
        updated_at_formatted = format_timestamp(pr_data["updated_at"])
        return (
            nextcord.Embed(
                title=f"{pr_data['title']} - {'Issue' if is_issue else 'Pull Request'} #{pr_data['number']}",
                description=pr_data.get("body", "No description available.")[:500],
                color=color,
                url=pr_data["html_url"],
            )
            .add_field(name="Status", value=pr_data["state"].capitalize())
            .add_field(name="Comments", value=pr_data["comments"])
            .set_footer(text=f"Last updated on {updated_at_formatted}")
        )

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        """Detect and handle repository or PR/Issue mentions in messages."""
        if message.author.bot:
            return

        content = message.content

        # Check for repository reference
        repo_match = REPO_PATTERN.search(content)
        if repo_match:
            await message.edit(suppress=True)
            owner, repo_name = repo_match.groups()
            repo_data = await self.fetch_github_data(
                f"{GITHUB_BASE_URL}/repos/{owner}/{repo_name}"
            )
            if repo_data:
                await message.channel.send(embed=self.build_repo_embed(repo_data))
            return  # Only process the first match in the message

        # Check for PR/issue reference
        pr_issue_match = PR_ISSUE_PATTERN.search(content)
        if pr_issue_match:
            owner, repo_name, pr_issue_number = pr_issue_match.groups()
            url = (
                f"{GITHUB_BASE_URL}/repos/{owner}/{repo_name}/issues/{pr_issue_number}"
            )
            pr_issue_data = await self.fetch_github_data(url)
            if pr_issue_data:
                is_issue = "pull_request" not in pr_issue_data
                embed = self.build_pr_issue_embed(pr_issue_data, is_issue)
                view = self.RefreshView(self, url, is_issue)
                await message.channel.send(embed=embed, view=view)

    class RefreshView(ui.View):
        def __init__(self, cog, url, is_issue):
            super().__init__()
            self.cog = cog
            self.url = url
            self.is_issue = is_issue

        @ui.button(label="Refresh Status", style=nextcord.ButtonStyle.primary)
        async def refresh(self, button: ui.Button, interaction: nextcord.Interaction):
            pr_issue_data = await self.cog.fetch_github_data(self.url)
            if pr_issue_data:
                embed = self.cog.build_pr_issue_embed(pr_issue_data, self.is_issue)
                await interaction.response.edit_message(embed=embed)


def setup(bot):
    bot.add_cog(GitHubCog(bot))
