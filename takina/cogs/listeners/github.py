# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyhelpers, lyerrors
from discord.ext import commands
from datetime import datetime
from takina import config
from typing import Any
import logging
import discord
import aiohttp
import time
import re

logger = logging.getLogger("takina.github")

# github owners are letters, digits and hyphens; repositories may also use . and _
# the lookbehind keeps urls and paths such as example.com/path#1 from matching
OWNER = r"(?<![\w./:-])([A-Za-z0-9-]{1,39})"
REPO = r"([A-Za-z0-9_.-]{1,100})"
PR_ISSUE_PATTERN = re.compile(rf"{OWNER}/{REPO}#(\d+)\b")
REPO_PATTERN = re.compile(rf"\b(?:repo|gh|github):([A-Za-z0-9-]{{1,39}})/{REPO}\b", re.IGNORECASE)

CACHE_SECONDS = 5 * 60
MAX_CACHE_ENTRIES = 500
MAX_BODY_LENGTH = 1000


class GitHub(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot
        # url to (fetched at, response), so a busy channel cannot burn the rate limit
        self._cache: dict[str, tuple[float, Any]] = {}

    async def fetch(self, url: str) -> Any | None:
        now = time.monotonic()
        if (cached := self._cache.get(url)) and now - cached[0] < CACHE_SECONDS:
            return cached[1]

        headers = {"Accept": "application/vnd.github+json"}
        if config.GITHUB_AUTH_TOKEN:
            headers["Authorization"] = f"Bearer {config.GITHUB_AUTH_TOKEN}"

        try:
            data = await lyhelpers.request(url, headers=headers)
        except lyerrors.TakinaNotFoundError:
            # a pattern match is not necessarily a real repository
            data = None
        except (lyerrors.TakinaError, aiohttp.ClientError, TimeoutError) as error:
            # rate limits and outages; a preview is not worth an error message
            logger.warning(f"github request to {url} failed: {error}")
            return None

        if len(self._cache) >= MAX_CACHE_ENTRIES:
            self._cache = {
                key: entry for key, entry in self._cache.items() if now - entry[0] < CACHE_SECONDS
            }

        self._cache[url] = (now, data)
        return data

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        repo_match = REPO_PATTERN.search(message.content)
        pr_issue_match = None if repo_match else PR_ISSUE_PATTERN.search(message.content)
        match = repo_match or pr_issue_match
        if match is None or match.group(2) in (".", ".."):
            return

        if repo_match:
            embed = await self.repo_embed(*repo_match.groups())
        else:
            embed = await self.issue_embed(*match.groups())

        if embed is not None:
            await message.reply(embed=embed, mention_author=False)

    async def repo_embed(self, owner: str, repo_name: str) -> discord.Embed | None:
        repo_data = await self.fetch(f"https://api.github.com/repos/{owner}/{repo_name}")
        if not repo_data:
            return None

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
        return embed

    async def issue_embed(self, owner: str, repo_name: str, number: str) -> discord.Embed | None:
        data = await self.fetch(f"https://api.github.com/repos/{owner}/{repo_name}/issues/{number}")
        if not data:
            return None

        is_pr = "pull_request" in data

        if is_pr:
            status = "open" if data["state"] == "open" else "closed"

            if data.get("pull_request", {}).get("merged_at"):
                status = "merged"

            embed_title = f"Pull Request #{data['number']}: {data['title']}"
        else:
            status = data["state"]
            embed_title = f"Issue #{data['number']}: {data['title']}"

        body = data.get("body") or "No description provided."
        if len(body) > MAX_BODY_LENGTH:
            body = body[:MAX_BODY_LENGTH].rstrip() + "…"

        embed = discord.Embed(
            title=embed_title[:256],
            description=body,
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
        return embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GitHub(bot))
