from nextcord.ext import commands
import nextcord
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

    @commands.command(
        description="Ping the bot and check its latency.", help="Usage: `ping`."
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def ping(self, ctx: commands.Context):
        latency = round(self.bot.latency * 1000)
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            description=f"{emoji} Success! {BOT_NAME} is awake. Ping: {latency}ms",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="join-position",
        aliases=["jp", "japan"],
        description="Check a user's join position in the server.",
        help="Usage: `jp <member>`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def join_position(self, ctx: commands.Context, member: str = None):
        guild = ctx.guild
        if member is None:
            member = ctx.author
        else:
            member = extract_user_id(member, ctx)
            if isinstance(member, str):
                embed = nextcord.Embed(description=member, color=0xFF0037)
                await ctx.reply(embed=embed, mention_author=False)
                return

        members = sorted(guild.members, key=lambda m: m.joined_at)
        join_position = members.index(member) + 1

        ordinal_position = get_ordinal(join_position)

        if not member == ctx.author:
            embed = nextcord.Embed(
                description=f"**{member.mention}** was the {ordinal_position} to join **{guild.name}**.",
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
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="member-count",
        aliases=["mc"],
        description="Fetch the server's current member count.",
        help="Usage: `mc`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
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
        latency = round(self.bot.latency * 1000)
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            description=f"{emoji} Success! {BOT_NAME} is awake. Ping: {latency}ms",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(
        name="join-position", description="Fetch a user's join position in the server."
    )
    async def slash_join_position(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(
            description="The member whose join position you want to check",
            required=False,
        ),
    ):
        guild = interaction.guild
        if member is None:
            member = interaction.user

        members = sorted(guild.members, key=lambda m: m.joined_at)
        join_position = members.index(member) + 1

        ordinal_position = get_ordinal(join_position)

        if not member == interaction.user:
            embed = nextcord.Embed(
                description=f"**{member.mention}** was the {ordinal_position} to join **{guild.name}**.",
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
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(
        name="member-count", description="Fetch the server's current member count."
    )
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
