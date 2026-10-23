# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers, lyviews
from dns import asyncresolver, exception, name, resolver
from whodap.errors import WhodapError
from discord.ext import commands
from takina import config
import datetime
import discord
import whodap

RECORD_TYPES = ["A", "CNAME", "AAAA", "MX", "TXT", "SRV", "NS"]
# public resolvers rather than the host's, which would answer for internal names too
PUBLIC_NAMESERVERS = ["1.1.1.1", "9.9.9.9"]


class DNS(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot
        self._resolver = asyncresolver.Resolver(configure=False)
        self._resolver.nameservers = PUBLIC_NAMESERVERS
        self._resolver.lifetime = 5

    async def resolve_domain(self, domain: str) -> whodap.DomainResponse | None:
        parts = domain.lower().strip().split(".")
        if len(parts) < 2:
            return None

        # rdap wants the name and the top-level domain apart, so example.co.uk is example.co + uk.
        # longest first: shorter names like co.uk are registries that answer for themselves,
        # and www.example.com still falls back to example.com
        tld = parts[-1]
        async with whodap.DNSClient.new_aio_client_context() as client:
            for start in range(len(parts) - 1):
                try:
                    return await client.aio_lookup(".".join(parts[start:-1]), tld)
                except WhodapError:
                    continue

        return None

    @commands.hybrid_command(
        name="whois", description="Perform a WHOIS search on a domain name.", usage="orangc.net"
    )
    @lychecks.is_user_app()
    async def whois(self, ctx: commands.Context, domain: str):
        await ctx.defer()
        try:
            response = await self.resolve_domain(domain)
        except NotImplementedError:
            raise lyerrors.TakinaNotFoundError(
                "WHOIS lookups for this top-level domain are not supported."
            )

        if not isinstance(response, whodap.DomainResponse):
            raise lyerrors.TakinaNotFoundError("This domain name doesn't appear to exist.")

        data = response.to_whois_dict()

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = f"WHOIS Information for {domain}"
        embed.description = ""

        for key, value in data.items():
            if value is None:
                continue

            key_str = key.replace("_", " ").title()

            if isinstance(value, datetime.datetime):
                value = f"<t:{int(value.timestamp())}:D>"

            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)

            embed.description += f"\n> **{key_str}**: {value}"
        embed.description = lyhelpers.truncate(embed.description, 3900)
        embed.description += (
            "\n> **URL of the ICANN Whois Inaccuracy Complaint Form**: https://www.icann.org/wicf/"
        )

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="dig", description="Dig a URL for its DNS records.", usage="orangc.net"
    )
    @lychecks.is_user_app()
    async def dig(self, ctx: commands.Context, url: str):
        await ctx.defer()
        url = url.removeprefix("https://").removeprefix("http://").split("/")[0]

        lines: list[str] = []

        for record_type in RECORD_TYPES:
            try:
                answers = await self._resolver.resolve(url, record_type)
            except (resolver.NoAnswer, resolver.NoNameservers):
                continue
            except resolver.NXDOMAIN as error:
                raise lyerrors.TakinaNotFoundError(f"Domain `{url}` does not exist.") from error
            except (name.LabelTooLong, name.EmptyLabel, name.NameTooLong) as error:
                raise lyerrors.TakinaUserInputError(f"`{url}` is not a valid domain.") from error
            except exception.Timeout as error:
                raise lyerrors.TakinaError("The DNS lookup timed out.") from error

            # a backtick in a txt record would otherwise close the code block early
            records = "\n".join(str(answer) for answer in answers).replace("`", "`\u200b")
            if records:
                lines.append(
                    f"{await lyhelpers.fetch_random_emoji()}**{record_type} Records**\n```{lyhelpers.truncate(records, 1000)}```"
                )

        if not lines:
            raise lyerrors.TakinaNotFoundError(f"No DNS records found for `{url}`.")

        pages = []

        for chunk in lyhelpers.chunked(lines, 3):
            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.title = f"DNS Records for {url}"
            embed.description = "\n".join(chunk)
            pages.append(embed)

        await lyviews.PaginatorView.send(ctx, pages)


async def setup(bot: commands.Bot):
    await bot.add_cog(DNS(bot))
