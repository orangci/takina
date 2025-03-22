import nextcord
from nextcord.ext import commands
from config import *
from ..libs.oclib import *


class Dictionary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help="Query the dictionary for a definition. \nUsage: `define grass`.",
        aliases=["dict"],
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def define(self, ctx: commands.Context, *, word: str):
        api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = await request(api_url)

        if (
            not response
            or isinstance(response, dict)
            and response.get("title") == "No Definitions Found"
        ):
            error_embed = nextcord.Embed(color=ERROR_COLOR)
            error_embed.description = ":x: No definition found."
            await ctx.reply(embed=error_embed, mention_author=False)
            return

        data = response[0]
        word = data.get("word", "N/A")
        phonetic = data.get("phonetic", "")
        meanings = data.get("meanings", [])

        if not meanings:
            error_embed = nextcord.Embed(color=ERROR_COLOR)
            error_embed.description = ":x: No definition found."
            await ctx.reply(embed=error_embed, mention_author=False)
            return

        embed = nextcord.Embed(title=word, color=EMBED_COLOR)
        description = f"*{phonetic}*\n\n" if phonetic else ""

        for meaning in meanings:
            part_of_speech = meaning.get("partOfSpeech", "N/A").capitalize()
            definitions = meaning.get("definitions", [])
            if definitions:
                description += f"**{part_of_speech}**\n"
                for idx, definition in enumerate(definitions, start=1):
                    def_text = definition.get("definition", "N/A")
                    example = definition.get("example")
                    description += f"{idx}. {def_text}\n"
                    if example:
                        description += f'"*{example}*"\n'
                    if idx >= 3:
                        break
                description += "\n"

        embed.description = description.strip()
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(
        name="define", description="Fetch a dictionary definition for a word."
    )
    async def slash_define(self, interaction: nextcord.Interaction, *, word: str):
        await interaction.response.defer()
        api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = await request(api_url)

        if (
            not response
            or isinstance(response, dict)
            and response.get("title") == "No Definitions Found"
        ):
            error_embed = nextcord.Embed(color=ERROR_COLOR)
            error_embed.description = ":x: No definition found."
            await interaction.send(embed=error_embed, ephemeral=True)
            return

        data = response[0]
        word = data.get("word", "N/A")
        phonetic = data.get("phonetic", "")
        meanings = data.get("meanings", [])

        if not meanings:
            error_embed = nextcord.Embed(color=ERROR_COLOR)
            error_embed.description = ":x: No definition found."
            await interaction.send(embed=error_embed, ephemeral=True)
            return

        embed = nextcord.Embed(title=word, color=EMBED_COLOR)
        description = f"*{phonetic}*\n\n" if phonetic else ""

        for meaning in meanings:
            part_of_speech = meaning.get("partOfSpeech", "N/A").capitalize()
            definitions = meaning.get("definitions", [])
            if definitions:
                description += f"**{part_of_speech}**\n"
                for idx, definition in enumerate(definitions, start=1):
                    def_text = definition.get("definition", "N/A")
                    example = definition.get("example")
                    description += f"{idx}. {def_text}\n"
                    if example:
                        description += f'"*{example}*"\n'
                description += "\n"

        embed.description = description.strip()
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Dictionary(bot))
