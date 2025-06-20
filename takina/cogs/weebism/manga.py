# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
from ..libs import oclib
import nextcord
import config


class MangaSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_manga(self, manga_name: str):
        url1 = f"https://api.jikan.moe/v4/manga?q={manga_name}&limit=1"
        url2 = f"https://api.jikan.moe/v4/manga/{manga_name}"

        try:
            data = await oclib.request(url2)
            if data and data.get("data"):
                return data["data"]

            data = await oclib.request(url1)
            if data and data.get("data"):
                return data["data"][0]

        except Exception as e:
            raise e

    async def build_manga_embed(self, manga_name):
        url = f"https://api.jikan.moe/v4/manga?q={manga_name}&limit=1"
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        try:
            manga = await self.fetch_manga(manga_name)
            if manga:
                title = manga.get("title")
                chapters = manga.get("chapters")
                volumes = manga.get("volumes")
                score = manga.get("score")
                published = manga.get("published", {}).get("string")
                english_title = manga.get("title_english")
                status = manga.get("status")
                cover_image = manga["images"]["jpg"]["image_url"]
                url = manga.get("url")
                mal_id = manga.get("mal_id")
                genres = ", ".join([genre["name"] for genre in manga.get("genres", [])])
                authors = " & ".join([author["name"] for author in manga.get("authors", [])])

                embed = nextcord.Embed(title=title, url=url, color=config.EMBED_COLOR)
                embed.description = ""
                if english_title and english_title != title:
                    embed.description += f"-# {english_title}\n"
                if status != "Publishing":
                    embed.description += f"\n> **Chapters**: {chapters}"
                    embed.description += f"\n> **Volumes**: {volumes}"
                embed.description += f"\n> **Score**: {score}"
                embed.description += f"\n> **Status**: {status}"
                embed.description += f"\n> **Genres**: {genres}"
                embed.description += f"\n> **Published**: {published}"
                embed.description += f"\n> **Authors**: {authors}"
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))
                return embed

            else:
                embed.description = ":x: Manga not found."
                embed.color = config.ERROR_COLOR

        except Exception as e:
            embed = nextcord.Embed(description=str(e), color=config.ERROR_COLOR)
            return embed

    async def build_mangasyn_embed(self, manga_name):
        url = f"https://api.jikan.moe/v4/manga?q={manga_name}&limit=1"
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        try:
            manga = await self.fetch_manga(manga_name)
            if manga:
                title = manga.get("title")
                english_title = manga.get("title_english")
                cover_image = manga["images"]["jpg"]["image_url"]
                url = manga.get("url")
                mal_id = manga.get("mal_id")
                synopsis = manga.get("synopsis")
                if len(synopsis) > 700:
                    synopsis = synopsis[:700] + "..."

                embed = nextcord.Embed(title=title, url=url, color=config.EMBED_COLOR)
                embed.description = ""
                if english_title and english_title != title:
                    embed.description += f"-# {english_title}\n"
                embed.description += f"\n{synopsis}"
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))
                return embed

            else:
                embed.description = ":x: Manga not found."
                embed.color = config.ERROR_COLOR
                return embed

        except Exception as e:
            embed = nextcord.Embed(description=str(e), color=config.ERROR_COLOR)
            return embed

    @commands.command(
        name="manga",
        help="Fetch manga information from MyAnimeList. You may specify a manga name or its ID in the MAL database.",
        usage="Lycoris Recoil",
    )
    async def base_manga(self, ctx: commands.Context, *, manga_name: str):
        embed = await self.build_manga_embed(manga_name)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="manga", description="MyAnimeList manga information commands.")
    async def manga(self, interaction: nextcord.Interaction):
        pass

    @manga.subcommand(name="info", description="Fetch manga information from MyAnimeList.")
    async def slash_manga_info(self, interaction: Interaction, manga_name: str = SlashOption(description="Name of the manga")):
        await interaction.response.defer()
        embed = await self.build_manga_embed(manga_name)
        await interaction.send(embed=embed)

    @commands.command(
        aliases=["mangaplot", "mangasyn"],
        help="Fetch a manga's summary from MyAnimeList. You may specify a manga name or its ID in the MAL database.",
        usage="Lycoris Recoil",
    )
    async def manga_synopsis(self, ctx: commands.Context, *, manga_name: str):
        embed = await self.build_mangasyn_embed(manga_name)
        await ctx.reply(embed=embed, mention_author=False)

    @manga.subcommand(name="synopsis", description="Fetch a manga's summary from MyAnimeList.")
    async def slash_manga_synopsis(self, interaction: Interaction, manga_name: str = SlashOption(description="Name of the manga")):
        await interaction.response.defer()
        embed = await self.build_mangasyn_embed(manga_name)
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(MangaSearch(bot))
