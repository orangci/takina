# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
from ..libs import oclib
import nextcord
import config


class Neko(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    async def request_neko(self, file_format: str, category: str) -> nextcord.Embed:
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        url = f"https://nekos.best/api/v2/{category}"
        data = await oclib.request(url)
        if data.get("code"):
            embed.color = config.ERROR_COLOR
            embed.description = f":x: {category.lower().capitalize()} is not a valid nekos.best endpoint. For a list of available endpoints such as 'kitsune', see the [list of endpoints](https://nekos.best/api/v2/endpoints)."
            return embed

        result = data.get("results", [])[0]

        image_url = result.get("url")
        embed.set_image(url=image_url)

        if file_format == "gif":
            anime_name = result.get("anime_name")
            embed.set_footer(text=f"Anime: {anime_name}")
        elif file_format == "png":
            artist = result.get("artist_name")
            artist_url = result.get("artist_href")
            embed.set_author(name=f"Artist: {artist}", url=artist_url)

        return embed

    @commands.command(name="neko", aliases=["kitsune"], help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.")
    @commands.has_permissions(embed_links=True)
    async def neko(self, ctx: commands.Context, category: str = "neko"):
        if category in ["neko", "kitsune"]:
            file_format = "png"
        else:
            file_format = "gif"
        embed = await self.request_neko(file_format, category)
        await ctx.reply(embed=embed, mention_author=False)


def setup(bot):
    bot.add_cog(Neko(bot))
