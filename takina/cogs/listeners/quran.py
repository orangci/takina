# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyhelpers, lyerrors
from discord.ext import commands
from takina import config
import logging
import discord
import aiohttp
import re

logger = logging.getLogger("takina.quran")


class Quran(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self.QURAN_REGEX = re.compile(
            r"\b(?:quran|qur'an|koran|coran)\s*\(?(\d{1,3}):(\d{1,3})\)?", re.IGNORECASE
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        match = self.QURAN_REGEX.search(message.content)
        if not match:
            return

        surah = int(match.group(1))
        ayah = int(match.group(2))

        # an ayah past the end of its surah is refused by the api, and skipped below
        if not (1 <= surah <= 114) or ayah < 1:
            return

        try:
            english_data = await lyhelpers.request(
                f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/en.hilali"
            )
            data = english_data["data"]
            surah_data = data["surah"]
            title = f"The Holy Qur'ān, Āyah {ayah} of Surah {surah_data['englishName']} ({surah_data['englishNameTranslation']})"
            text = data["text"]
        except (lyerrors.TakinaError, aiohttp.ClientError, TimeoutError) as error:
            logger.debug(f"quran lookup for {surah}:{ayah} failed: {error}")
            return
        except (KeyError, TypeError) as error:
            # the api changed shape under us
            logger.warning(f"unexpected quran api response for {surah}:{ayah}: {error!r}")
            return

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = title
        embed.description = text
        embed.set_footer(text="English translation by Hilali & Khan")
        await message.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Quran(bot))
