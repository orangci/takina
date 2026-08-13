# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyhelpers, lyerrors
from discord.ext import commands
from takina import config
import discord


class Neko(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.hybrid_command(
        name="neko",
        aliases=["kitsune"],
        description="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @lychecks.has_permissions(embed_links=True)
    @lychecks.is_user_app()
    async def neko(self, ctx: commands.Context, category: str = "neko"):
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        data = await lyhelpers.request(f"https://nekos.best/api/v2/{category}")
        if not data:
            raise lyerrors.TakinaUserInputError(
                f"{category.lower().capitalize()} is not a valid [nekos.best](https://nekos.best) endpoint. For a list of available endpoints such as 'kitsune', see the [list of endpoints](https://nekos.best/api/v2/endpoints)."
            )

        result = data.get("results", [])[0]
        embed.set_image(url=result.get("url"))

        # for PNG file formats
        if category in ["neko", "kitsune"]:
            artist = result.get("artist_name")
            artist_url = result.get("artist_href")
            embed.set_author(name=f"Artist: {artist}", url=artist_url)

        # for GIFs
        else:
            anime_name = result.get("anime_name")
            embed.set_footer(text=f"Anime: {anime_name}")

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Neko(bot))
