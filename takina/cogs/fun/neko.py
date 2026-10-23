# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from discord import app_commands
from discord.ext import commands
from takina import config
import discord
import aiohttp

API_URL = "https://nekos.best/api/v2"


class Neko(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        # endpoint name to image format, fetched once
        self._endpoints: dict[str, str] | None = None

    async def endpoints(self) -> dict[str, str]:
        if self._endpoints is None:
            data = await lyhelpers.request(f"{API_URL}/endpoints")
            self._endpoints = {name: info.get("format", "") for name, info in data.items()}

        return self._endpoints

    @commands.hybrid_command(
        name="neko",
        aliases=["kitsune"],
        description="Fetch a GIF or image from nekos.best.",
        usage="kitsune",
    )
    @lychecks.has_permissions(embed_links=True)
    @lychecks.is_user_app()
    async def neko(self, ctx: commands.Context, category: str | None = None):
        # the kitsune alias asks for kitsunes
        category = (category or ("kitsune" if ctx.invoked_with == "kitsune" else "neko")).lower()

        endpoints = await self.endpoints()
        if category not in endpoints:
            raise lyerrors.TakinaNotFoundError(
                f"`{category.replace('`', '')[:50]}` is not a valid [nekos.best](https://nekos.best) endpoint. For a list of available endpoints such as `kitsune`, see the [list of endpoints]({API_URL}/endpoints)."
            )

        data = await lyhelpers.request(f"{API_URL}/{category}")
        if not (results := data.get("results")) or not (url := results[0].get("url")):
            raise lyerrors.TakinaNotFoundError("nekos.best returned nothing for that endpoint.")

        result = results[0]
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.set_image(url=url)

        # still images credit an artist, gifs name their anime
        if endpoints[category] == "png":
            embed.set_author(
                name=f"Artist: {result.get('artist_name')}", url=result.get("artist_href")
            )
        else:
            embed.set_footer(text=f"Anime: {result.get('anime_name')}")

        await ctx.reply(embed=embed, mention_author=False)

    @neko.autocomplete("category")
    async def category_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        try:
            endpoints = await self.endpoints()
        except (lyerrors.TakinaError, aiohttp.ClientError, TimeoutError):
            # a failed lookup should leave the box empty, not raise in the user's face
            return []

        matches = [name for name in sorted(endpoints) if current.lower() in name]
        return [app_commands.Choice(name=name, value=name) for name in matches[:25]]


async def setup(bot: commands.Bot):
    await bot.add_cog(Neko(bot))
