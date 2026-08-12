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
        response = await lyhelpers.request(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        )

        if not response or (
            isinstance(response, dict) and response.get("title") == "No Definitions Found"
        ):
            raise lyerrors.TakinaError("No definition found.")

        data = response[0]
        word = data.get("word", "N/A")
        phonetic = data.get("phonetic", "")
        meanings = data.get("meanings", [])

        if not meanings:
            raise lyerrors.TakinaError("No definition found.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = word
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

        embed.description = description.strip()
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        aliases=["ubdefine"], description="Query Urban Dictionary for a definition.", usage="anime"
    )
    @lychecks.is_user_app()
    async def ubdict(self, ctx: commands.Context, *, word: str) -> None:
        response = await lyhelpers.request(
            "https://api.urbandictionary.com/v0/define", params={"term": word}
        )

        if not response or not response.get("list"):
            raise lyerrors.TakinaError("No results found.")

        data = response["list"][0]

        def format_text(text: str) -> str:
            text = re.sub(
                r"\[(.*?)\]",
                lambda match: (
                    f"[{match.group(1)}](https://www.urbandictionary.com/define.php?term={urllib.parse.quote(match.group(1))})"
                ),
                text,
            )

            if len(text) > 300:
                return f"{text[:300].strip()}..."

            return text

        definition = format_text(data["definition"])
        example = format_text(data["example"]) if data["example"] else "No examples provided."

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
