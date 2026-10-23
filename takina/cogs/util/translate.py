# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from discord.ext import commands
from takina import config
import discord

# both texts share one embed description, which holds 4096 characters
MAX_TEXT_LENGTH = 2000


class Translate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        # casefolded code to the instance's spelling, e.g. "zh-hans" to "zh-Hans"; fetched once
        self._languages: dict[str, str] | None = None

    async def languages(self) -> dict[str, str]:
        if self._languages is None:
            data = await lyhelpers.request(f"{config.LIBRETRANSLATE_API_URL}/languages")
            self._languages = {language["code"].casefold(): language["code"] for language in data}

        return self._languages

    async def parse_languages(self, lang: str) -> tuple[str, str]:
        languages = await self.languages()

        if target := languages.get(lang.casefold()):
            return "auto", target

        # codes such as zh-Hans hold a dash themselves, so try every place to split
        for index, character in enumerate(lang):
            if character != "-":
                continue

            source = languages.get(lang[:index].casefold())
            target = languages.get(lang[index + 1 :].casefold())
            if source and target:
                return source, target

        raise lyerrors.TakinaUserInputError(
            f"Unknown language: `{lang.replace('`', '')[:50]}`. Use `from-to`, e.g. `en-ar` for English to Arabic, or just the target language."
        )

    @commands.hybrid_command(
        name="translate",
        aliases=["tl"],
        description="Translate text from one language to another.",
        usage="en-ar peace be upon you",
    )
    @lychecks.is_user_app()
    async def translate(
        self, ctx: commands.Context, lang: str, *, text: commands.Range[str, 1, MAX_TEXT_LENGTH]
    ):
        await ctx.defer()

        source, target = await self.parse_languages(lang)
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
        embed.description += (
            f"\n> **Translation**: {lyhelpers.truncate(translated_text, MAX_TEXT_LENGTH)}"
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    if not config.LIBRETRANSLATE_API_URL:
        raise lyerrors.TakinaMissingEnvironmentVariableError(
            "LIBRETRANSLATE_API_URL has not been set."
        )

    await bot.add_cog(Translate(bot))
