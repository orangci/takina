from ..libs.oclib import *
import nextcord
from nextcord.ext import commands
import nextcord
from nextcord import Interaction, SlashOption
from __main__ import EMBED_COLOR


class CharacterSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_character(self, character_name: str):
        url1 = f"https://api.jikan.moe/v4/characters?q={character_name}&limit=1"
        url2 = f"https://api.jikan.moe/v4/characters/{character_name}"

        try:
            data = await request(url2)
            if data and data.get("data"):
                return data["data"]

            data = await request(url1)
            if data and data.get("data"):
                return data["data"][0]

        except Exception as e:
            raise e

    @commands.command(
        aliases=["waifu", "chr"],
        description="Fetch character information from MyAnimeList.",
        help="Usage: `chr Takina Inoue` or `chr 204620`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def character(self, ctx: commands.Context, *, character_name: str):
        try:
            character = await self.fetch_character(character_name)

            if character:
                name = character.get("name")
                cover_image = (
                    character.get("images", {}).get("jpg", {}).get("image_url")
                )
                mal_id = character.get("mal_id")
                url = character.get("url")
                nicknames = ", ".join(character.get("nicknames", []))
                about = character.get("about")[:400] + "..."
                name_kanji = character.get("name_kanji")

                embed = nextcord.Embed(
                    title=name,
                    url=url,
                    description=nicknames or name_kanji,
                    color=EMBED_COLOR,
                )
                embed.add_field(name="About", value=about, inline=False)
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    description="Character not found.",
                    color=0xFF0037,
                )

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=0xFF0037)

        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(
        name="character", description="Fetch character information from MyAnimeList."
    )
    async def slash_character(
        self,
        interaction: Interaction,
        character_name: str = SlashOption(
            description="Name or MAL ID of the character"
        ),
    ):
        """Slash command for searching characters on MyAnimeList."""
        try:
            character = await self.fetch_character(character_name)

            if character:
                name = character.get("name")
                cover_image = (
                    character.get("images", {}).get("jpg", {}).get("image_url")
                )
                mal_id = character.get("mal_id")
                url = character.get("url")
                nicknames = ", ".join(character.get("nicknames", []))
                about = character.get("about")[:400] + "..."
                name_kanji = character.get("name_kanji")

                embed = nextcord.Embed(
                    title=name,
                    url=url,
                    description=nicknames or name_kanji,
                    color=EMBED_COLOR,
                )
                embed.add_field(name="About", value=about, inline=False)
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    description="Character not found.",
                    color=0xFF0037,
                )

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=0xFF0037)

        await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(CharacterSearch(bot))
