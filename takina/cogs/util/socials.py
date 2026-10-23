# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from discord.ext import commands
from urllib.parse import quote
from takina import config
import datetime
import discord


class Socials(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_command(
        name="github",
        description="Display information on a GitHub user.",
        usage="orangci",
        aliases=["gh"],
    )
    @lychecks.is_user_app()
    async def github(self, ctx: commands.Context, *, username: str):
        username = username.removeprefix("@")

        headers = {"Accept": "application/vnd.github+json"}
        if config.GITHUB_AUTH_TOKEN:
            headers["Authorization"] = f"Bearer {config.GITHUB_AUTH_TOKEN}"

        data = await lyhelpers.request(
            f"https://api.github.com/users/{quote(username, safe='')}",
            headers=headers,
            not_found="That GitHub account does not exist.",
        )

        if not data:
            raise lyerrors.TakinaNotFoundError("That GitHub account does not exist.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = ""
        embed.title = data["login"]
        embed.url = data["html_url"]

        if bio := data.get("bio"):
            embed.description = bio + "\n"

        if website := data.get("blog"):
            website_display = website.removeprefix("https://").removeprefix("http://")
            embed.description += f"\n> **Website**: [{website_display}]({website})"

        if email_address := data.get("email"):
            embed.description += f"\n> **Email**: [{email_address}](mailto:{email_address})"

        if location := data.get("location"):
            embed.description += f"\n> **Location**: {location}"

        if data.get("hireable"):
            embed.description += "\n> **Hireable**: This user is available for hire."

        if company := data.get("company"):
            embed.description += f"\n> **Company**: {company}"

        if followers := data.get("followers"):
            embed.description += f"\n> **Followers**: {followers}"

        if following := data.get("following"):
            embed.description += f"\n> **Following**: {following}"

        if created := data.get("created_at"):
            created_at = datetime.datetime.fromisoformat(created)
            embed.description += f"\n> **Joined GitHub**: <t:{int(created_at.timestamp())}:D> (<t:{int(created_at.timestamp())}:R>)"

        if public_repos := data.get("public_repos"):
            embed.description += f"\n> **Public Repositories**: {public_repos}"

        if public_gists := data.get("public_gists"):
            embed.description += f"\n> **Public Gists**: {public_gists}"

        if data.get("type") != "User":
            embed.description += "\n\nThis account is not a regular GitHub user account."

        if data.get("site_admin"):
            embed.description += "\n\n**This user is a GitHub site administrator.**"

        embed.set_thumbnail(url=data["avatar_url"])
        embed.set_footer(text=f"User ID: {data['id']}")

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="codeberg",
        description="Social information command for Codeberg.",
        usage="orangc",
        aliases=["cb"],
    )
    @lychecks.is_user_app()
    async def codeberg(self, ctx: commands.Context, *, username: str):
        user_url = f"https://codeberg.org/api/v1/users/{quote(username.removeprefix('@'), safe='')}"
        data = await lyhelpers.request(user_url, not_found="That Codeberg account does not exist.")

        if not data or data.get("message"):
            raise lyerrors.TakinaNotFoundError("That Codeberg account does not exist.")

        # one repository is enough, as forgejo puts the full count in a header
        _, repo_headers = await lyhelpers.request(
            f"{user_url}/repos", params={"limit": 1}, with_headers=True
        )

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = ""
        embed.title = data["username"]
        embed.url = data["html_url"]

        if description := data.get("description"):
            embed.description = description

        if website := data.get("website"):
            website_display = website.removeprefix("https://").removeprefix("http://")
            embed.description += f"\n\n> **Website**: [{website_display}]({website})"

        if email_address := data.get("email"):
            embed.description += f"\n> **Email**: [{email_address}](mailto:{email_address})"

        if location := data.get("location"):
            embed.description += f"\n> **Location**: {location}"

        if followers := data.get("followers_count"):
            embed.description += f"\n> **Followers**: {followers}"

        if following := data.get("following_count"):
            embed.description += f"\n> **Following**: {following}"

        if (repo_count := repo_headers.get("X-Total-Count")) is not None:
            embed.description += f"\n> **Public Repositories**: {int(repo_count):,}"

        if created := data.get("created"):
            created_at = datetime.datetime.fromisoformat(created)
            embed.description += f"\n> **Joined Codeberg**: <t:{int(created_at.timestamp())}:D> (<t:{int(created_at.timestamp())}:R>)"

        if data.get("is_admin"):
            embed.description += "\n\n**This user is a Codeberg site administrator.**"

        if avatar_url := data.get("avatar_url"):
            embed.set_thumbnail(url=avatar_url)

        embed.set_footer(text=f"User ID: {data['id']}")
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Socials(bot))
