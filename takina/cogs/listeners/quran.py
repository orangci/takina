from takina.libs import lyhelpers, lyerrors
from discord.ext import commands
from takina import config
import discord
import re


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

        if not (1 <= surah <= 114):
            return

        try:
            english_data = await lyhelpers.request(
                f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/en.hilali"
            )
        except lyerrors.TakinaError:
            return

        if not english_data:
            return

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = f"The Holy Qu'rān, Āyah {ayah} of Surah {english_data['data']['surah']['englishName']} ({english_data['data']['surah']['englishNameTranslation']})"
        embed.description = english_data["data"]["text"]
        embed.set_footer(text="English translation by Hilali & Khan")
        await message.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Quran(bot))
