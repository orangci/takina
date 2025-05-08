# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import nextcord
import config
from nextcord.ext import commands

from ..libs import oclib


async def fetch_stats(ctx: commands.Context or nextcord.Interaction, username: str, category: str):
    slash_command = isinstance(ctx, nextcord.Interaction)
    try:
        profile_data = await oclib.request(f"https://api.jikan.moe/v4/users/{username}")
        if not profile_data or not profile_data.get("data"):
            embed = nextcord.Embed(title="User not found.", color=config.EMBED_COLOR)
            (await ctx.reply(embed=embed, mention_author=False) if not slash_command else await ctx.send(embed=embed, ephemeral=True))
            return

        user = profile_data["data"]
        profile_url = user.get("url")
        profile_pic = user.get("images", {}).get("jpg", {}).get("image_url", "")
        profile_stats = await oclib.request(f"https://api.jikan.moe/v4/users/{username}/statistics")
        category_stats = profile_stats["data"].get(category)

        embed = nextcord.Embed(title=f"{category.lower()} statistics for {username}", url=profile_url, color=config.EMBED_COLOR)

        # Add all available statistics to the embed
        embed.description = ""
        for key, value in category_stats.items():
            embed.description += f"\n> **{key.replace('_', ' ').capitalize()}:** {value}"

        if profile_pic:
            embed.set_thumbnail(url=profile_pic)

    except Exception as e:
        embed = nextcord.Embed(description=str(e), color=config.ERROR_COLOR)
        (await ctx.reply(embed=embed, mention_author=False) if not slash_command else await ctx.send(embed=embed, ephemeral=True))
        return

    (await ctx.reply(embed=embed, mention_author=False) if not slash_command else await ctx.send(embed=embed))


class MAL_Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(help="Fetch a MyAnimeList user's statistics.")
    async def malstats(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = nextcord.Embed(
                description=":x: Please specify either `anime` or `manga`.\nUsage: `malstats <anime/manga> <username>`.", color=config.ERROR_COLOR
            )
            await ctx.reply(embed=embed, mention_author=False)

    @malstats.command(help="Fetch a MyAnimeList user's anime statistics. \nUsage: `malstats anime <username>`.")
    async def anime(self, ctx: commands.Context, *, username: str):
        await fetch_stats(ctx, username, category="anime")

    @malstats.command(help="Fetch a MyAnimeList user's manga statistics. \nUsage: `malstats manga <username>`.")
    async def manga(self, ctx: commands.Context, *, username: str):
        await fetch_stats(ctx, username, category="manga")


class SlashMAL_Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(description="MyAnimeList statistics commands.")
    async def malstats(self, interaction: nextcord.Interaction):
        pass

    @malstats.subcommand(name="anime", description="Fetch a MyAnimeList user's anime statistics.")
    async def malstats_anime(self, interaction: nextcord.Interaction, username: str = nextcord.SlashOption(description="MyAnimeList username")):
        await interaction.response.defer()
        await fetch_stats(interaction, username, category="anime")

    @malstats.subcommand(name="manga", description="Fetch a MyAnimeList user's manga statistics.")
    async def malstats_manga(self, interaction: nextcord.Interaction, username: str = nextcord.SlashOption(description="MyAnimeList username")):
        await interaction.response.defer()
        await fetch_stats(interaction, username, category="manga")


def setup(bot):
    bot.add_cog(MAL_Stats(bot))
    bot.add_cog(SlashMAL_Stats(bot))
