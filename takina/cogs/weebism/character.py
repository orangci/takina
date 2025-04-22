# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from ..libs.oclib import *
import nextcord
from nextcord.ext import commands
import nextcord
from nextcord import Interaction, SlashOption
from config import *


class CharacterSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_character(
        self, character: str, embed: nextcord.Embed
    ) -> nextcord.Embed:
        url1 = f"https://api.jikan.moe/v4/characters?q={character}&limit=1"
        url2 = f"https://api.jikan.moe/v4/characters/{character}"
        character_data = None
        is_error_embed = False

        try:
            data = await request(url2)
            if data and data.get("data"):
                character_data = data["data"]
            else:
                data = await request(url1)
                if data and data.get("data"):
                    character_data = data["data"][0]

        except Exception as e:
            embed.description = f":x: {e}"
            embed.color = ERROR_COLOR
            is_error_embed = True
            return embed, is_error_embed

        if not character_data:
            embed.description = ":x: Character not found."
            embed.color = ERROR_COLOR
            is_error_embed = True
            return embed, is_error_embed

        name = character_data.get("name", "Unknown")
        cover_image = (
            character_data.get("images", {}).get("jpg", {}).get("image_url", "")
        )
        mal_id = character_data.get("mal_id", "N/A")
        url = character_data.get("url", "")
        nicknames = (
            ", ".join(character_data.get("nicknames", [])) or "No nicknames available"
        )
        about = (
            (character_data.get("about")[:400] + "...")
            if character_data.get("about")
            else "No information available."
        )
        name_kanji = character_data.get("name_kanji", "")

        embed.title = name
        embed.url = url
        embed.description = nicknames or name_kanji if name_kanji else ""
        if about:
            embed.add_field(name="About", value=about, inline=False)
        if cover_image:
            embed.set_thumbnail(url=cover_image)
        embed.set_footer(text=str(mal_id))

        return embed, is_error_embed

    @commands.command(
        aliases=["waifu", "chr"],
        help="Fetch character information from MyAnimeList. \nUsage: `chr Takina Inoue` or `chr 204620`.",
    )
    async def character(self, ctx: commands.Context, *, character: str):
        embed = nextcord.Embed(color=EMBED_COLOR)
        embed, is_error_embed = await self.fetch_character(character, embed)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(
        name="character", description="Fetch character information from MyAnimeList."
    )
    async def slash_character(
        self,
        interaction: Interaction,
        character: str = SlashOption(description="Name or MAL ID of the character"),
    ):
        await interaction.response.defer()
        embed = nextcord.Embed(color=EMBED_COLOR)
        embed, is_error_embed = await self.fetch_character(character, embed)
        if is_error_embed:
            await interaction.send(embed=embed, ephemeral=True)
        else:
            await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(CharacterSearch(bot))
