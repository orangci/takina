# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
import nextcord
import config
import aiohttp
import re


class Translate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def translate_text(self, lang: str, text: str) -> nextcord.Embed:
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        source, target = lang.split("-", 1) if "-" in lang else "auto", lang
        payload = {"q": text, "source": source, "target": target, "api_key": config.LIBRETRANSLATE_API_KEY}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{config.LIBRETRANSLATE_API_URL}/translate", json=payload) as resp:
                data = await resp.json()
                if resp.status != 200:
                    error = data.get("error") or f"API responded with status {resp.status}"
                    embed.color = config.ERROR_COLOR
                    embed.description = f":x: Translation failed: {error}."
                    return embed

        embed.description = f"> **Original**: {text}\n> **Translation**: {data.get('translatedText')}"
        return embed

    def validate_lang(self, lang: str) -> bool:
        return bool(re.compile(r"^[a-z]{2}(-[a-z]{2})?$").match(lang))

    @commands.command(name="translate", aliases=["tl"], help="Translate text", usage="en-ar hello world OR ar hello world")
    async def translate(self, ctx: commands.Context, lang: str, *, text: str):
        if not self.validate_lang(lang):
            embed = nextcord.Embed(color=config.ERROR_COLOR)
            embed.description = f":x: Invalid language format: `{lang}`. Use `from-to`, e.g. `en-ar` for English to Arabic."
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = await self.translate_text(lang, text)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="translate", description="Translate text from one language to another.")
    async def slash_translate(
        self,
        interaction: nextcord.Interaction,
        lang: str = nextcord.SlashOption(required=True, description="The language you want to translate to, e.g. ar for Arabic"),
        text: str = nextcord.SlashOption(required=True, description="The text you wish to translate"),
    ):
        if not self.validate_lang(lang):
            embed = nextcord.Embed(color=config.ERROR_COLOR)
            embed.description = f":x: Invalid language format: `{lang}`. Use `from-to`, e.g. `en-ar` for English to Arabic."
            await interaction.send(embed=embed)
            return

        embed = await self.translate_text(lang, text)
        await interaction.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Translate(bot))
