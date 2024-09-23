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

class MangaSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_manga(self, manga_name: str):
        url1 = f"https://api.jikan.moe/v4/manga?q={manga_name}&limit=1"
        url2 = f"https://api.jikan.moe/v4/manga/{manga_name}"

        try:
            data = await request(url2)
            if data and data.get("data"):
                return data["data"] 
            
            data = await request(url1)
            if data and data.get("data"):
                return data["data"][0]

        except Exception as e:
            raise e

    @commands.command()
    async def manga(self, ctx: commands.Context, *, manga_name: str):
        """Command for searching manga on MymangaList. Usage example: `?manga Shikanoko Nokonoko Koshitantan`."""
        url = f"https://api.jikan.moe/v4/manga?q={manga_name}&limit=1"
        try:
            manga = await self.fetch_manga(manga_name)
            if manga:
                title = manga.get("title")
                chapters = manga.get("chapters")
                score = manga.get("score")
                status = manga.get("status")
                cover_image = manga["images"]["jpg"]["image_url"]
                url = manga.get("url")
                mal_id = manga.get("mal_id")
                genres = ", ".join([genre["name"] for genre in manga.get("genres", [])])

                embed = nextcord.Embed(title=title, url=url, color=0x2E51A2)
                if not status == "Publishing":
                    embed.add_field(name="Chapters", value=chapters, inline=True)
                embed.add_field(name="Score", value=score, inline=True)
                embed.add_field(name="Status", value=status, inline=True)
                embed.add_field(name="Genres", value=genres, inline=True)
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    description="Manga not found.",
                    color=0x2E51A2,
                )

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=0x2E51A2)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="manga", description="Get information about a manga")
    async def slash_manga(
        self,
        interaction: Interaction,
        manga_name: str = SlashOption(description="Name of the manga"),
    ):
        """Slash command for searching manga on MymangaList. Usage example: `/manga manga_name:Shikanoko Nokonoko Koshitantan`."""
        url = f"https://api.jikan.moe/v4/manga?q={manga_name}&limit=1"
        try:
            manga = await self.fetch_manga(manga_name)
            if manga:
                title = manga.get("title")
                chapters = manga.get("chapters")
                score = manga.get("score")
                status = manga.get("status")
                cover_image = manga["images"]["jpg"]["image_url"]
                url = manga.get("url")
                mal_id = manga.get("mal_id")
                genres = ", ".join([genre["name"] for genre in manga.get("genres", [])])

                embed = nextcord.Embed(title=title, url=url, color=0x2E51A2)
                if not status == "Publishing":
                    embed.add_field(name="Chapters", value=chapters, inline=True)
                embed.add_field(name="Score", value=score, inline=True)
                embed.add_field(name="Status", value=status, inline=True)
                embed.add_field(name="Genres", value=genres, inline=True)
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    description="Manga not found.",
                    color=0x2E51A2,
                )

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=0x2E51A2)
        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(MangaSearch(bot))
