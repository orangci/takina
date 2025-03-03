"""
    BSD 3-Clause License

    Copyright (c) 2024 - present, MaskDuck

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, this
    list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

    3. Neither the name of the copyright holder nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# code has been modified and is not the original code from MaskDuck

from __future__ import annotations

import re
from typing import List, TypedDict
from typing_extensions import NotRequired
import aiohttp
import nextcord
from nextcord.ext import application_checks as ac, commands
from nextcord import Interaction, OptionConverter
from config import *
from .libs.lib import *
import random
import json


class Domain(TypedDict):
    description: NotRequired[str]
    repo: NotRequired[str]
    owner: _OwnerObject
    record: _RecordObject


class SubdomainNameConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> str:  # type: ignore
        argument = argument.lower()
        if argument.endswith(".is-a.dev"):
            return argument[:-9]
        return argument


class SlashSubdomainNameConverter(OptionConverter):
    async def convert(self, interaction: Interaction, value: str) -> str:  # type: ignore
        value = value.lower()
        if value.endswith(".is-a.dev"):
            return value[:-9]
        return value


class DomainNotExistError(commands.CommandError):
    """Error raised when domain cannot be found."""


async def request(requesting_domain: bool = False, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request(*args, **kwargs) as ans:
            if ans.status == 404 and requesting_domain:
                raise DomainNotExistError("imagine")
            return await ans.json(content_type=None)


request.__doc__ = aiohttp.ClientSession.request.__doc__


class SubdomainUtils(commands.Cog):
    """Various utility commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self._bot: commands.Bot = bot
        self.reserved_domains = []

    async def fetch_reserved_domains(self) -> None:
        """Fetches the list of reserved domains."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://raw.githubusercontent.com/is-a-dev/register/refs/heads/main/util/reserved.json"
            ) as response:
                if response.status == 200:
                    text_data = await response.text()
                    try:
                        self.reserved_domains = json.loads(text_data)
                    except json.JSONDecodeError:
                        print("Failed to parse reserved domains as JSON.")
                        self.reserved_domains = []
                else:
                    print(
                        f"Failed to fetch reserved domains. Status code: {response.status}"
                    )
                    self.reserved_domains = []

    @commands.Cog.listener()
    async def on_ready(self):
        """Fetch reserved domains when the bot is ready."""
        await self.fetch_reserved_domains()

    @classmethod
    def fetch_description_about_a_domain(cls, data: Domain):
        parsed_contact = {}
        for platform, username in data["owner"].items():
            if platform == "username":
                parsed_contact["github"] = (
                    f"[{username}](https://github.com/{username})"
                )
            elif platform == "twitter":
                parsed_contact["twitter"] = (
                    f"[{username}](https://twitter.com/{username})"
                )
            elif platform == "email":
                if username != "":
                    parsed_contact["email"] = username
            else:
                # unknown contact, ignoring
                parsed_contact[platform] = username

        contact_desc = """**Contact Info**:\n"""
        for x, y in parsed_contact.items():
            contact_desc += f"**{x}**: {y}\n"

        record_desc = """**Record Info**:\n"""
        for x, y in data["record"].items():
            if x == "CNAME":
                record_desc += f"**{x}**: [{y}](https://{y})\n"
            else:
                record_desc += f"**{x}**: {y}\n"

        if domain_desc := data.get("description"):
            domain_desc = "**Description**: " + domain_desc + "\n"
        else:
            domain_desc = None

        if repo := data.get("repo"):
            repo_desc = "**Repository**: " + f"[here]({repo})" + "\n"
        else:
            repo_desc = None

        my_description = f"""
        {contact_desc}

        {record_desc}
        """
        if domain_desc is not None:
            my_description += domain_desc + "\n"
        if repo_desc is not None:
            my_description += repo_desc + "\n"
        return my_description

    @commands.command()
    @is_in_guild()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def whois(
        self, ctx: commands.Context, domain: SubdomainNameConverter
    ) -> None:
        """Lookup information about an is-a.dev domain. Usage: `whois domain.is-a.dev`."""
        k = nextcord.ui.View()
        k.add_item(
            nextcord.ui.Button(
                style=nextcord.ButtonStyle.url,
                url=f"https://github.com/is-a-dev/register/edit/main/domains/{domain}.json",
                label="Edit this subdomain?",
            )
        )
        try:
            data = await request(
                True,
                "GET",
                f"https://raw.githubusercontent.com/is-a-dev/register/main/domains/{domain}.json",
            )
        except DomainNotExistError:
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = ":x: The domain queried does not exist."
            await ctx.reply(embed=embed, mention_author=False)
            return
        embed = nextcord.Embed(
            color=EMBED_COLOR,
            title=f"Info about {domain}.is-a.dev",
            description=self.fetch_description_about_a_domain(data),
        )
        await ctx.reply(embed=embed, view=k, mention_author=False)

    @commands.command()
    @is_in_guild()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def check(
        self, ctx: commands.Context, domain: SubdomainNameConverter
    ) -> None:
        """Checks if an is-a.dev domain is available. Usage: `check domain.is-a.dev`."""
        if domain in self.reserved_domains:
            embed = nextcord.Embed(
                color=ERROR_COLOR,
                description=f":x: Sorry, `{domain}.is-a.dev` has been reserved by maintainers and cannot be registered.",
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        try:
            await request(
                True,
                "GET",
                f"https://raw.githubusercontent.com/is-a-dev/register/main/domains/{domain}.json",
            )
            embed = nextcord.Embed(
                color=ERROR_COLOR,
                description=f":x: Sorry, [{domain}.is-a.dev](<https://{domain}.is-a.dev>) is taken.",
            )
            await ctx.reply(embed=embed, mention_author=False)
        except DomainNotExistError:
            embed = nextcord.Embed(
                color=EMBED_COLOR,
                description=f"✅ Congratulations, [{domain}.is-a.dev](<https://{domain}.is-a.dev>) is available!",
            )
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="willyoumarryme",
        help="Takina replies to whether or not marriage is feasible.",
        hidden=True,
    )
    @is_in_guild()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def willyoumarryme(self, ctx: commands.Context):
        guaranteed_marriages = [
            1040303561847881729,
            961063229168164864,
            713254655999868931,
            1049263707177353247,
            # Add more as needed, orangc.
        ]
        embed = nextcord.Embed(
            description=f"### {ctx.author.mention} proposed to {BOT_NAME}\n\n",
            color=EMBED_COLOR,
        )
        if ctx.author.id in guaranteed_marriages:
            embed.description += "Yes! I love you too. I can't wait to get married!"
            await ctx.reply(embed=embed, mention_author=False)
            return

        choice = bool(random.getrandbits(1))
        if choice == True:
            embed.description += "Sure, I will marry you."
            await ctx.reply(embed=embed, mention_author=False)
        else:
            embed.description += "No, stay away from me."
            await ctx.reply(embed=embed, mention_author=False)


class SubdomainUtilsSlash(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot: commands.Bot = bot
        self.reserved_domains = []

    async def fetch_reserved_domains(self) -> None:
        """Fetches the list of reserved domains."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://raw.githubusercontent.com/is-a-dev/register/refs/heads/main/util/reserved.json"
            ) as response:
                if response.status == 200:
                    text_data = await response.text()
                    try:
                        self.reserved_domains = json.loads(text_data)
                    except json.JSONDecodeError:
                        print("Failed to parse reserved domains as JSON.")
                        self.reserved_domains = []
                else:
                    print(
                        f"Failed to fetch reserved domains. Status code: {response.status}"
                    )
                    self.reserved_domains = []

    @commands.Cog.listener()
    async def on_ready(self):
        """Fetch reserved domains when the bot is ready."""
        await self.fetch_reserved_domains()

    @nextcord.slash_command(name="check", guild_ids=[SERVER_ID])
    async def check(
        self,
        interaction: nextcord.Interaction,
        domain: SlashSubdomainNameConverter = nextcord.SlashOption(
            description="The domain name to check for.", required=True
        ),
    ) -> None:
        if domain in self.reserved_domains:
            embed = nextcord.Embed(
                color=ERROR_COLOR,
                description=f":x: Sorry, `{domain}.is-a.dev` has been reserved by maintainers and cannot be registered.",
            )
            await interaction.send(embed=embed)
            return

        try:
            await request(
                True,
                "GET",
                f"https://raw.githubusercontent.com/is-a-dev/register/main/domains/{domain}.json",
            )
            embed = nextcord.Embed(
                color=ERROR_COLOR,
                description=f":x: Sorry, [{domain}.is-a.dev](<https://{domain}.is-a.dev>) is taken.",
            )
            await interaction.send(embed=embed)
        except DomainNotExistError:
            embed = nextcord.Embed(
                color=EMBED_COLOR,
                description=f"✅ Congratulations, [{domain}.is-a.dev](<https://{domain}.is-a.dev>) is available!",
            )
            await interaction.send(embed=embed)

    @nextcord.slash_command(name="whois", guild_ids=[SERVER_ID])
    async def whois_slash(
        self,
        interaction: nextcord.Interaction,
        domain: SlashSubdomainNameConverter = nextcord.SlashOption(
            description="The is-a.dev domain name to lookup information for.",
            required=True,
        ),
    ) -> None:
        try:
            data = await request(
                True,
                "GET",
                f"https://raw.githubusercontent.com/is-a-dev/register/main/domains/{domain}.json",
            )
            view = nextcord.ui.View()

            view.add_item(
                nextcord.ui.Button(
                    style=nextcord.ButtonStyle.url,
                    url=f"https://github.com/is-a-dev/register/edit/main/domains/{domain}.json",
                    label="Edit this subdomain?",
                )
            )
            await interaction.send(
                embed=nextcord.Embed(
                    title=f"Domain info for {domain}.is-a.dev",
                    description=SubdomainUtils.fetch_description_about_a_domain(data),
                    color=EMBED_COLOR,
                ),
                view=view,
                ephemeral=True,
            )
        except DomainNotExistError:
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = ":x: The domain queried does not exist."
            await interaction.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(SubdomainUtils(bot))
    bot.add_cog(SubdomainUtilsSlash(bot))
