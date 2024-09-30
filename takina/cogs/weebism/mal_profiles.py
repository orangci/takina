from ..libs.oclib import *
import nextcord
from nextcord.ext import commands
from datetime import datetime
import nextcord

def format_date(date_str):
    dt = datetime.fromisoformat(date_str)
    return dt.strftime("%B %d, %Y")


def format_date_long(date_str):
    dt = datetime.fromisoformat(date_str)
    return dt.strftime("%b %d, %Y at %I:%M %p")

class MAL_Profiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mal(self, ctx: commands.Context, *, username: str):
        try:
            profile_url = f"https://api.jikan.moe/v4/users/{username}"
            profile_data = await request(profile_url)

            if not profile_data or not profile_data.get("data"):
                embed = nextcord.Embed(title="User not found.", color=nextcord.Color.red())
                await ctx.reply(embed=embed, mention_author=False)
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

        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command()
    async def mal_slash(self, ctx: nextcord.Interaction, *, username: str = nextcord.SlashOption(description="Username of the user to fetch")):
        try:
            profile_url = f"https://api.jikan.moe/v4/users/{username}"
            profile_data = await request(profile_url)

            if not profile_data or not profile_data.get("data"):
                embed = nextcord.Embed(title="User not found.", color=0x2E51A2)
                await ctx.response.send_message(embed=embed, ephemeral=True)
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

        await ctx.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(MAL_Profiles(bot))
