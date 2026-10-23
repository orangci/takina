# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lymal
from discord.ext import commands


class Anime(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(
        aliases=["ani"],
        description="Fetch anime information from MyAnimeList.",
        usage="Lycoris Recoil",
    )
    @lychecks.is_user_app()
    async def anime(self, ctx: commands.Context, *, anime_name: str) -> None:
        await ctx.defer()
        anime = await lymal.search("anime", anime_name)

        title = anime.get("title") or "Unknown"
        embed = lymal.entry_embed(anime, title)
        embed.description = ""

        if (english_title := anime.get("title_english")) and english_title != title:
            embed.description = f"-# {english_title}"

        embed.description += f"\n> **Type**: {lymal.shown(anime.get('type'))}"
        embed.description += f"\n> **Episodes**: {lymal.shown(anime.get('episodes'))}"
        embed.description += f"\n> **Score**: {lymal.shown(anime.get('score'))}"
        embed.description += f"\n> **Source**: {lymal.shown(anime.get('source'))}"
        embed.description += (
            f"\n> **Aired**: {lymal.shown((anime.get('aired') or {}).get('string'))}"
        )
        embed.description += f"\n> **Genres**: {lymal.names(anime.get('genres'))}"
        embed.description += f"\n> **Studios**: {lymal.names(anime.get('studios'))}"
        embed.description += f"\n> **Rating**: {lymal.shown(anime.get('rating'))}"

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        aliases=["animeplot", "animesyn", "anisyn"],
        description="Fetch an anime's synopsis from MyAnimeList.",
        usage="Lycoris Recoil",
    )
    @lychecks.is_user_app()
    async def anime_synopsis(self, ctx: commands.Context, *, anime_name: str) -> None:
        await ctx.defer()
        await lymal.send_synopsis(ctx, await lymal.search("anime", anime_name))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Anime(bot))
