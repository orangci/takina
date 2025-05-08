# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import nextcord
import config
from nextcord.ext import commands
from ..libs import oclib


class MAL_Updates(commands.Cog):
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

            list_updates = await oclib.request(f"https://api.jikan.moe/v4/users/{username}/userupdates")

            if not list_updates or not list_updates.get("data"):
                embed.description = ":x: User not found."
                embed.color = config.ERROR_COLOR
                return embed

        except Exception as e:
            embed.description = str(e)
            embed.color = config.ERROR_COLOR
            return embed

        embed.title = f"{username}'s MyAnimeList Updates"
        user = profile_data["data"]
        updates = list_updates["data"]

        embed.url = user.get("url")

        embed.set_footer(text=f"For more information on this user, run the mal {username} command.")

        profile_pic = user.get("images", {}).get("jpg", {}).get("image_url", "")
        if profile_pic:
            embed.set_thumbnail(url=profile_pic)

        anime_updates = []
        manga_updates = []

        for anime in updates.get("anime", []):
            entry = anime.get("entry", {})
            title = entry.get("title", "Unknown Title")
            url = entry.get("url", "")
            progress = anime.get("episodes_seen", 0)
            total = anime.get("episodes_total", 0)
            status = anime.get("status", "unknown").lower()
            score = anime.get("score", 0)

            if progress is None:
                progress = 0
            if total is None:
                total = 0

            if total == 0:
                progress_text = f" at {progress}/?" if progress > 0 else ""
            else:
                progress_text = f" at {progress}/{total}"

            if status == "watching":
                line = f"Watching **[{title}]({url})**{progress_text}."
            elif status == "plan to watch":
                line = f"Planning to watch **[{title}]({url})**."
            elif status == "on-hold":
                line = f"Placed **[{title}]({url})** on hold{progress_text}."
            elif status == "dropped":
                line = f"Dropped **[{title}]({url})**{progress_text}."
            elif status == "completed":
                line = f"Completed **[{title}]({url})** with a rating of {score}/10."
            else:
                line = f"{status.capitalize()} **[{title}]({url})**{progress_text} with a score of {score}/10."

            anime_updates.append(line)

        for manga in updates.get("manga", []):
            entry = manga.get("entry", {})
            title = entry.get("title", "Unknown Title")
            url = entry.get("url", "")
            progress = manga.get("chapters_read", 0)
            total = manga.get("chapters_total", 0)
            status = manga.get("status", "unknown").lower()
            score = manga.get("score", 0)

            if progress is None:
                progress = 0
            if total is None:
                total = 0

            if total == 0:
                progress_text = f" at {progress}/?" if progress > 0 else ""
            else:
                progress_text = f" at {progress}/{total}"

            if status == "reading":
                line = f"Reading **[{title}]({url})**{progress_text}."
            elif status == "plan to read":
                line = f"Planning to read **[{title}]({url})**."
            elif status == "on-hold":
                line = f"Placed **[{title}]({url})** on hold{progress_text}."
            elif status == "dropped":
                line = f"Dropped **[{title}]({url})**{progress_text}."
            elif status == "completed":
                line = f"Completed **[{title}]({url})** with a rating of {score}/10."
            else:
                line = f"{status.capitalize()} **[{title}]({url})**{progress_text} with a score of {score}/10."

            manga_updates.append(line)

        embed.description = ""
        if anime_updates:
            embed.description += f"### Anime Updates\n{'\n'.join(anime_updates)}\n\n"

        if manga_updates:
            embed.description += f"### Manga Updates\n{'\n'.join(manga_updates)}"

        return embed

    @commands.command(help="Fetch a MyAnimeList user's latest list updates. \nUsage: `mal <username>`.")
    async def malupdates(self, ctx: commands.Context, *, username: str):
        embed = await self.build_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="mal_updates", description="Fetch a MyAnimeList user's latest list updates.")
    async def malupdates_slash(
        self, interaction: nextcord.Interaction, *, username: str = nextcord.SlashOption(description="Username of the user to fetch")
    ):
        await interaction.response.defer()
        embed = await self.build_embed(username)
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(MAL_Updates(bot))
