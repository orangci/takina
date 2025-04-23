# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import re
import aiohttp
import nextcord
from nextcord.ext import application_checks as ac, commands
from config import *
from .libs.lib import *
from ...libs.oclib import *
import re


async def is_valid_domain(domain):
    pattern = r"^(?!.*--)[a-z0-9-]+$"
    return bool(re.match(pattern, domain))


async def fetch_subdomain_info(subdomain_name):
    is_valid = await is_valid_domain(subdomain_name)
    if not is_valid:
        return None

    if subdomain_name.endswith(".is-a.dev"):
        subdomain_name = subdomain_name[:-9]
    data = await request("https://raw.is-a.dev/v2.json")

    for entry in data:
        if entry.get("domain")[:-9] == subdomain_name:
            return entry

    return None


async def build_whois_embed(domain):
    domain_data = await fetch_subdomain_info(domain)

    if not domain_data:
        embed = nextcord.Embed(color=ERROR_COLOR)
        embed.description = ":x: The domain queried does not exist."
        return embed

    if domain_data.get("reserved"):
        embed = nextcord.Embed(color=ERROR_COLOR)
        embed.description = f":x: `{domain}.is-a.dev` has been reserved by our maintainers and cannot be registered."
        return embed

    if domain_data.get("internal"):
        embed = nextcord.Embed(color=ERROR_COLOR)
        embed.description = f":x: `{domain}.is-a.dev` is being used internally by our maintainers and cannot be registered."
        return embed

    embed = nextcord.Embed(color=EMBED_COLOR)
    embed.url = f"https://{domain}.is-a.dev"
    embed.title = f"{domain}.is-a.dev"
    embed.set_footer(
        text="is-a.dev",
        icon_url="https://raw.githubusercontent.com/is-a-dev/register/refs/heads/main/media/logo.png",
    )

    owner_field_value = ""
    for platform, username in domain_data["owner"].items():
        if platform == "username":
            owner_field_value += (
                f"Github: [{username}](https://github.com/{username})\n"
            )
        else:
            owner_field_value += f"{platform.capitalize()}: {username}\n"

    records_field_value = ""
    for record_type, record_value in domain_data["records"].items():
        if isinstance(record_value, str):
            records_field_value += f"{record_type}: {record_value}\n"
        elif isinstance(record_value, dict):
            record_items = ", ".join(
                f"{key}: {value}" for key, value in record_value.items()
            )
            records_field_value += f"{record_type}: {{{record_items}}}\n"
        else:
            records_field_value += (
                f"{record_type}: {', '.join(map(str, record_value))}\n"
            )

    redirect_config = domain_data.get("redirect_config")
    if redirect_config:
        redirect_config_field_value = ""
        custom_paths = redirect_config.get("custom_paths")

        if custom_paths:
            custom_paths_items = "\n".join(
                f" {path}: {url}" for path, url in custom_paths.items()
            )
            redirect_config_field_value += f"{custom_paths_items}\n"

        if redirect_config.get("redirect_paths"):
            redirect_config_field_value += f"Redirect Paths: True\n"

    embed.add_field(name="Owner", value=owner_field_value, inline=True)
    embed.add_field(name="Records", value=records_field_value, inline=True)
    if redirect_config:
        embed.add_field(name="Redirect Config", value=redirect_config_field_value)

    if domain_data.get("proxied"):
        embed.description += "\n *This domain is proxied.*"

    return embed


async def fetch_staff_subdomains():
    data = await request("https://raw.is-a.dev/v2.json")

    non_reserved_domains = [
        entry["domain"][:-9]
        for entry in data
        if entry.get("owner", {}).get("username") == "is-a-dev"
        or entry.get("internal")
        and not entry.get("reserved")
    ]

    embed = nextcord.Embed(color=EMBED_COLOR)
    embed.title = f"is-a.dev staff domains"

    if non_reserved_domains:
        embed.description = "\n".join(
            f"- [{domain}.is-a.dev](https://{domain}.is-a.dev)"
            for domain in non_reserved_domains
        )
    else:
        embed.description = f":x: No staff owned subdomains of is-a.dev were found."

    return embed


