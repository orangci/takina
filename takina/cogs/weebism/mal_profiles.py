# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from datetime import datetime

import nextcord
import config
from nextcord.ext import commands

from ..libs import oclib


def format_date(date_str):
    dt = datetime.fromisoformat(date_str)
    return f"<t:{int(dt.timestamp())}:D>"


def format_date_long(date_str):
    dt = datetime.fromisoformat(date_str)
    return f"<t:{int(dt.timestamp())}>"


class MAL_Profiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def build_embed(self, username):
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        try:
            profile_data = await oclib.request(f"https://api.jikan.moe/v4/users/{username}")

            if not profile_data or not profile_data.get("data"):
                embed.description = ":x: User not found."
                embed.color = config.ERROR_COLOR
                return embed

            user = profile_data["data"]

            mal_id = user.get("mal_id")
            profile_url = user.get("url")
            profile_pic = user.get("images", {}).get("jpg", {}).get("image_url", "")
            gender = user.get("gender") or "Not Specified"
            last_online = format_date_long(user.get("last_online"))
            joined = format_date(user.get("joined"))
            location = user.get("location") or "Not Specified"
            anime_list_url = f"https://myanimelist.net/animelist/{username}"
            manga_list_url = f"https://myanimelist.net/mangalist/{username}"

            # stats
            profile_stats = await oclib.request(f"https://api.jikan.moe/v4/users/{username}/statistics")

            anime_stats = profile_stats["data"].get("anime")
            days_watched = f"**{str(anime_stats.get('days_watched'))}**"
            anime_mean = f"**{str(anime_stats.get('mean_score'))}**"

            manga_stats = profile_stats["data"].get("manga")
            days_read = f"**{str(manga_stats.get('days_read'))}**"
            manga_mean = f"**{str(manga_stats.get('mean_score'))}**"

            embed = nextcord.Embed(title=f"{username}'s Profile", url=profile_url, color=config.EMBED_COLOR)

            embed.description = f"-# [Anime List]({anime_list_url}) • [Manga List]({manga_list_url})\n"
            embed.description += f"\n> **Gender**: {gender}"
            embed.description += f"\n> **Last Seen**: {last_online}"
            embed.description += f"\n> **Joined**: {joined}"
            embed.description += f"\n> **Location**: {location}"
            embed.description += f"\n> **Anime:** {days_watched} days watched with a mean score of {anime_mean}."
            embed.description += f"\n> **Manga:** {days_read} days read with a mean score of {manga_mean}."
            embed.set_footer(text=str(mal_id))

            if profile_pic:
                embed.set_thumbnail(url=profile_pic)
            return embed

        except Exception as e:
            embed.description = str(e)
            embed.color = config.ERROR_COLOR
            return embed

    @commands.command(help="Fetch information about a MyAnimeList user. \nUsage: `mal <username>`.")
    async def mal(self, ctx: commands.Context, *, username: str):
        embed = await self.build_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="mal", description="Fetch information about a MyAnimeList user.")
    async def mal_slash(
        self, interaction: nextcord.Interaction, *, username: str = nextcord.SlashOption(description="Username of the user to fetch")
    ):
        await interaction.response.defer()
        embed = await self.build_embed(username)
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(MAL_Profiles(bot))
