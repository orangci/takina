# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors, lyhelpers, lychecks, lyviews
from discord.ext import commands
from takina import config
import discord


class Anime(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    async def fetch_anime(self, anime_name: str) -> dict | None:
        data = await lyhelpers.request(f"https://api.tenrai.org/v1/anime?q={anime_name}&limit=1")
        if data and data.get("data"):
            return data["data"][0]

        return None

    @commands.hybrid_command(
        aliases=["ani"],
        description="Fetch anime information from MyAnimeList.",
        usage="Lycoris Recoil",
    )
    @lychecks.is_user_app()
    async def anime(self, ctx: commands.Context, *, anime_name: str) -> None:
        anime = await self.fetch_anime(anime_name)
        if not anime:
            raise lyerrors.TakinaError("Anime not found.")

        title = anime.get("title", "Unknown")
        english_title = anime.get("title_english")
        cover_image = anime.get("images", {}).get("jpg", {}).get("image_url")
        genres = ", ".join(genre["name"] for genre in anime.get("genres", []))
        studios = ", ".join(studio["name"] for studio in anime.get("studios", []))
        mal_id = anime.get("mal_id")

        embed = discord.Embed(title=title, url=anime.get("url"), colour=config.EMBED_COLOUR)

        if english_title and english_title != title:
            embed.description = f"-# {english_title}"

        embed.description = embed.description or ""
        embed.description += f"\n> **Type**: {anime.get('type')}"
        embed.description += f"\n> **Episodes**: {anime.get('episodes')}"
        embed.description += f"\n> **Score**: {anime.get('score')}"
        embed.description += f"\n> **Source**: {anime.get('source')}"
        embed.description += f"\n> **Aired**: {anime.get('aired', {}).get('string')}"
        embed.description += f"\n> **Genres**: {genres}"
        embed.description += f"\n> **Studios**: {studios}"
        embed.description += f"\n> **Rating**: {anime.get('rating')}"

        if cover_image:
            embed.set_thumbnail(url=cover_image)

        if mal_id:
            embed.set_footer(text="MAL ID: " + str(mal_id))

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        aliases=["animeplot", "animesyn", "anisyn"],
        description="Fetch an anime's synopsis from MyAnimeList.",
        usage="Lycoris Recoil",
    )
    @lychecks.is_user_app()
    async def anime_synopsis(self, ctx: commands.Context, *, anime_name: str) -> None:
        anime = await self.fetch_anime(anime_name)

        if not anime:
            raise lyerrors.TakinaError("Anime not found.")

        title = anime.get("title", "Unknown")
        english_title = anime.get("title_english")
        synopsis = anime.get("synopsis") or "No synopsis available."
        url = anime.get("url")
        mal_id = anime.get("mal_id")
        cover_image = anime.get("images", {}).get("jpg", {}).get("image_url")

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
    await bot.add_cog(Anime(bot))
