# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
from ..libs import oclib
import nextcord
import nltk
import re
import os

# download the nltk dictionary thing.. this is the data containing syllables and stuff
if not os.getenv("NIXOS_INSTANCE"):
    NLTK_DIR = os.path.join(os.getcwd(), ".nltk_data")
    os.makedirs(NLTK_DIR, exist_ok=True)
    nltk.data.path.append(NLTK_DIR)
    nltk.download("cmudict", download_dir=NLTK_DIR)


class Haikus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cmu = nltk.corpus.cmudict.dict()

    def syllables(self, word: str) -> int:
        word = word.lower()
        if word in self.cmu:
            return len([p for p in self.cmu[word][0] if p[-1].isdigit()])
        return 0

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return

        text = message.content.strip()
        if not text:
            return

        # stop the idiots from spamming the same character 17 times over
        # and just filter out short messages
        if len(text.strip(" ")) <= 33:
            return
        
        # sometimes, GIFs somehow have exactly 17 syllables...
        # so let's just block links from being recognised as haikus entirely
        if "://" in text:
            return

        words = re.findall(r"\b\w+\b", text)
        if not words:
            return
        
        # this is to stop people from spamming the same one syllable word 17 times over;
        # if more than half of the words are the same word
        # we skip! teehee
        for word in set(words):
            if words.count(word) > len(words) / 2:
                return

        syllable_counts = [self.syllables(w) for w in words]
        total = sum(syllable_counts)

        if total != 17:
            return

        target = [5, 7, 5]
        lines = []
        current_line = []
        current_syllables = 0
        target_index = 0

        for word, syl in zip(words, syllable_counts):
            current_line.append(word)
            current_syllables += syl

            if current_syllables == target[target_index]:
                lines.append(" ".join(current_line))
                current_line = []
                current_syllables = 0
                target_index += 1
                if target_index == 3:
                    break

            elif current_syllables > target[target_index]:
                # invalid split, abort
                return

        if len(lines) == 3:
            await message.reply(
                f"\n{lines[0]}\n{lines[1]}\n{lines[2]}\n-# {await oclib.fetch_random_emoji()} I detect haikus. Yes, just like [u/haikusbot](<https://reddit.com/u/haikus.bot>)."
            )


def setup(bot: commands.Bot):
    bot.add_cog(Haikus(bot))
