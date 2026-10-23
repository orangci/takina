# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lymal
from discord.ext import commands


class Manga(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(
        description="Fetch manga information from MyAnimeList.", usage="Call The Name of the Night"
    )
    @lychecks.is_user_app()
    async def manga(self, ctx: commands.Context, *, manga_name: str) -> None:
        await ctx.defer()
        manga = await lymal.search("manga", manga_name)

        title = manga.get("title") or "Unknown"
        status = manga.get("status")
        authors = " & ".join(
            author["name"] for author in manga.get("authors") or [] if author.get("name")
        )

        embed = lymal.entry_embed(manga, title)
        embed.description = ""

        if (english_title := manga.get("title_english")) and english_title != title:
            embed.description = f"-# {english_title}"

        if status != "Publishing":
            embed.description += f"\n> **Chapters**: {lymal.shown(manga.get('chapters'))}"
            embed.description += f"\n> **Volumes**: {lymal.shown(manga.get('volumes'))}"

        embed.description += f"\n> **Score**: {lymal.shown(manga.get('score'))}"
        embed.description += f"\n> **Status**: {lymal.shown(status)}"
        embed.description += f"\n> **Genres**: {lymal.names(manga.get('genres'))}"
        embed.description += (
            f"\n> **Published**: {lymal.shown((manga.get('published') or {}).get('string'))}"
        )
        embed.description += f"\n> **Authors**: {authors or 'Unknown'}"

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        aliases=["mangaplot", "mangasyn"],
        description="Fetch a manga's synopsis from MyAnimeList.",
        usage="The Empty Box and Zeroth Maria",
    )
    @lychecks.is_user_app()
    async def manga_synopsis(self, ctx: commands.Context, *, manga_name: str) -> None:
        await ctx.defer()
        await lymal.send_synopsis(ctx, await lymal.search("manga", manga_name))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Manga(bot))
