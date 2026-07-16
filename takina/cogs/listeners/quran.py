# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
from ..libs import oclib
import nextcord
import config
import re


class Quran(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.QURAN_REGEX = re.compile(r"\b(?:quran|qur'an|koran|coran)\s*\(?(\d{1,3}):(\d{1,3})\)?", re.IGNORECASE)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return

        match = self.QURAN_REGEX.search(message.content)

        if match is None:
            return

        surah = int(match.group(1))
        ayah = int(match.group(2))

        if not (1 <= surah <= 114):
            return

        try:
            english_data = await oclib.request(f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/en.hilali")

        except Exception:
            return

        if english_data.get("code") != 200:
            return

        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed.title = f"The Holy Qu'rān, Āyah {ayah} of Surah {english_data['data']['surah']['englishName']} ({english_data['data']['surah']['englishNameTranslation']})"
        embed.description = english_data["data"]["text"]
        embed.set_footer(text="English translation by Hilali & Khan")

        await message.reply(embed=embed, mention_author=False)


def setup(bot: commands.Bot):
    bot.add_cog(Quran(bot))