async def fetch_non_existent_single_character_domains():
    data = await request("https://raw.is-a.dev/v2.json")
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    non_existent_single_character_domains = []

    for character in alphabet:
        domain_name = f"{character}.is-a.dev"
        exists = any(entry["domain"] == domain_name for entry in data)

        if not exists:
            non_existent_single_character_domains.append(domain_name)

    embed = nextcord.Embed(color=EMBED_COLOR)
    embed.title = "Unregistered is-a.dev single-character subdomains"

    if non_existent_single_character_domains:
        embed.description = "\n".join(
            f"- [{domain}](https://{domain})"
            for domain in non_existent_single_character_domains
        )
    else:
        embed.description = ":x: All single-character domains have been registered."

    return embed


async def isadev_domain_data_overview_embed_builder():
    data = await request("https://raw.is-a.dev/v2.json")

    subdomains_count = 0
    records_count = 0
    unique_users = set()
    domains_per_user = {}
    dns_records = {
        "A": 0,
        "AAAA": 0,
        "CAA": 0,
        "CNAME": 0,
        "DS": 0,
        "MX": 0,
        "NS": 0,
        "SRV": 0,
        "TXT": 0,
        "URL": 0,
    }

    for entry in data:
        if entry.get("reserved") or entry.get("internal"):
            continue

        subdomains_count += 1

        for record_type, record_value in entry.get("records", {}).items():
            if record_type in dns_records:
                if isinstance(record_value, int):
                    dns_records[record_type] += record_value
                elif isinstance(record_value, str):
                    dns_records[record_type] += 1
                elif isinstance(record_value, list):
                    dns_records[record_type] += len(record_value)

        owner = entry.get("owner", {}).get("username", "Unknown")
        unique_users.add(owner)
        if owner in domains_per_user:
            domains_per_user[owner] += 1
        else:
            domains_per_user[owner] = 1

    records_count = sum(dns_records.values())
    average_domains_per_user = (
        subdomains_count / len(unique_users) if unique_users else 0
    )
    most_domains_user = max(
        domains_per_user.items(), key=lambda x: x[1], default=("None", 0)
    )

    statistics = (
        f"- Subdomains: {subdomains_count}\n"
        f"- Records: {records_count}\n"
        f"- Unique users: {len(unique_users)}\n"
        f"- Average domains per user: {average_domains_per_user:.1f}\n"
        f"- Most domains: {most_domains_user[0]} ({most_domains_user[1]})\n\n"
    )

    record_statistics = ""
    for record_type, count in dns_records.items():
        record_statistics += f"- {record_type}: {count}\n"

    statistics_embed = nextcord.Embed(
        color=EMBED_COLOR,
        title="is-a.dev Statistics",
        url="https://data.is-a.dev",
    )
    statistics_embed.add_field(name="Stats", value=statistics, inline=True)
    statistics_embed.add_field(name="DNS Records", value=record_statistics, inline=True)
    statistics_embed.set_footer(
        text="is-a.dev",
        icon_url="https://raw.githubusercontent.com/is-a-dev/register/refs/heads/main/media/logo.png",
    )
    return statistics_embed


