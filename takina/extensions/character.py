import aiohttp
import nextcord
from nextcord.ext import commands
from datetime import datetime
from nextcord import Interaction, SlashOption


# Helper function for API requests
async def request(url, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request("GET", url, *args, **kwargs) as response:
            return await response.json()

class CharacterSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["waifu", "chr"])
    async def character(self, ctx: commands.Context, *, character_name: str):
        """Command for searching character on MyAnimeList. Usage example: `?character Takina Inoue"""
        url = f"https://api.jikan.moe/v4/characters?q={character_name}&limit=1"
        try:
            data = await request(url)
            if data and data.get("data"):
                character = data["data"][0]
                name = character.get("name")
                cover_image = character.get("images", {}).get("jpg", {}).get("image_url")
                mal_id = character.get("mal_id")
                url = character.get("url")
                about = character.get("about")[:400] + "..."
                name_kanji = character.get("name_kanji")

                embed = nextcord.Embed(title=name, url=url, description=name_kanji, color=0x2E51A2)
                embed.add_field(name="About", value=about[:500], inline=False)
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    description="Character not found.",
                    color=0x2E51A2,
                )

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=0x2E51A2)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="character", description="Get information about an character")
    async def slash_character(
        self,
        interaction: Interaction,
        character_name: str = SlashOption(description="Name of the character"),
    ):
        """Slash command for searching characters on MyAnimeList. Usage example: `/character character_name:Takina Inoue"""
        url = f"https://api.jikan.moe/v4/character?q={character_name}&limit=1"
        try:
            data = await request(url)
            if data and data.get("data"):
                character = data["data"][0]
                name = character.get("name")
                cover_image = character.get("images", {}).get("jpg", {}).get("image_url")
                mal_id = character.get("mal_id")
                url = character.get("url")
                about = character.get("about")[:400] + "..."
                name_kanji = character.get("name_kanji")

                embed = nextcord.Embed(title=name, url=url, description=name_kanji, color=0x2E51A2)
                embed.add_field(name="About", value=about, inline=False)
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    description="Character not found.",
                    color=0x2E51A2,
                )

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=0x2E51A2)
        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(CharacterSearch(bot))
