# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors, lyhelpers, lychecks
from discord.ext import commands
from takina import config
import discord


class Characters(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(
        aliases=["waifu", "chr"],
        description="Fetch character information from MyAnimeList.",
        usage="Takina",
    )
    @lychecks.is_user_app()
    async def character(self, ctx: commands.Context, *, character: str) -> None:
        data = await lyhelpers.request(
            f"https://api.tenrai.org/v1/characters?q={character}&limit=1"
        )

        if not data or not data.get("data"):
            raise lyerrors.TakinaError("Character not found.")

        data = data["data"][0]
        name = data.get("name", "Unknown")
        english_name = data.get("name_english")
        about = data.get("about") or "No information available."
        about = about[:400] + "..." if len(about) > 400 else about

        embed = discord.Embed(title=name, url=data.get("url"), colour=config.EMBED_COLOUR)
        names = []
        if english_name and english_name != name:
            names.append(english_name)

        if name_kanji := data.get("name_kanji"):
            names.append(name_kanji)

        if nicknames := data.get("nicknames"):
            names.extend(nicknames)

        embed.description = f"-# {' • '.join(names)}" if names else ""
        embed.description += "\n" + about

        if cover_image := data.get("images", {}).get("jpg", {}).get("image_url"):
            embed.set_thumbnail(url=cover_image)

        if mal_id := data.get("mal_id"):
            embed.set_footer(text="MAL ID: " + str(mal_id))

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Characters(bot))
