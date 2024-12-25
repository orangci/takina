import nextcord
from nextcord.ext import commands
import nextcord
from nextcord import Interaction, SlashOption
from config import *
from ..libs.oclib import *


class AnimeSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_anime(self, anime_name: str):
        url1 = f"https://api.jikan.moe/v4/anime?q={anime_name}&limit=1"
        url2 = f"https://api.jikan.moe/v4/anime/{anime_name}"

        try:
            data = await request(url2)
            if data and data.get("data"):
                return data["data"]

            data = await request(url1)
            if data and data.get("data"):
                return data["data"][0]

        except Exception as e:
            raise e

    @commands.command(
        aliases=["ani"],
        help="Fetch anime information from MyAnimeList. \nUsage: `anime Lycoris Recoil` or `anime 50709`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def anime(self, ctx: commands.Context, *, anime_name: str):
        url = f"https://api.jikan.moe/v4/anime?q={anime_name}&limit=1"
        try:
            anime = await self.fetch_anime(anime_name)
            if anime:
                title = anime.get("title")
                episodes = anime.get("episodes")
                score = anime.get("score")
                synopsis = anime.get("synopsis")
                source = anime.get("source")
                english_title = anime.get("title_english")
                aired = anime.get("aired", {}).get("string")
                type = anime.get("type")
                cover_image = anime["images"]["jpg"]["image_url"]
                url = anime.get("url")
                rating = anime.get("rating")
                mal_id = anime.get("mal_id")
                genres = ", ".join([genre["name"] for genre in anime.get("genres", [])])
                studios = ", ".join(
                    [studio["name"] for studio in anime.get("studios", [])]
                )

                embed = nextcord.Embed(title=title, url=url, color=EMBED_COLOR)
                embed.description = ""
                if english_title and english_title != title:
                    embed.description += f"-# {english_title}\n"
                embed.description += f"\n> **Type**: {type}"
                embed.description += f"\n> **Episodes**: {episodes}"
                embed.description += f"\n> **Score**: {score}"
                embed.description += f"\n> **Source**: {source}"
                embed.description += f"\n> **Aired**: {aired}"
                embed.description += f"\n> **Genres**: {genres}"
                embed.description += f"\n> **Studios**: {studios}"
                embed.description += f"\n> **Rating**: {rating}"
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    description=":x: Anime not found.",
                    color=ERROR_COLOR,
                )

        except Exception as e:
            embed = nextcord.Embed(description=str(e), color=ERROR_COLOR)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(
        name="anime", description="Fetch anime information from MyAnimeList."
    )
    async def slash_anime(
        self,
        interaction: Interaction,
        anime_name: str = SlashOption(description="Name of the anime"),
    ):
        url = f"https://api.jikan.moe/v4/anime?q={anime_name}&limit=1"
        try:
            anime = await self.fetch_anime(anime_name)
            if anime:
                title = anime.get("title")
                episodes = anime.get("episodes")
                score = anime.get("score")
                synopsis = anime.get("synopsis")
                source = anime.get("source")
                english_title = anime.get("title_english")
                aired = anime.get("aired", {}).get("string")
                type = anime.get("type")
                cover_image = anime["images"]["jpg"]["image_url"]
                url = anime.get("url")
                rating = anime.get("rating")
                mal_id = anime.get("mal_id")
                genres = ", ".join([genre["name"] for genre in anime.get("genres", [])])
                studios = ", ".join(
                    [studio["name"] for studio in anime.get("studios", [])]
                )

                embed = nextcord.Embed(title=title, url=url, color=EMBED_COLOR)
                embed.description = ""
                if english_title and english_title != title:
                    embed.description += f"-# {english_title}\n"
                embed.description += f"\n> **Type**: {type}"
                embed.description += f"\n> **Episodes**: {episodes}"
                embed.description += f"\n> **Score**: {score}"
                embed.description += f"\n> **Source**: {source}"
                embed.description += f"\n> **Aired**: {aired}"
                embed.description += f"\n> **Genres**: {genres}"
                embed.description += f"\n> **Studios**: {studios}"
                embed.description += f"\n> **Rating**: {rating}"
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    description=":x: Anime not found.",
                    color=ERROR_COLOR,
                )

        except Exception as e:
            embed = nextcord.Embed(description=str(e), color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed)


class AnimeSynopsis(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_anime(self, anime_name: str):
        url1 = f"https://api.jikan.moe/v4/anime?q={anime_name}&limit=1"
        url2 = f"https://api.jikan.moe/v4/anime/{anime_name}"

        try:
            data = await request(url2)
            if data and data.get("data"):
                return data["data"]

            data = await request(url1)
            if data and data.get("data"):
                return data["data"][0]

        except Exception as e:
            raise e

    @commands.command(
        aliases=["animeplot", "anisyn", "animesyn"],
        help="Fetch anime information from MyAnimeList. \nUsage: `anisyn Lycoris Recoil` or `anisyn 50709`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def anime_synopsis(self, ctx: commands.Context, *, anime_name: str):
        url = f"https://api.jikan.moe/v4/anime?q={anime_name}&limit=1"
        try:
            anime = await self.fetch_anime(anime_name)
            if anime:
                title = anime.get("title")
                synopsis = anime.get("synopsis")
                if len(synopsis) > 700:
                    synopsis = synopsis[:700] + '...'
                english_title = anime.get("title_english")
                cover_image = anime["images"]["jpg"]["image_url"]
                url = anime.get("url")
                mal_id = anime.get("mal_id")

                embed = nextcord.Embed(title=title, url=url, color=EMBED_COLOR)
                embed.description = ""
                if english_title and english_title != title:
                    embed.description += f"-# {english_title}\n"
                embed.description += f"\n{synopsis}"
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    description=":x: Anime not found.",
                    color=ERROR_COLOR,
                )

        except Exception as e:
            embed = nextcord.Embed(description=str(e), color=ERROR_COLOR)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(
        name="anime_synopsis", description="Fetch anime information from MyAnimeList."
    )
    async def slash_anime_synopsis(
        self,
        interaction: Interaction,
        anime_name: str = SlashOption(description="Name of the anime"),
    ):
        url = f"https://api.jikan.moe/v4/anime?q={anime_name}&limit=1"
        try:
            anime = await self.fetch_anime(anime_name)
            if anime:
                title = anime.get("title")
                synopsis = anime.get("synopsis")
                if len(synopsis) > 700:
                    synopsis = synopsis[:700] + '...'
                english_title = anime.get("title_english")
                cover_image = anime["images"]["jpg"]["image_url"]
                url = anime.get("url")
                mal_id = anime.get("mal_id")

                embed = nextcord.Embed(title=title, url=url, color=EMBED_COLOR)
                embed.description = ""
                if english_title and english_title != title:
                    embed.description += f"-# {english_title}\n"
                embed.description += f"\n{synopsis}"
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    description=":x: Anime not found.",
                    color=ERROR_COLOR,
                )

        except Exception as e:
            embed = nextcord.Embed(description=str(e), color=ERROR_COLOR)
        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(AnimeSearch(bot))
    bot.add_cog(AnimeSynopsis(bot))
