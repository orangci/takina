import re
from nextcord.ext import commands
import nextcord
from nextcord import SlashOption
from __main__ import BOT_NAME, EMBED_COLOR
from ..libs.oclib import *


def get_ordinal(n: int) -> str:
    """Helper function to return the ordinal representation of a number."""
    suffix = ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"]
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    else:
        return f"{n}{suffix[n % 10]}"


class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Ping the bot."""
        latency = round(self.bot.latency * 1000)
        await ctx.reply(
            f"Success! {BOT_NAME} is awake. Ping: {latency}ms", mention_author=False
        )

    @commands.command(name="join-position", aliases=["jp", "japan"])
    async def join_position(self, ctx: commands.Context, member: str = None):
        guild = ctx.guild
        if member is None:
            member = ctx.author
        else:
            member = extract_user_id(member, ctx)

        members = sorted(guild.members, key=lambda m: m.joined_at)
        join_position = members.index(member) + 1

        ordinal_position = get_ordinal(join_position)

        if not member == ctx.author:
            embed = nextcord.Embed(
                description=f"**{member}** was the {ordinal_position} to join **{guild.name}**.",
                color=EMBED_COLOR,
            )
        else:
            embed = nextcord.Embed(
                description=f"You were the {ordinal_position} to join **{guild.name}**.",
                color=EMBED_COLOR,
            )
        embed.add_field(
            name="Joined",
            value=f"<t:{int(member.joined_at.timestamp())}:F> (<t:{int(member.joined_at.timestamp())}:R>)",
            inline=False,
        )
        embed.set_thumbnail(url=member.avatar.url or None)

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="member-count", aliases=["mc"])
    async def member_count(self, ctx: commands.Context):
        guild = ctx.guild

        total_members = len([member for member in guild.members if not member.bot])
        total_bots = len([member for member in guild.members if member.bot])
        total_count = guild.member_count

        embed = nextcord.Embed(
            title="👥 Members",
            description=f"There are currently **{total_members}** members and **{total_bots}** bots in this guild.",
            color=EMBED_COLOR,
        )
        embed.set_footer(text=f"Total (members and bots): {total_count}.")
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        await ctx.reply(embed=embed, mention_author=False)


class UtilsSlash(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @nextcord.slash_command(name="ping", description="Ping the bot.")
    async def slash_ping(self, interaction: nextcord.Interaction):
        """Ping the bot."""
        latency = round(self.bot.latency * 1000)
        await interaction.send(
            f"Success! {BOT_NAME} is awake. Ping: {latency}ms", ephemeral=True
        )

    @nextcord.slash_command(name="join-position")
    async def slash_join_position(
        self, interaction: nextcord.Interaction, member: nextcord.Member = None
    ):
        guild = interaction.guild
        if member is None:
            member = interaction.author
        else:
            member = extract_user_id(member, interaction)

        members = sorted(guild.members, key=lambda m: m.joined_at)
        join_position = members.index(member) + 1

        ordinal_position = get_ordinal(join_position)

        if not member == interaction.author:
            embed = nextcord.Embed(
                description=f"**{member}** was the {ordinal_position} to join **{guild.name}**.",
                color=EMBED_COLOR,
            )
        else:
            embed = nextcord.Embed(
                description=f"You were the {ordinal_position} to join **{guild.name}**.",
                color=EMBED_COLOR,
            )
        embed.add_field(
            name="Joined",
            value=f"<t:{int(member.joined_at.timestamp())}:F> (<t:{int(member.joined_at.timestamp())}:R>)",
            inline=False,
        )
        embed.set_thumbnail(url=member.avatar.url or None)

        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="member-count")
    async def slash_member_count(self, interaction: nextcord.Interaction):
        guild = interaction.guild

        total_members = len([member for member in guild.members if not member.bot])
        total_bots = len([member for member in guild.members if member.bot])
        total_count = guild.member_count

        embed = nextcord.Embed(
            title="👥 Members",
            description=f"There are currently **{total_members}** members and **{total_bots}** bots in this guild.",
            color=EMBED_COLOR,
        )
        embed.set_footer(text=f"Total (members and bots): {total_count}.")
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        await interaction.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(Utils(bot))
    bot.add_cog(UtilsSlash(bot))