async def isadev_user_domain_data_overview_embed_builder(username):
    data = await request("https://raw.is-a.dev/v2.json")

    subdomains_count = 0
    records_count = 0
    dns_records = {
        "A": 0,
        "AAAA": 0,
        "CAA": 0,
        "CNAME": 0,
        "DS": 0,
        "MX": 0,
        "NS": 0,
        "SRV": 0,
        "TXT": 0,
        "URL": 0,
    }

    for entry in data:
        entry_owner = entry.get("owner").get("username")
        if str(entry_owner).lower() != username.lower():
            continue
        if entry.get("reserved") or entry.get("internal"):
            continue

        subdomains_count += 1

        for record_type, record_value in entry.get("records", {}).items():
            if record_type in dns_records:
                if isinstance(record_value, int):
                    dns_records[record_type] += record_value
                elif isinstance(record_value, str):
                    dns_records[record_type] += 1
                elif isinstance(record_value, list):
                    dns_records[record_type] += len(record_value)

    records_count = sum(dns_records.values())

    statistics = f"- Subdomains: {subdomains_count}\n" f"- Records: {records_count}\n"

    statistics += "\n**DNS Records**:\n"
    for record_type, count in dns_records.items():
        if count == 0:
            continue
        statistics += f"- {record_type}: {count}\n"

    statistics_embed = nextcord.Embed(
        color=EMBED_COLOR,
        title=f"is-a.dev Statistics for {username}",
        description=statistics,
        url=f"https://github.com/{username}",
    )
    statistics_embed.set_footer(
        text="is-a.dev",
        icon_url="https://raw.githubusercontent.com/is-a-dev/register/refs/heads/main/media/logo.png",
    )
    return statistics_embed


async def build_check_embed(domain):
    domain_data = await fetch_subdomain_info(domain)
    is_valid = await is_valid_domain(domain)

    if not is_valid:
        embed = nextcord.Embed(color=ERROR_COLOR)
        embed.description = f":x: That is not a valid domain name. A valid domain may only have alphabetical, numerical, period (.), and dash (-) characters."
        embed.set_footer(
            text="is-a.dev",
            icon_url="https://raw.githubusercontent.com/is-a-dev/register/refs/heads/main/media/logo.png",
        )
        return embed

    if not domain_data:
        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = f"✅ [{domain}.is-a.dev](https://{domain}.is-a.dev) is available for [registration](https://github.com/is-a-dev/register?tab=readme-ov-file#how-to-register)."
        embed.set_footer(
            text="is-a.dev",
            icon_url="https://raw.githubusercontent.com/is-a-dev/register/refs/heads/main/media/logo.png",
        )
        return embed

    if domain_data.get("reserved"):
        embed = nextcord.Embed(color=ERROR_COLOR)
        embed.description = f":x: Sorry, `{domain}.is-a.dev` has been reserved by our maintainers and cannot be registered."
        embed.set_footer(
            text="is-a.dev",
            icon_url="https://raw.githubusercontent.com/is-a-dev/register/refs/heads/main/media/logo.png",
        )
        return embed

    if domain_data.get("internal"):
        embed = nextcord.Embed(color=ERROR_COLOR)
        embed.description = f":x: Sorry, `{domain}.is-a.dev` is being used internally by our maintainers and cannot be registered."
        embed.set_footer(
            text="is-a.dev",
            icon_url="https://raw.githubusercontent.com/is-a-dev/register/refs/heads/main/media/logo.png",
        )
        return embed

    if domain_data:
        embed = nextcord.Embed(color=ERROR_COLOR)
        domain_holder = str(domain_data.get("owner").get("username"))
        embed.description = f":x: [{domain}.is-a.dev](https://{domain}.is-a.dev) has already been registered by [{domain_holder}](https://github.com/{domain_holder})."
        embed.set_footer(
            text="is-a.dev",
            icon_url="https://raw.githubusercontent.com/is-a-dev/register/refs/heads/main/media/logo.png",
        )
        return embed

    raise commands.DiscordException


