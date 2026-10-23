# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from ping3 import ping as dns_ping
from discord.ext import commands
from takina import config
import ipaddress
import discord
import asyncio
import socket


async def resolve_address(host: str) -> str:
    try:
        addresses = await asyncio.get_running_loop().getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError) as error:
        raise lyerrors.TakinaNotFoundError(
            "The specified hostname is unknown and could not be resolved."
        ) from error

    return str(addresses[0][4][0])


def is_public(address: str) -> bool:
    ip = ipaddress.ip_address(address.split("%")[0])
    return ip.is_global and not ip.is_multicast


class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(
        description="Ping the bot and check its latency, or ping a domain.",
        aliases=["pong"],
        usage="orangc.net",
    )
    @lychecks.is_user_app()
    async def ping(self, ctx: commands.Context, host: str | None = None):
        emoji = await lyhelpers.fetch_random_emoji()
        embed = discord.Embed(colour=config.EMBED_COLOUR)

        if host is None:
            latency = round(self._bot.latency * 1000)
            embed.description = f"{emoji} Success! {config.BOT_NAME} is awake. Ping: {latency}ms"
            await ctx.reply(embed=embed, mention_author=False)
            return

        await ctx.defer()
        address = await resolve_address(host)

        # otherwise anyone could probe the network the bot runs on
        if not is_public(address) and not await ctx.bot.is_owner(ctx.author):
            raise lyerrors.TakinaPermissionError("You can only ping public addresses.")

        # the address checked above, not the hostname, so a second lookup cannot land elsewhere
        latency = await asyncio.to_thread(dns_ping, address, unit="ms")
        if not latency:
            raise lyerrors.TakinaError("The specified host timed out.")

        embed.description = f"{emoji} Success! {host} responded with a latency of {int(latency)}ms"
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(description="Check the bot's uptime since the last downtime/restart.")
    @lychecks.is_user_app()
    async def uptime(self, ctx: commands.Context):
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{await lyhelpers.fetch_random_emoji()} {config.BOT_NAME} has been up for {lyhelpers.uptime_fetcher()}."

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="member-count",
        aliases=["mc", "membercount", "members"],
        description="Fetch the server's current member count.",
    )
    @lychecks.guild_only()
    async def member_count(self, ctx: commands.Context):
        assert ctx.guild is not None
        total_count = await lyhelpers.fetch_member_count(ctx.guild)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = "👥 Members"
        embed.description = (
            f"There are currently about **{total_count:,}** members in this guild, bots included."
        )

        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="version", aliases=["v"], description=f"Fetch {config.BOT_NAME}'s current version."
    )
    @lychecks.is_user_app()
    async def version(self, ctx: commands.Context):
        version_link = f"[**{config.BOT_VERSION}**]({config.CHANGELOG_URL})"

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.BOT_NAME} is currently on version {version_link}."
        embed.set_footer(text="For more information, run the info command.")
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utils(bot))
