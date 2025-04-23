# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from ..libs.oclib import *
import nextcord
from nextcord.ext import commands
from nextcord import ButtonStyle, Interaction, SlashOption
from nextcord.ui import Button, View
from config import *


class PaginatedView(View):
    def __init__(self, pages, author_id=None):
        super().__init__(timeout=300)
        self.pages = pages
        self.current_page = 0
        self.author_id = author_id

        if len(pages) <= 1:
            self.previous_page.disabled = True
            self.next_page.disabled = True

    async def update_embed(self, interaction: Interaction):
        embed = self.pages[self.current_page]

        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == len(self.pages) - 1

        await interaction.response.edit_message(embed=embed, view=self)

    @nextcord.ui.button(label="Previous", style=ButtonStyle.primary, disabled=True)
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

    def trim_rating(self, rating):
        ratings_map = {
            "G - All Ages": "G",
            "PG - Children": "PG",
            "PG-13 - Teens 13 or older": "PG-13",
            "R - 17+ (violence & profanity)": "R",
            "R+ - Mild Nudity": "R+",
            "Rx - Hentai": "Rx",
        }
        return ratings_map.get(rating, rating)

    async def build_seasonal_response(self, season, year, emoji=""):
        if season is None or year is None:
            url = "https://api.jikan.moe/v4/seasons/now"
            title = f"{emoji} Current Season's Anime"
        else:
            url = f"https://api.jikan.moe/v4/seasons/{year}/{season}"
            title = f"{emoji} {season.lower().capitalize()} {year} Anime"

        try:
            data = await request(url)
            seasonals = data.get("data", [])

            if not seasonals:
                return None, nextcord.Embed(
                    description="No seasonal anime available.",
                    color=ERROR_COLOR,
                )

            pages = []
            for i in range(0, len(seasonals), 5):
                embed = nextcord.Embed(title=title, color=EMBED_COLOR)
                for anime in seasonals[i : i + 5]:
                    embed.add_field(
                        name="\u200b",
                        value=(
                            f"[{anime['title']}]({anime['url']})\n"
                            f"{anime.get('episodes')} episodes, rated {self.trim_rating(anime.get('rating'))}, "
                            f"ranked {anime.get('rank')} with {anime.get('members')} members and a score of {anime.get('score')}."
                        ),
                        inline=False,
                    )
                pages.append(embed)

            return pages, None

        except Exception as e:
            return None, nextcord.Embed(description=str(e), color=ERROR_COLOR)

    @commands.command(
        aliases=["season"],
        help="Fetch a season's airing anime.\nUsage: `season <season> <year>` or `season` to fetch the current season.",
    )
    async def seasonals(
        self, ctx: commands.Context, season: str = None, year: int = None
    ):
        emoji = await fetch_random_emoji()
        pages, error_embed = await self.build_seasonal_response(season, year, emoji)

        if error_embed:
            await ctx.reply(embed=error_embed, mention_author=False)
        else:
            view = PaginatedView(pages, ctx.author.id)
            await ctx.reply(embed=pages[0], view=view, mention_author=False)

    @nextcord.slash_command(
        name="seasonals",
        description="Fetch a season's airing anime.",
    )
    async def seasonals_slash(
        self,
        interaction: Interaction,
        season: str = SlashOption(
            name="season",
            description="The anime season (winter, spring, summer, fall)",
            required=False,
        ),
        year: int = SlashOption(
            name="year",
            description="The anime year",
            required=False,
        ),
    ):
        await interaction.response.defer()
        pages, error_embed = await self.build_seasonal_response(season, year)

        if error_embed:
            await interaction.send(embed=error_embed)
        else:
            view = PaginatedView(pages, interaction.user.id)
            await interaction.send(embed=pages[0], view=view)


def setup(bot):
    bot.add_cog(AnimeSeasonals(bot))
