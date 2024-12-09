from ..libs.oclib import *
import nextcord
from nextcord.ext import commands
from datetime import datetime
import nextcord
from __main__ import EMBED_COLOR


def format_date(date_str):
    dt = datetime.fromisoformat(date_str)
    return dt.strftime("%B %d, %Y")


def format_date_long(date_str):
    dt = datetime.fromisoformat(date_str)
    return dt.strftime("%b %d, %Y at %I:%M %p")


class MAL_Profiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help="Fetch information about a MyAnimeList user. \nUsage: `mal <username>`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def mal(self, ctx: commands.Context, *, username: str):
        try:
            profile_url = f"https://api.jikan.moe/v4/users/{username}"
            profile_data = await request(profile_url)

            if not profile_data or not profile_data.get("data"):
                embed = nextcord.Embed(title="User not found.", color=0xFF0037)
                await ctx.reply(embed=embed, mention_author=False)
                return

            user = profile_data["data"]
            profile_url = user.get("url")
            profile_pic = user.get("images", {}).get("jpg", {}).get("image_url", "")
            gender = user.get("gender") or "Not Specified"
            last_online = format_date_long(user.get("last_online"))
            joined = format_date(user.get("joined"))
            location = user.get("location") or "Not Specified"
            mal_id = user.get("mal_id")
            anime_list_url = f"https://myanimelist.net/animelist/{username}"
            manga_list_url = f"https://myanimelist.net/mangalist/{username}"

            stats_url = f"https://api.jikan.moe/v4/users/{username}/statistics"
            stats_data = await request(stats_url)

            anime_mean = stats_data.get("data", {}).get("anime", {}).get("mean_score")
            manga_mean = stats_data.get("data", {}).get("manga", {}).get("mean_score")

            embed = nextcord.Embed(
                title=f"{username}'s Profile",
                url=profile_url,
                color=EMBED_COLOR,
            )

            embed.description = (
                f"-# [Anime List]({anime_list_url}) • [Manga List]({manga_list_url})\n"
            )
            embed.description += f"\n> **Gender**: {gender}"
            embed.description += f"\n> **Last Online**: {last_online}"
            embed.description += f"\n> **Joined**: {joined}"
            embed.description += f"\n> **Location**: {location}"
            embed.description += f"\n> **Anime Mean**: {str(anime_mean)}"
            embed.description += f"\n> **Manga Mean**: {str(manga_mean)}"
            embed.set_footer(text=str(mal_id))

            if profile_pic:
                embed.set_thumbnail(url=profile_pic)

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=0xFF0037)

        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(
        name="mal", description="Fetch information about a MyAnimeList user."
    )
    async def mal_slash(
        self,
        ctx: nextcord.Interaction,
        *,
        username: str = nextcord.SlashOption(
            description="Username of the user to fetch"
        ),
    ):
        try:
            profile_url = f"https://api.jikan.moe/v4/users/{username}"
            profile_data = await request(profile_url)

            if not profile_data or not profile_data.get("data"):
                embed = nextcord.Embed(title="User not found.", color=EMBED_COLOR)
                await ctx.response.send_message(embed=embed, ephemeral=True)
                return

            user = profile_data["data"]
            profile_url = user.get("url")
            profile_pic = user.get("images", {}).get("jpg", {}).get("image_url", "")
            gender = user.get("gender") or "Not Specified"
            last_online = format_date_long(user.get("last_online"))
            joined = format_date(user.get("joined"))
            location = user.get("location") or "Not Specified"
            mal_id = user.get("mal_id")
            anime_list_url = f"https://myanimelist.net/animelist/{username}"
            manga_list_url = f"https://myanimelist.net/mangalist/{username}"

            stats_url = f"https://api.jikan.moe/v4/users/{username}/statistics"
            stats_data = await request(stats_url)

            anime_mean = stats_data.get("data", {}).get("anime", {}).get("mean_score")
            manga_mean = stats_data.get("data", {}).get("manga", {}).get("mean_score")

            embed = nextcord.Embed(
                title=f"{username}'s Profile",
                url=profile_url,
                color=EMBED_COLOR,
            )

            embed.description = (
                f"-# [Anime List]({anime_list_url}) • [Manga List]({manga_list_url})\n"
            )
            embed.description += f"\n> **Gender**: {gender}"
            embed.description += f"\n> **Last Online**: {last_online}"
            embed.description += f"\n> **Joined**: {joined}"
            embed.description += f"\n> **Location**: {location}"
            embed.description += f"\n> **Anime Mean**: {str(anime_mean)}"
            embed.description += f"\n> **Manga Mean**: {str(manga_mean)}"
            embed.set_footer(text=str(mal_id))

            if profile_pic:
                embed.set_thumbnail(url=profile_pic)

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=0xFF0037)

        await ctx.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(MAL_Profiles(bot))
