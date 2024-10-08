from ..libs.oclib import *
import nextcord
from nextcord.ext import commands
from nextcord import ButtonStyle, Interaction, SlashOption
from nextcord.ui import Button, View
from __main__ import EMBED_COLOR


class PaginatedView(View):
    def __init__(self, pages, author_id=None):
        super().__init__(timeout=300)
        self.pages = pages
        self.current_page = 0
        self.author_id = author_id

    async def update_embed(self, interaction: Interaction):
        embed = self.pages[self.current_page]
        await interaction.response.edit_message(embed=embed, view=self)

    @nextcord.ui.button(label="Previous", style=ButtonStyle.primary)
    async def previous_page(self, button: Button, interaction: Interaction):
        if interaction.user.id != self.author_id:
            return
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_embed(interaction)

    @nextcord.ui.button(label="Next", style=ButtonStyle.primary)
    async def next_page(self, button: Button, interaction: Interaction):
        if interaction.user.id != self.author_id:
            return
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.update_embed(interaction)


class AnimeSeasonals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["season"])
    async def seasonals(
        self, ctx: commands.Context, season: str = None, year: int = None
    ):
        """Command for displaying seasonal anime from MyAnimeList. Usage: `season Fall 2024`, or `season` to fetch the current season."""
        emoji = await fetch_random_emoji()
        if season == None or year == None or season and year == None:
            url = "https://api.jikan.moe/v4/seasons/now"
            embed_title = f" {emoji} Current Season's Anime"
        else:
            url = f"https://api.jikan.moe/v4/seasons/{year}/{season}"
            embed_title = f"{emoji} {season} {year} Anime"

        def trim_rating(rating):
            ratings_map = {
                "G - All Ages": "G",
                "PG - Children": "PG",
                "PG-13 - Teens 13 or older": "PG-13",
                "R - 17+ (violence & profanity)": "R",
                "R+ - Mild Nudity": "R+",
                "Rx - Hentai": "Rx",
            }

            return ratings_map.get(rating, rating)

        try:
            data = await request(url)
            seasonals = data.get("data", [])

            if not seasonals:
                embed = nextcord.Embed(
                    title="No Seasonals Found",
                    description="No seasonal anime available.",
                    color=nextcord.Color.red(),
                )
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Create paginated embeds (5 seasonals per page)
            pages = []
            for i in range(0, len(seasonals), 5):
                embed = nextcord.Embed(title=embed_title, color=EMBED_COLOR)
                for anime in seasonals[i : i + 5]:
                    title = anime["title"]
                    url = anime["url"]
                    episodes = anime.get("episodes")
                    source = anime.get("source")
                    anime_type = anime.get("type")
                    rating = anime.get("rating")
                    score = anime.get("score")
                    rank = anime.get("rank")
                    members = anime.get("members")
                    trimmed_rating = trim_rating(rating)
                    embed.add_field(
                        name="\u200b",
                        value=f"[{title}]({url})\n {episodes} episodes, rated {trimmed_rating}, ranked {rank} with {members} members and a score of {score}.",
                        inline=False,
                    )

                pages.append(embed)

            # Send first page with buttons for navigation
            view = PaginatedView(pages, ctx.author.id)
            await ctx.reply(embed=pages[0], view=view, mention_author=False)

        except Exception as e:
            embed = nextcord.Embed(
                title="Error", description=str(e), color=nextcord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="seasonals", description="Display seasonal anime.")
    async def seasonals_slash(
        self,
        interaction: Interaction,
        season: str = SlashOption(
            name="season",
            description="The anime season (winter, spring, summer, fall)",
            required=False,
        ),
        year: int = SlashOption(
            name="year", description="The anime year", required=False
        ),
    ):
        """Slash command for displaying seasonal anime from MyAnimeList."""

        if season is None or year is None:
            url = "https://api.jikan.moe/v4/seasons/now"
            embed_title = "Current Season's Anime"
        else:
            url = f"https://api.jikan.moe/v4/seasons/{year}/{season}"
            embed_title = f"{season} {year} Anime"

        def trim_rating(rating):
            ratings_map = {
                "G - All Ages": "G",
                "PG - Children": "PG",
                "PG-13 - Teens 13 or older": "PG-13",
                "R - 17+ (violence & profanity)": "R",
                "R+ - Mild Nudity": "R+",
                "Rx - Hentai": "Rx",
            }
            return ratings_map.get(rating, rating)

        try:
            data = await request(url)
            seasonals = data.get("data", [])

            if not seasonals:
                embed = nextcord.Embed(
                    title="No Seasonals Found",
                    description="No seasonal anime available.",
                    color=nextcord.Color.red(),
                )
                await interaction.response.send_message(embed=embed)
                return

            # Create paginated embeds (5 seasonals per page)
            pages = []
            for i in range(0, len(seasonals), 5):
                embed = nextcord.Embed(title=embed_title, color=EMBED_COLOR)
                for anime in seasonals[i : i + 5]:
                    title = anime["title"]
                    url = anime["url"]
                    episodes = anime.get("episodes")
                    source = anime.get("source")
                    anime_type = anime.get("type")
                    rating = anime.get("rating")
                    score = anime.get("score")
                    rank = anime.get("rank")
                    members = anime.get("members")
                    trimmed_rating = trim_rating(rating)
                    embed.add_field(
                        name="\u200b",
                        value=f"[{title}]({url})\n {episodes} episodes, rated {trimmed_rating}, ranked {rank} with {members} members and a score of {score}.",
                        inline=False,
                    )

                pages.append(embed)

            # Send first page with buttons for navigation
            view = PaginatedView(pages)
            await interaction.response.send_message(embed=pages[0], view=view)

        except Exception as e:
            embed = nextcord.Embed(
                title="Error", description=str(e), color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(AnimeSeasonals(bot))
