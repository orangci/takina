# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyhelpers, lychecks, lymal
from discord.ext import commands


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
        await ctx.defer()
        data = await lymal.search("characters", character)

        name = data.get("name") or "Unknown"
        about = lyhelpers.truncate(data.get("about") or "No information available.", 400)

        names = []
        if (english_name := data.get("name_english")) and english_name != name:
            names.append(english_name)

        if name_kanji := data.get("name_kanji"):
            names.append(name_kanji)

        if nicknames := data.get("nicknames"):
            names.extend(nicknames)

        embed = lymal.entry_embed(data, name)
        embed.description = f"-# {' • '.join(names)}" if names else ""
        embed.description += "\n" + about

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Characters(bot))
