import nextcord
from nextcord.ext import commands
from datetime import datetime
import nextcord
from nextcord import Interaction, SlashOption
from __main__ import EMBED_COLOR
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

    @commands.command(aliases=["ani"])
    async def anime(self, ctx: commands.Context, *, anime_name: str):
        """Command for searching anime on MyAnimeList. Usage example: `?anime Lycoris Recoil` or `?anime 50709`."""
        url = f"https://api.jikan.moe/v4/anime?q={anime_name}&limit=1"
        try:
            anime = await self.fetch_anime(anime_name)
            if anime:
                title = anime.get("title")
                episodes = anime.get("episodes")
                # score = anime.get("score")
                # synopsis = anime.get("synopsis")
                # if len(synopsis) > 200:
                #     synopsis = synopsis[:700] + '...'
                source = anime.get("source")
                aired = anime.get("aired", {}).get("string")
                type = anime.get("type")
                rating = anime.get("rating")
                cover_image = anime["images"]["jpg"]["image_url"]
                url = anime.get("url")
                mal_id = anime.get("mal_id")
                genres = ", ".join([genre["name"] for genre in anime.get("genres", [])])
                studios = ", ".join(
                    [studio["name"] for studio in anime.get("studios", [])]
                )

                embed = nextcord.Embed(title=title, url=url, color=EMBED_COLOR)
                embed.add_field(name="Type", value=type, inline=True)
                embed.add_field(name="Episodes", value=episodes, inline=True)
                # embed.add_field(name="Score", value=score, inline=True)
                embed.add_field(name="Source", value=source, inline=True)
                embed.add_field(name="Aired", value=aired, inline=True)
                embed.add_field(name="Genres", value=genres, inline=True)
                embed.add_field(name="Studios", value=studios, inline=True)
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    description="Anime not found.",
                    color=nextcord.Color.red(),
                )

        except Exception as e:
            embed = nextcord.Embed(
                title="Error", description=str(e), color=nextcord.Color.red()
            )
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="anime", description="Get information about an anime")
    async def slash_anime(
        self,
        interaction: Interaction,
        anime_name: str = SlashOption(description="Name of the anime"),
    ):
        """Slash command for searching anime on MyAnimeList. Usage example: `/anime anime_name:Lycoris Recoil`."""
        url = f"https://api.jikan.moe/v4/anime?q={anime_name}&limit=1"
        try:
            anime = await self.fetch_anime(anime_name)
            if anime:
                title = anime.get("title")
                episodes = anime.get("episodes")
                # score = anime.get("score")
                # synopsis = anime.get("synopsis")
                # if len(synopsis) > 200:
                #     synopsis = synopsis[:500] + '...'
                source = anime.get("source")
                aired = anime.get("aired", {}).get("string")
                type = anime.get("type")
                rating = anime.get("rating")
                cover_image = anime["images"]["jpg"]["image_url"]
                url = anime.get("url")
                mal_id = anime.get("mal_id")
                genres = ", ".join([genre["name"] for genre in anime.get("genres", [])])
                studios = ", ".join(
                    [studio["name"] for studio in anime.get("studios", [])]
                )

                embed = nextcord.Embed(title=title, url=url, color=EMBED_COLOR)
                embed.add_field(name="Type", value=type, inline=True)
                embed.add_field(name="Episodes", value=episodes, inline=True)
                # embed.add_field(name="Score", value=score, inline=True)
                embed.add_field(name="Source", value=source, inline=True)
                embed.add_field(name="Aired", value=aired, inline=True)
                embed.add_field(name="Genres", value=genres, inline=True)
                embed.add_field(name="Studios", value=studios, inline=True)
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    description="Anime not found.",
                    color=nextcord.Color.red(),
                )

        except Exception as e:
            embed = nextcord.Embed(
                title="Error", description=str(e), color=nextcord.Color.red()
            )
        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(AnimeSearch(bot))
