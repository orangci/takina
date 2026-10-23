# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from discord.ext import commands
from takina import config
import discord


class Ias(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def request_api(self, ctx: commands.Context, endpoint: str) -> None:
        data = await lyhelpers.request(f"https://api.iostpa.com/{endpoint}")
        if not (image_link := data.get("image_link")):
            raise lyerrors.TakinaError("The image service returned no image.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.set_image(url=image_link)
        embed.set_author(name="Source", url=data.get("twitter_link"))

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        aliases=["umamusume"],
        description="Fetch a random Uma Musume. Utilises [iostpa's](https://api.iostpa.com) API.",
    )
    @lychecks.has_permissions(embed_links=True)
    @lychecks.is_user_app()
    async def uma(self, ctx: commands.Context):
        await self.request_api(ctx, "uma")

    @commands.hybrid_command(
        aliases=["2hu"],
        description="Fetch a random Touhou. Utilises [iostpa's](https://api.iostpa.com) API.",
    )
    @lychecks.has_permissions(embed_links=True)
    @lychecks.is_user_app()
    async def touhou(self, ctx: commands.Context):
        await self.request_api(ctx, "touhou")


async def setup(bot: commands.Bot):
    await bot.add_cog(Ias(bot))
