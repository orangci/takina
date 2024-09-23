import aiohttp
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Helper function for API requests
async def request(url, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request("GET", url, *args, **kwargs) as response:
            if response.status != 200:
                logging.error(f"Request to {url} failed with status: {response.status}")
            return await response.json()

class CharacterSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_character(self, character_name: str):
        url1 = f"https://api.jikan.moe/v4/characters?q={character_name}&limit=1"
        url2 = f"https://api.jikan.moe/v4/characters/{character_name}"

        try:
            data = await request(url1)
            if data and data.get("data"):
                return data["data"][0]

            data = await request(url2)
            if data and data.get("data"):
                return data["data"] 

        except Exception as e:
            logging.error(f"Error fetching character: {str(e)}")
            raise e

    @commands.command(aliases=["waifu", "chr"])
    async def character(self, ctx: commands.Context, *, character_name: str):
        """Command for searching character on MyAnimeList."""
        try:
            character = await self.fetch_character(character_name)

            if character:
                name = character.get("name")
                cover_image = character.get("images", {}).get("jpg", {}).get("image_url")
                mal_id = character.get("mal_id")
                url = character.get("url")
                nicknames = ", ".join(character.get("nicknames", []))
                about = character.get("about")[:400] + "..."
                name_kanji = character.get("name_kanji")

                embed = nextcord.Embed(title=name, url=url, description=nicknames or name_kanji, color=0x2E51A2)
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
        
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="character", description="Get information about a character")
    async def slash_character(
        self,
        interaction: Interaction,
        character_name: str = SlashOption(description="Name of the character"),
    ):
        """Slash command for searching characters on MyAnimeList."""
        try:
            character = await self.fetch_character(character_name)

            if character:
                name = character.get("name")
                cover_image = character.get("images", {}).get("jpg", {}).get("image_url")
                mal_id = character.get("mal_id")
                url = character.get("url")
                nicknames = ", ".join(character.get("nicknames", []))
                about = character.get("about")[:400] + "..."
                name_kanji = character.get("name_kanji")

                embed = nextcord.Embed(title=name, url=url, description=nicknames or name_kanji, color=0x2E51A2)
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
