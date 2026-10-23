# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors, lyhelpers, lychecks
from discord.ext import commands
from takina import config
import urllib.parse
import discord
import re


class Dictionary(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(
        aliases=["def"], description="Query the dictionary for a definition.", usage="grass"
    )
    @lychecks.is_user_app()
    async def define(self, ctx: commands.Context, *, word: str) -> None:
        await ctx.defer()
        response = await lyhelpers.request(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word, safe='')}",
            not_found="No definition found.",
        )

        data = response[0]
        word = data.get("word", "N/A")
        phonetic = data.get("phonetic", "")
        meanings = data.get("meanings", [])

        if not meanings:
            raise lyerrors.TakinaError("No definition found.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = lyhelpers.truncate(word, 256)
        description = f"*{phonetic}*\n\n" if phonetic else ""

        for meaning in meanings:
            part_of_speech = meaning.get("partOfSpeech", "N/A").capitalize()
            definitions = meaning.get("definitions", [])
            if not definitions:
                continue

            description += f"**{part_of_speech}**\n"
            for index, definition in enumerate(definitions, start=1):
                definition_text = definition.get("definition", "N/A")
                example = definition.get("example")
                description += f"{index}. {definition_text}\n"

                if example:
                    description += f'"*{example}*"\n'

                if index >= 3:
                    break

            description += "\n"

        # a word with many senses easily outgrows an embed
        embed.description = lyhelpers.truncate(description.strip(), 4096)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        aliases=["ubdefine"], description="Query Urban Dictionary for a definition.", usage="anime"
    )
    @lychecks.is_user_app()
    async def ubdict(self, ctx: commands.Context, *, word: str) -> None:
        await ctx.defer()
        response = await lyhelpers.request(
            "https://api.urbandictionary.com/v0/define", params={"term": word}
        )

        if not response.get("list"):
            raise lyerrors.TakinaError("No results found.")

        data = response["list"][0]

        def format_text(text: str, limit: int) -> str:
            # cut before expanding [terms] into links, so a link is never cut in half
            text = lyhelpers.truncate(text, 300)
            linked = re.sub(
                r"\[(.*?)\]",
                lambda match: (
                    f"[{match.group(1)}](https://www.urbandictionary.com/define.php?term={urllib.parse.quote(match.group(1))})"
                ),
                text,
            )

            # many short terms can still outgrow the limit once linked
            return linked if len(linked) <= limit else text.replace("[", "").replace("]", "")

        definition = format_text(data["definition"], 4096)
        example = format_text(data["example"], 1024) if data["example"] else "No examples provided."

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = data["word"]
        embed.description = definition
        embed.url = data["permalink"]
        embed.add_field(name="Example", value=example, inline=False)
        embed.set_footer(
            text=f"👍 {data['thumbs_up']:,} | 👎 {data['thumbs_down']:,} | Powered by Urban Dictionary"
        )
        embed.set_thumbnail(url="https://www.urbandictionary.com/favicon-32x32.png")

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Dictionary(bot))
