# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from __future__ import annotations

import nextcord
import config
from nextcord.ext import commands

from ..libs import oclib


async def gary_api(cat: str) -> nextcord.Embed:
    url = f"https://api.garythe.cat/{cat}"
    data = await oclib.request(url)
    image_url = data.get("url")

    embed = nextcord.Embed(color=config.EMBED_COLOR)
    embed.set_image(url=image_url)

    return embed


class Gary(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.command(
        name="gary",
        help="Get a random picture of gary.",
    )
    @commands.has_permissions(embed_links=True)
    async def gary(self, ctx: commands.Context):
        embed = await gary_api("gary")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="goober",
        help="Get a random picture of goober.",
    )
    @commands.has_permissions(embed_links=True)
    async def goober(self, ctx: commands.Context):
        embed = await gary_api("goober")
        await ctx.reply(embed=embed, mention_author=False)


def setup(bot):
    bot.add_cog(Gary(bot))
