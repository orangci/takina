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


def format_date(date_str):
    dt = datetime.fromisoformat(date_str)
    return dt.strftime("%B %d, %Y")


def format_date_long(date_str):
    dt = datetime.fromisoformat(date_str)
    return dt.strftime("%b %d, %Y at %I:%M %p")


class MAL_Anime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def anime(self, ctx: commands.Context, *, anime_name: str):
        """Command for searching anime on MyAnimeList. Usage example: `a?anime Lycoris Recoil"""
        url = f"https://api.jikan.moe/v4/anime?q={anime_name}&limit=1?sfw"
        try:
            data = await request(url)
            if data and data.get("data"):
                anime = data["data"][0]
                title = anime.get("title")
                episodes = anime.get("episodes")
                # score = anime.get("score")
                # synopsis = anime.get("synopsis")
                # if len(synopsis) > 200:
                #     synopsis = synopsis[:700] + '...'
                source = anime.get("source")
                aired = anime.get("aired", {}).get("string")
                type = anime.get("type")
                rating = anime.get("rating")
                cover_image = anime["images"]["jpg"]["image_url"]
                url = anime.get("url")
                mal_id = anime.get("mal_id")
                genres = ", ".join([genre["name"] for genre in anime.get("genres", [])])
                studios = ", ".join(
                    [studio["name"] for studio in anime.get("studios", [])]
                )

                embed = nextcord.Embed(title=title, url=url, color=0x2E51A2)
                embed.add_field(name="Type", value=type, inline=True)
                embed.add_field(name="Episodes", value=episodes, inline=True)
                # embed.add_field(name="Score", value=score, inline=True)
                embed.add_field(name="Source", value=source, inline=True)
                embed.add_field(name="Aired", value=aired, inline=True)
                embed.add_field(name="Genres", value=genres, inline=True)
                embed.add_field(name="Studios", value=studios, inline=True)
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    title="Anime not found or is NSFW; only SFW results are returned.",
                    color=0x2E51A2,
                )

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=0x2E51A2)
        await ctx.send(embed=embed)

    @nextcord.slash_command(name="anime", description="Get information about an anime")
    async def slash_anime(
        self,
        interaction: Interaction,
        anime_name: str = SlashOption(description="Name of the anime"),
    ):
        """Slash command for searching anime on MyAnimeList. Usage example: `/anime anime_name:Lycoris Recoil"""
        url = f"https://api.jikan.moe/v4/anime?q={anime_name}&limit=1??sfw"
        try:
            data = await request(url)
            if data and data.get("data"):
                anime = data["data"][0]
                title = anime.get("title")
                episodes = anime.get("episodes")
                # score = anime.get("score")
                # synopsis = anime.get("synopsis")
                # if len(synopsis) > 200:
                #     synopsis = synopsis[:500] + '...'
                source = anime.get("source")
                aired = anime.get("aired", {}).get("string")
                type = anime.get("type")
                rating = anime.get("rating")
                cover_image = anime["images"]["jpg"]["image_url"]
                url = anime.get("url")
                mal_id = anime.get("mal_id")
                genres = ", ".join([genre["name"] for genre in anime.get("genres", [])])
                studios = ", ".join(
                    [studio["name"] for studio in anime.get("studios", [])]
                )

                embed = nextcord.Embed(title=title, url=url, color=0x2E51A2)
                embed.add_field(name="Type", value=type, inline=True)
                embed.add_field(name="Episodes", value=episodes, inline=True)
                # embed.add_field(name="Score", value=score, inline=True)
                embed.add_field(name="Source", value=source, inline=True)
                embed.add_field(name="Aired", value=aired, inline=True)
                embed.add_field(name="Genres", value=genres, inline=True)
                embed.add_field(name="Studios", value=studios, inline=True)
                embed.set_thumbnail(url=cover_image)
                embed.set_footer(text=str(mal_id))

            else:
                embed = nextcord.Embed(
                    title="Anime not found or is NSFW; only SFW results are returned.",
                    color=0x2E51A2,
                )

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=0x2E51A2)
        await interaction.response.send_message(embed=embed)


