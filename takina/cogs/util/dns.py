# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
from ..libs import oclib
from dns import resolver
import datetime
import nextcord
import whodap
import config


class DNS(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot: commands.Bot = bot

    async def resolve_domain(self, domain: str) -> whodap.DomainResponse | None:
        parts = domain.lower().strip().split(".")
        if len(parts) < 2:
            return None

        for i in range(1, len(parts)):
            tld = ".".join(parts[i:])
            sld = parts[i - 1]

        async with whodap.DNSClient.new_aio_client_context() as client:
            try:
                response = await client.aio_lookup(sld, tld)
                return response
            except Exception:
                return None

    async def build_whois_embed(self, ctx: commands.Context | nextcord.Interaction, domain: str) -> nextcord.Embed:
        embed = nextcord.Embed(color=config.EMBED_COLOR, description="")
        response = await self.resolve_domain(domain)

        if not isinstance(response, whodap.DomainResponse):
            embed.color = config.ERROR_COLOR
            embed.description = ":x: This domain name doesn't appear to exist."
            return embed

        data = response.to_whois_dict()
        embed.title = f"WHOIS Information for {domain}"

        for key, value in data.items():
            if value is None:
                continue

            key_str = key.replace("_", " ").title()

            if isinstance(value, datetime.datetime):
                timestamp = int(value.timestamp())
                value_str = f"<t:{timestamp}:D>"
            else:
                value_str = str(value)

            embed.description += f"\n> **{key_str}**: {value_str}"

        return embed

    # 2025.03.16: removed base command because the output for dig commands are too long; an ephemeral slash command is the best choice here

    @nextcord.slash_command(name="dig", description="Dig an URL for its DNS records.")
    async def dig_slash(
        self, interaction: nextcord.Interaction, url: str = nextcord.SlashOption(description="The URL to dig for DNS records.", required=True)
    ) -> None:
        record_types = ["A", "CNAME", "AAAA", "MX", "TXT", "SRV", "NS"]
        full_answer = ""
        url = url.removeprefix("https://")
        url = url.removeprefix("http://")

        for record_type in record_types:
            try:
                answers = resolver.resolve(url, record_type)
                records = "\n".join([str(answer) for answer in answers])
                if records:
                    emoji = await oclib.fetch_random_emoji()
                    full_answer += f"{emoji}**{record_type} Records**\n```{records}```\n"
            except resolver.NoAnswer:
                continue
            except resolver.NXDOMAIN:
                error_embed = nextcord.Embed(color=config.ERROR_COLOR)
                error_embed.description = f"❌ Domain '{url}' does not exist."
                await interaction.send(embed=error_embed, ephemeral=True)
                return

        if full_answer:
            embed = nextcord.Embed(title=f"DNS Records for {url}", description=full_answer, color=config.EMBED_COLOR)
            await interaction.send(embed=embed, ephemeral=True)
        else:
            embed = nextcord.Embed(color=config.ERROR_COLOR)
            embed.description = f":x: No records found for {url}."
            await interaction.send(embed=error_embed, ephemeral=True)

    # @commands.command(name="whois", help="Perform a WHOIS search on a domain name.")
    # async def whois(self, ctx: commands.Context, domain: str):
    #     embed = await self.build_whois_embed(ctx, domain)
    #     await ctx.reply(embed=embed, mention_author=False)
    # Output is too long. Use slash command instead.

    @nextcord.slash_command(name="whois", description="Perform a WHOIS search on a domain name.")
    async def slash_whois(self, interaction: nextcord.Interaction, domain: str):
        embed = await self.build_whois_embed(interaction, domain)
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(DNS(bot))
