# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from discord.ext import commands
from takina import config
import discord
import re


class Translate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_command(
        name="translate",
        aliases=["tl"],
        description="Translate text from one language to another.",
        usage="en-ar peace be upon you",
    )
    @lychecks.is_user_app()
    async def translate(self, ctx: commands.Context, lang: str, *, text: str):
        if not re.fullmatch(r"[a-z]{2}(?:-[a-z]{2})?", lang):
            raise lyerrors.TakinaUserInputError(
                f"Invalid language format: `{lang}`. Use `from-to`, e.g. `en-ar` for English to Arabic."
            )

        source, target = ("auto", lang) if "-" not in lang else lang.split("-", 1)
        data = await lyhelpers.request(
            f"{config.LIBRETRANSLATE_API_URL}/translate",
            method="POST",
            json={
                "q": text,
                "source": source,
                "target": target,
                "api_key": config.LIBRETRANSLATE_API_KEY,
            },
        )

        if error := data.get("error"):
            raise lyerrors.TakinaError(f"Translation failed: {error}.")

        if not (translated_text := data.get("translatedText")):
            raise lyerrors.TakinaError("Translation failed.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"> **Original**: {text}"
        embed.description += f"\n> **Translation**: {translated_text}"
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    if not config.LIBRETRANSLATE_API_URL:
        raise lyerrors.TakinaMissingEnvironmentVariableError(
            "LIBRETRANSLATE_API_URL has not been set."
        )

    await bot.add_cog(Translate(bot))
