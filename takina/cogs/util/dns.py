from takina.libs import lychecks, lyerrors, lyhelpers, lyviews
from discord.ext import commands
from takina import config
from dns import resolver
import datetime
import discord
import whodap


class DNS(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

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
            except NotImplementedError:
                raise
            except Exception:
                return None

    @lychecks.is_user_app()
    @commands.hybrid_command(
        name="whois", description="Perform a WHOIS search on a domain name.", usage="orangc.net"
    )
    async def whois(self, ctx: commands.Context, domain: str):
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
                value = ", ".join(item for item in value)

            embed.description += f"\n> **{key_str}**: {value}"
        embed.description += (
            "\n> **URL of the ICANN Whois Inaccuracy Complaint Form**: https://www.icann.org/wicf/"
        )

        await ctx.reply(embed=embed, mention_author=False)

    @lychecks.is_user_app()
    @commands.hybrid_command(
        name="dig", description="Dig a URL for its DNS records.", usage="orangc.net"
    )
    async def dig(self, ctx: commands.Context, url: str):
        record_types = ["A", "CNAME", "AAAA", "MX", "TXT", "SRV", "NS"]
        url = url.removeprefix("https://").removeprefix("http://")

        lines: list[str] = []

        for record_type in record_types:
            try:
                answers = resolver.resolve(url, record_type)
                records = "\n".join(str(answer) for answer in answers)

                if records:
                    lines.append(
                        f"{await lyhelpers.fetch_random_emoji()}**{record_type} Records**\n```{records}```"
                    )

            except resolver.NoAnswer:
                continue
            except resolver.NXDOMAIN:
                raise lyerrors.TakinaNotFoundError(f"Domain `{url}` does not exist.")

        if not lines:
            raise lyerrors.TakinaNotFoundError(f"No DNS records found for `{url}`.")

        pages = []

        for chunk in lyhelpers.chunked(lines, 3):
            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.title = f"DNS Records for {url}"
            embed.description = "\n".join(chunk)
            pages.append(embed)

        view = lyviews.PaginatorView(ctx.author, pages)
        view.message = await ctx.reply(embed=pages[0], view=view, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(DNS(bot))
