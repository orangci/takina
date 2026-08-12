# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyhelpers
from discord.ext import commands
from datetime import datetime
from takina import config
import discord
import re


class GitHub(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot
        self.PR_ISSUE_PATTERN = re.compile(r"\b([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)#(\d+)\b")
        self.REPO_PATTERN = re.compile(
            r"\b(?:repo:|gh:|github:)([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)\b", re.IGNORECASE
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        # check for repository references first
        repo_match = self.REPO_PATTERN.search(message.content)
        if repo_match:
            owner, repo_name = repo_match.groups()
            repo_data = await lyhelpers.request(f"https://api.github.com/repos/{owner}/{repo_name}")

            if not repo_data:
                return

            embed = discord.Embed(
                title=repo_data["full_name"],
                description=repo_data.get("description") or "No description provided.",
                url=repo_data["html_url"],
                colour=config.EMBED_COLOUR,
            )

            embed.add_field(
                name="Stars",
                value=f"[{repo_data['stargazers_count']}](https://github.com/{repo_data['full_name']}/stargazers)",
                inline=True,
            )
            embed.add_field(
                name="Forks",
                value=f"[{repo_data['forks_count']}](https://github.com/{repo_data['full_name']}/forks)",
                inline=True,
            )
            embed.add_field(
                name="Open issues",
                value=f"[{repo_data['open_issues_count']:,}](https://github.com/{repo_data['full_name']}/issues)",
                inline=True,
            )

            embed.set_thumbnail(url=repo_data["owner"]["avatar_url"])
            await message.channel.send(embed=embed)
            return

        # check for issue / pull request references
        pr_issue_match = self.PR_ISSUE_PATTERN.search(message.content)
        if not pr_issue_match:
            return

        owner, repo_name, number = pr_issue_match.groups()
        data = await lyhelpers.request(
            f"https://api.github.com/repos/{owner}/{repo_name}/issues/{number}"
        )

        if not data:
            return

        is_pr = "pull_request" in data

        if is_pr:
            status = "open" if data["state"] == "open" else "closed"

            if data.get("pull_request", {}).get("merged_at"):
                status = "merged"

            embed_title = f"Pull Request #{data['number']}: {data['title']}"
        else:
            status = data["state"]
            embed_title = f"Issue #{data['number']}: {data['title']}"

        embed = discord.Embed(
            title=embed_title,
            description=data.get("body") or "No description provided.",
            url=data["html_url"],
            colour=config.EMBED_COLOUR,
        )

        embed.add_field(
            name="Repository",
            value=f"[{data['repository_url'].rsplit('/', 2)[-2]}/{data['repository_url'].rsplit('/', 1)[-1]}]({data['repository_url']})",
            inline=True,
        )
        embed.add_field(name="Status", value=status.capitalize(), inline=True)
        embed.add_field(name="Comments", value=f"{data['comments']:,}", inline=True)

        if data.get("user"):
            embed.set_author(name=data["user"]["login"], icon_url=data["user"]["avatar_url"])

        timestamp = datetime.fromisoformat(data["updated_at"])
        formatted_timestamp = timestamp.strftime(
            f"%B {timestamp.day}{lyhelpers.get_ordinal(timestamp.day)}, %Y at %H:%M UTC"
        )
        embed.set_footer(text=f"Last updated {formatted_timestamp}")
        await message.channel.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GitHub(bot))
