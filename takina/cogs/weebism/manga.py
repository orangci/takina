# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors, lyhelpers, lychecks, lyviews
from discord.ext import commands
from takina import config
import discord


class Manga(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    async def fetch_manga(self, manga_name: str) -> dict | None:
        data = await lyhelpers.request(f"https://api.tenrai.org/v1/manga?q={manga_name}&limit=1")
        if data and data.get("data"):
            return data["data"][0]

        return None

    @commands.hybrid_command(
        description="Fetch manga information from MyAnimeList.", usage="Call The Name of the Night"
    )
    @lychecks.is_user_app()
    async def manga(self, ctx: commands.Context, *, manga_name: str) -> None:
        manga = await self.fetch_manga(manga_name)
        if not manga:
            raise lyerrors.TakinaError("Manga not found.")

        title = manga.get("title", "Unknown")
        english_title = manga.get("title_english")
        cover_image = manga.get("images", {}).get("jpg", {}).get("image_url")
        genres = ", ".join(genre["name"] for genre in manga.get("genres", []))
        authors = " & ".join(author["name"] for author in manga.get("authors", []))
        mal_id = manga.get("mal_id")
        status = manga.get("status")

        embed = discord.Embed(title=title, url=manga.get("url"), colour=config.EMBED_COLOUR)

        if english_title and english_title != title:
            embed.description = f"-# {english_title}"

        embed.description = embed.description or ""

        if status != "Publishing":
            embed.description += f"\n> **Chapters**: {manga.get('chapters')}"
            embed.description += f"\n> **Volumes**: {manga.get('volumes')}"

        embed.description += f"\n> **Score**: {manga.get('score')}"
        embed.description += f"\n> **Status**: {status}"
        embed.description += f"\n> **Genres**: {genres}"
        embed.description += f"\n> **Published**: {manga.get('published', {}).get('string')}"
        embed.description += f"\n> **Authors**: {authors}"

        if cover_image:
            embed.set_thumbnail(url=cover_image)

        if mal_id:
            embed.set_footer(text="MAL ID: " + str(mal_id))

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        aliases=["mangaplot", "mangasyn"],
        description="Fetch a manga's synopsis from MyAnimeList.",
        usage="The Empty Box and Zeroth Maria",
    )
    @lychecks.is_user_app()
    async def manga_synopsis(self, ctx: commands.Context, *, manga_name: str) -> None:
        manga = await self.fetch_manga(manga_name)

        if not manga:
            raise lyerrors.TakinaError("Manga not found.")

        title = manga.get("title", "Unknown")
        english_title = manga.get("title_english")
        synopsis = manga.get("synopsis") or "No synopsis available."
        url = manga.get("url")
        mal_id = manga.get("mal_id")
        cover_image = manga.get("images", {}).get("jpg", {}).get("image_url")

        if english_title and english_title != title:
            synopsis = f"-# {english_title}\n\n{synopsis}"

        if len(synopsis) <= 500:
            embed = discord.Embed(title=title, url=url, colour=config.EMBED_COLOUR)
            embed.description = synopsis

            if cover_image:
                embed.set_thumbnail(url=cover_image)

            if mal_id:
                embed.set_footer(text="MAL ID: " + str(mal_id))

            await ctx.reply(embed=embed, mention_author=False)
            return

        embeds = []

        for index in range(0, len(synopsis), 500):
            embed = discord.Embed(title=title, url=url, colour=config.EMBED_COLOUR)
            embed.description = synopsis[index : index + 500]

            if cover_image:
                embed.set_thumbnail(url=cover_image)

            if mal_id:
                embed.set_footer(text="MAL ID: " + str(mal_id))

            embeds.append(embed)

        view = lyviews.PaginatorView(ctx.author, embeds)
        view.message = await ctx.reply(embed=embeds[0], view=view, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Manga(bot))
