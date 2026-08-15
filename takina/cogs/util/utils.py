# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from ping3 import ping as dns_ping
from discord.ext import commands
from datetime import datetime
from takina import config
import discord
import asyncio


class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(
        description="Ping the bot and check its latency, or ping a domain.",
        aliases=["pong"],
        usage="orangc.net",
    )
    @lychecks.is_user_app()
    async def ping(self, ctx: commands.Context, ip: str | None = None):
        emoji = await lyhelpers.fetch_random_emoji()
        embed = discord.Embed(colour=config.EMBED_COLOUR)

        if ip is None:
            latency = round(self._bot.latency * 1000)
            embed.description = f"{emoji} Success! {config.BOT_NAME} is awake. Ping: {latency}ms"
        else:
            latency = await asyncio.to_thread(dns_ping, ip, unit="ms")

            if latency:
                embed.description = (
                    f"{emoji} Success! {ip} responded with a latency of {int(latency)}ms"
                )
            elif latency is False:
                raise lyerrors.TakinaNotFoundError(
                    "The specified hostname is unknown and could not be resolved."
                )
            else:
                raise lyerrors.TakinaError("The specified host timed out.")

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(description="Check the bot's uptime since the last downtime/restart.")
    @lychecks.is_user_app()
    async def uptime(self, ctx: commands.Context):
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{await lyhelpers.fetch_random_emoji()} {config.BOT_NAME} has been up for {await lyhelpers.uptime_fetcher()}."

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="join-position",
        aliases=["jp", "japan"],
        description="Check a user's join position in the server.",
        usage="@member",
    )
    @lychecks.guild_only()
    async def join_position(self, ctx: commands.Context, member: discord.Member | None = None):
        assert ctx.guild is not None
        if member is None:
            if not isinstance(ctx.author, discord.Member):
                raise lyerrors.TakinaError("This command can only be used in a server.")
            member = ctx.author

        members = sorted(
            (member for member in ctx.guild.members if member.joined_at),
            key=lambda member: member.joined_at or datetime.min,
        )

        join_position = members.index(member) + 1
        ordinal_position = lyhelpers.get_ordinal(join_position)

        embed = discord.Embed(colour=config.EMBED_COLOUR)

        if member == ctx.author:
            embed.description = (
                f"You were the {join_position:,}{ordinal_position} to join **{ctx.guild.name}**."
            )
        else:
            embed.description = f"**{member.mention}** was the {join_position:,}{ordinal_position} to join **{ctx.guild.name}**."

        if member.joined_at:
            joined_at = int(member.joined_at.timestamp())
            embed.add_field(
                name="Joined", value=f"<t:{joined_at}:F> (<t:{joined_at}:R>)", inline=False
            )

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="member-count",
        aliases=["mc", "membercount", "members", "minecraft"],
        description="Fetch the server's current member count.",
    )
    @lychecks.guild_only()
    async def member_count(self, ctx: commands.Context):
        assert ctx.guild is not None

        total_members = sum(not member.bot for member in ctx.guild.members)
        total_bots = sum(member.bot for member in ctx.guild.members)
        total_count = ctx.guild.member_count

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = "👥 Members"
        embed.description = f"There are currently **{total_members:,}** members and **{total_bots:,}** bots in this guild."
        embed.set_footer(text=f"Total (members and bots): {total_count:,}.")

        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="version", aliases=["v"], description=f"Fetch {config.BOT_NAME}'s current version."
    )
    @lychecks.is_user_app()
    async def version(self, ctx: commands.Context):
        version_link = f"[**{config.BOT_VERSION}**](https://git.orangc.net/c/takina/src/branch/master/CHANGELOG.md#{config.BOT_VERSION.replace('.', '-')})"

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.BOT_NAME} is currently on version {version_link}."
        embed.set_footer(text="For more information, run the info command.")
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utils(bot))
