from ..libs.oclib import *
import nextcord
from nextcord.ext import commands
from config import *


class MAL_Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(help="Fetch MyAnimeList user's statistics.")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def malstats(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = nextcord.Embed(
                description="Please specify either `anime` or `manga`.\nUsage: `malstats <anime/manga> <username>`.",
                color=ERROR_COLOR,
            )
            await ctx.reply(embed=embed, mention_author=False)

    @malstats.command(
        help="Fetch a MyAnimeList user's anime statistics. \nUsage: `malstats anime <username>`."
    )
    async def anime(self, ctx: commands.Context, *, username: str):
        await self.fetch_stats(ctx, username, category="anime")

    @malstats.command(
        help="Fetch a MyAnimeList user's manga statistics. \nUsage: `malstats manga <username>`."
    )
    async def manga(self, ctx: commands.Context, *, username: str):
        await self.fetch_stats(ctx, username, category="manga")

    async def fetch_stats(self, ctx: commands.Context, username: str, category: str):
        try:
            profile_data = await request(f"https://api.jikan.moe/v4/users/{username}")
            if not profile_data or not profile_data.get("data"):
                embed = nextcord.Embed(title="User not found.", color=EMBED_COLOR)
                await ctx.reply(embed=embed, mention_author=False)
                return

            user = profile_data["data"]
            profile_url = user.get("url")
            profile_pic = user.get("images", {}).get("jpg", {}).get("image_url", "")
            profile_stats = await request(
                f"https://api.jikan.moe/v4/users/{username}/statistics"
            )
            category_stats = profile_stats["data"].get(category)

            embed = nextcord.Embed(
                title=username,
                url=profile_url,
                color=EMBED_COLOR,
            )

            # Add all available statistics to the embed
            embed.description = ""
            for key, value in category_stats.items():
                embed.description += (
                    f"\n> **{key.replace('_', ' ').capitalize()}:** {value}"
                )

            if profile_pic:
                embed.set_thumbnail(url=profile_pic)

        except Exception as e:
            embed = nextcord.Embed(description=str(e), color=ERROR_COLOR)

        await ctx.reply(embed=embed, mention_author=False)


class SlashMAL_Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(description="Fetch MyAnimeList user's anime statistics.")
    async def malstats_anime(
        self,
        interaction: nextcord.Interaction,
        username: str = nextcord.SlashOption(description="MyAnimeList username"),
    ):
        await self.fetch_stats(interaction, username, category="anime")

    @nextcord.slash_command(description="Fetch MyAnimeList user's manga statistics.")
    async def malstats_manga(
        self,
        interaction: nextcord.Interaction,
        username: str = nextcord.SlashOption(description="MyAnimeList username"),
    ):
        await self.fetch_stats(interaction, username, category="manga")

    async def fetch_stats(
        self, interaction: nextcord.Interaction, username: str, category: str
    ):
        try:
            profile_data = await request(f"https://api.jikan.moe/v4/users/{username}")
            if not profile_data or not profile_data.get("data"):
                embed = nextcord.Embed(title="User not found.", color=EMBED_COLOR)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            user = profile_data["data"]
            profile_url = user.get("url")
            profile_pic = user.get("images", {}).get("jpg", {}).get("image_url", "")
            profile_stats = await request(
                f"https://api.jikan.moe/v4/users/{username}/statistics"
            )
            category_stats = profile_stats["data"].get(category)

            embed = nextcord.Embed(
                title=username,
                url=profile_url,
                color=EMBED_COLOR,
            )

            # Add all available statistics to the embed
            embed.description = ""
            for key, value in category_stats.items():
                embed.description += (
                    f"\n> **{key.replace('_', ' ').capitalize()}:** {value}"
                )

            if profile_pic:
                embed.set_thumbnail(url=profile_pic)

        except Exception as e:
            embed = nextcord.Embed(description=str(e), color=ERROR_COLOR)

        await interaction.response.send_message(embed=embed, ephemeral=False)


def setup(bot):
    bot.add_cog(MAL_Stats(bot))
    bot.add_cog(SlashMAL_Stats(bot))