class MAL_Manga(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def manga(self, ctx: commands.Context, *, manga_name: str):
        """Command for searching manga on MyAnimeList. Usage example: `a?manga Shikanoko Nokonoko Koshitantan"""
        url = f"https://api.jikan.moe/v4/manga?q={manga_name}&limit=1?sfw"
        try:
            data = await request(url)
            if data and data.get("data"):
                manga = data["data"][0]
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
                    title="Manga not found or is NSFW; only SFW results are returned.",
                    color=0x2E51A2,
                )

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=0x2E51A2)
        await ctx.send(embed=embed)

    @nextcord.slash_command(name="manga", description="Get information about a manga")
    async def slash_manga(
        self,
        interaction: Interaction,
        manga_name: str = SlashOption(description="Name of the manga"),
    ):
        """Slash command for searching manga on MyAnimeList. Usage example: `/manga manga_name:Shikanoko Nokonoko Koshitantan"""
        url = f"https://api.jikan.moe/v4/manga?q={manga_name}&limit=1?sfw"
        try:
            data = await request(url)
            if data and data.get("data"):
                manga = data["data"][0]
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
                    title="Manga not found or is NSFW; only SFW results are returned.",
                    color=0x2E51A2,
                )

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=0x2E51A2)
        await interaction.response.send_message(embed=embed)


class MAL_Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mal(self, ctx: commands.Context, *, username: str):
        try:
            profile_url = f"https://api.jikan.moe/v4/users/{username}"
            profile_data = await request(profile_url)

            if not profile_data or not profile_data.get("data"):
                embed = nextcord.Embed(title="User not found.", color=0x2E51A2)
                await ctx.send(embed=embed)
                return

            user = profile_data["data"]
            profile_url = user.get("url")
            profile_pic = user.get("images", {}).get("jpg", {}).get("image_url", "")
            gender = user.get("gender") or "Not Specified"
            last_online = format_date_long(user.get("last_online"))
            joined = format_date(user.get("joined"))
            location = user.get("location") or "Not Specified"
            birthday = user.get("birthday") or "Not Specified"
            mal_id = user.get("mal_id")
            anime_list_url = f"https://myanimelist.net/animelist/{username}"
            manga_list_url = f"https://myanimelist.net/mangalist/{username}"

            stats_url = f"https://api.jikan.moe/v4/users/{username}/statistics"
            stats_data = await request(stats_url)

            anime_mean = (
                stats_data.get("data", {}).get("anime", {}).get("mean_score")
            )
            manga_mean = (
                stats_data.get("data", {}).get("manga", {}).get("mean_score")
            )

            embed = nextcord.Embed(
                title=f"{username}'s Profile",
                url=profile_url,
                description=f"[Anime List]({anime_list_url}) • [Manga List]({manga_list_url})",
                color=0x2E51A2,
            )

            if gender == "Not Specified":
                gender_field_name = ":question: Gender"
            elif gender == "Male":
                gender_field_name = ":male_sign: Gender"
            elif gender == "Female":
                gender_field_name = ":female_sign: Gender"
            elif gender == "Non-Binary":
                gender_field_name = ":left_right_arrow: Gender"
            else:
                gender_field_name = "Gender"

            embed.add_field(name=gender_field_name, value=gender, inline=True)
            embed.add_field(name=":clock1: Last Online", value=last_online, inline=True)
            embed.add_field(name=":hourglass: Joined", value=joined, inline=True)
            embed.add_field(name=":map: Location", value=location, inline=True)
            embed.add_field(name=":tv: Anime", value=str(anime_mean), inline=True)
            embed.add_field(name=":book: Manga", value=str(manga_mean), inline=True)
            embed.set_footer(text=str(mal_id))

            if profile_pic:
                embed.set_thumbnail(url=profile_pic)

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=nextcord.Color.red())

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(MAL_Anime(bot))
    bot.add_cog(MAL_Manga(bot))
    bot.add_cog(MAL_Profile(bot))
