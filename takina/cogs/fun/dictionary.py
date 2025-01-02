import nextcord
from nextcord.ext import commands
from config import *
from ..libs.oclib import *

class Dictionary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help="Query the dictionary for a definition. \nUsage: `define grass`.",
        aliases=["dict"]
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def define(self, ctx: commands.Context, *, word: str):
        api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = await request(api_url)
        if response[0]:
            data = response[0]
        else:
            error_embed = nextcord.Embed(color=ERROR_COLOR)
            error_embed.description = ":x: No definition found."
            return
        
        word = data.get("word", "N/A")
        phonetic = data.get("phonetic", "")
        meanings = data.get("meanings", [])
        
        embed = nextcord.Embed(title=word,color=EMBED_COLOR)
        embed.description = ""
        if phonetic:
            embed.description += f"-# {phonetic}"
        
        if meanings:
            for meaning in meanings:
                part_of_speech = meaning.get("partOfSpeech", "N/A")
                definitions = meaning.get("definitions", [])
                if definitions:
                    definition = definitions[0].get("definition", "N/A")
                    example = definitions[0].get("example")
                    
                    embed.description += f"\n\n**{part_of_speech.capitalize()}**: {definition}"
                    if example: embed.description += f"\n**Example**: {example}"
        else:
            error_embed = nextcord.Embed(color=ERROR_COLOR)
            error_embed.description = ":x: No definition found."
            return
        
        await ctx.reply(embed=embed, mention_author=False)
        

def setup(bot):
    bot.add_cog(Dictionary(bot))
