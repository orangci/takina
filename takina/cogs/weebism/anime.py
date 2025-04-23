# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
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

    async def build_anime_embed(self, anime_name):
        embed = nextcord.Embed(color=EMBED_COLOR)
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
                return embed

            else:
                embed.description = ":x: Anime not found."
                embed.color = ERROR_COLOR
                return embed

        except Exception as e:
            embed = nextcord.Embed(description=str(e), color=ERROR_COLOR)
            return embed

    async def build_anisyn_embed(self, anime_name):
        embed = nextcord.Embed(color=EMBED_COLOR)
        url = f"https://api.jikan.moe/v4/anime?q={anime_name}&limit=1"
        try:
            anime = await self.fetch_anime(anime_name)
            if anime:
                title = anime.get("title")
                synopsis = anime.get("synopsis")
                if len(synopsis) > 700:
                    synopsis = synopsis[:700] + "..."
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
                return embed

            else:
                embed.description = ":x: Anime not found."
                embed.color = ERROR_COLOR
                return embed

        except Exception as e:
            embed = nextcord.Embed(description=str(e), color=ERROR_COLOR)
            return embed

    @commands.command(
        name="anime",
        aliases=["ani"],
        help="Fetch anime information from MyAnimeList. \nUsage: `anime Lycoris Recoil` or `anime 50709`.",
    )
    async def base_anime(self, ctx: commands.Context, *, anime_name: str):
        embed = await self.build_anime_embed(anime_name)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(
        name="anime", description="MyAnimeList anime information commands."
    )
    async def anime(
        self,
        interaction: nextcord.Interaction,
    ):
        pass

    @anime.subcommand(
        name="info", description="Fetch anime information from MyAnimeList."
    )
    async def slash_anime_info(
        self,
        interaction: Interaction,
        anime_name: str = SlashOption(description="Name of the anime"),
    ):
        await interaction.response.defer()
        embed = await self.build_anime_embed(anime_name)
        await interaction.send(embed=embed)

    @commands.command(
        aliases=["animeplot", "anisyn", "animesyn"],
        help="Fetch a anime's summary from MyAnimeList. \nUsage: `anisyn Lycoris Recoil` or `anisyn 50709`.",
    )
    async def anime_synopsis(self, ctx: commands.Context, *, anime_name: str):
        embed = await self.build_anisyn_embed(anime_name)
        await ctx.reply(embed=embed, mention_author=False)

    @anime.subcommand(
        name="synopsis", description="Fetch an anime's summary from MyAnimeList."
    )
    async def slash_anime_synopsis(
        self,
        interaction: Interaction,
        anime_name: str = SlashOption(description="Name of the anime"),
    ):
        await interaction.response.defer()
        embed = await self.build_anisyn_embed(anime_name)
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(AnimeSearch(bot))