class SubdomainUtils(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @is_in_guild()
    @commands.command(
        help="Lookup information on a subdomain of is-a.dev. Usage: `whois cirno.is-a.dev`."
    )
    async def whois(self, ctx: commands.Context, domain: str) -> None:
        embed = await build_whois_embed(domain)
        await ctx.reply(embed=embed, mention_author=False)

    @is_in_guild()
    @commands.command(
        help="Fetch all staff-owned is-a.dev subdomains. Usage: `staff_subdomains`",
        aliases=["iad-staff"],
    )
    async def staff_subdomains(self, ctx: commands.Context) -> None:
        embed = await fetch_staff_subdomains()
        await ctx.reply(embed=embed, mention_author=False)

    @is_in_guild()
    @commands.command(
        help="Fetch all unregistered single-character is-a.dev subdomains. Usage: `single_character_subdomains`",
        aliases=["iad-scs"],
    )
    async def single_character_subdomains(self, ctx: commands.Context) -> None:
        embed = await fetch_non_existent_single_character_domains()
        await ctx.reply(embed=embed, mention_author=False)

    @is_in_guild()
    @commands.command(
        help="Check whether an is-a.dev subdomain is available for registration. Usage: `check cirno`."
    )
    async def check(self, ctx: commands.Context, domain: str):
        embed = await build_check_embed(domain)
        await ctx.reply(embed=embed, mention_author=False)

    @is_in_guild()
    @commands.command(
        help="Fetch is-a.dev statistics for either the entire service or a specific Github username. Usage: `is-a-dev orangci`.",
        aliases=["isadev", "is-a-dev", "iad"],
    )
    async def is_a_dev(self, ctx: commands.Context, username: str = None):
        if username:
            embed = await isadev_user_domain_data_overview_embed_builder(username)
        else:
            embed = await isadev_domain_data_overview_embed_builder()
        await ctx.reply(embed=embed, mention_author=False)


class SubdomainUtilsSlash(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @nextcord.slash_command(
        name="whois",
        guild_ids=[SERVER_ID],
        description="Lookup information on a subdomain of is-a.dev. Usage: `whois cirno.is-a.dev`.",
    )
    async def whois(
        self,
        interaction: nextcord.Interaction,
        domain: str = nextcord.SlashOption(
            description="The is-a.dev subdomain name to lookup information on.",
            required=True,
        ),
    ) -> None:
        await interaction.response.defer()
        embed = await build_whois_embed(domain)
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(
        name="iad-staff-subdomains",
        guild_ids=[SERVER_ID],
        description="Fetch all staff-owned is-a.dev subdomains.",
    )
    async def staff_subdomains(
        self,
        interaction: nextcord.Interaction,
    ) -> None:
        await interaction.response.defer()
        embed = await fetch_staff_subdomains()
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(
        name="iad-single-character-subdomains",
        guild_ids=[SERVER_ID],
        description="Fetch all unregistered single-character is-a.dev subdomains.",
    )
    async def staff_subdomains(
        self,
        interaction: nextcord.Interaction,
    ) -> None:
        await interaction.response.defer()
        embed = await fetch_non_existent_single_character_domains()
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(
        name="check",
        guild_ids=[SERVER_ID],
        description="Check whether an is-a.dev subdomain is available for registration.",
    )
    async def check(
        self,
        interaction: nextcord.Interaction,
        domain: str = nextcord.SlashOption(
            description="The is-a.dev subdomain name to check the availability of.",
            required=True,
        ),
    ) -> None:
        await interaction.response.defer()
        embed = await build_check_embed(domain)
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(
        name="is-a-dev",
        guild_ids=[SERVER_ID],
        description="Fetch is-a.dev statistics for either the entire service or a specific Github username.",
    )
    async def is_a_dev(
        self,
        interaction: nextcord.Interaction,
        github_username: str = nextcord.SlashOption(
            description="The GitHub username to check the statistics of.",
            required=False,
        ),
    ) -> None:
        await interaction.response.defer()
        if github_username:
            embed = await isadev_user_domain_data_overview_embed_builder(
                github_username
            )
        else:
            embed = await isadev_domain_data_overview_embed_builder()
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(SubdomainUtils(bot))
    bot.add_cog(SubdomainUtilsSlash(bot))
