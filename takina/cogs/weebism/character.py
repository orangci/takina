# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import nextcord
import config
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from ..libs import oclib


class CharacterSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_character(self, character: str, embed: nextcord.Embed) -> nextcord.Embed:
        url1 = f"https://api.jikan.moe/v4/characters?q={character}&limit=1"
        url2 = f"https://api.jikan.moe/v4/characters/{character}"
        character_data = None

        try:
            data = await oclib.request(url2)
            if data and data.get("data"):
                character_data = data["data"]
            else:
                data = await oclib.request(url1)
                if data and data.get("data"):
                    character_data = data["data"][0]

        except Exception as e:
            embed.description = f":x: {e}"
            embed.color = config.ERROR_COLOR
            return embed

        if not character_data:
            embed.description = ":x: Character not found."
            embed.color = config.ERROR_COLOR
            return embed

        name = character_data.get("name", "Unknown")
        cover_image = character_data.get("images", {}).get("jpg", {}).get("image_url", "")
        mal_id = character_data.get("mal_id", "N/A")
        url = character_data.get("url", "")
        nicknames = ", ".join(character_data.get("nicknames", [])) or "No nicknames available"
        about = (character_data.get("about")[:400] + "...") if character_data.get("about") else "No information available."
        name_kanji = character_data.get("name_kanji", "")

        embed.title = name
        embed.url = url
        embed.description = nicknames or name_kanji if name_kanji else ""
        if about:
            embed.add_field(name="About", value=about, inline=False)
        if cover_image:
            embed.set_thumbnail(url=cover_image)
        embed.set_footer(text=str(mal_id))

        return embed

    @commands.command(aliases=["waifu", "chr"], help="Fetch character information from MyAnimeList. \nUsage: `chr Takina Inoue` or `chr 204620`.")
    async def character(self, ctx: commands.Context, *, character: str):
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed = await self.fetch_character(character, embed)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="character", description="Fetch character information from MyAnimeList.")
    async def slash_character(self, interaction: Interaction, character: str = SlashOption(description="Name or MAL ID of the character")):
        await interaction.response.defer()
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed = await self.fetch_character(character, embed)
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(CharacterSearch(bot))
