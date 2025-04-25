# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from datetime import datetime

import nextcord
import config
from google_books_api_wrapper.api import GoogleBooksAPI
from nextcord.ext import commands


class Books(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help="Fetch information on a book title or ISBN. \nUsage: `book Yumi and the Nightmare Painter`.",
        aliases=["books"],
    )
    async def book(self, ctx: commands.Context, *, book: str):
        api = GoogleBooksAPI()
        book_data = api.get_book_by_title(book)
        book_data = api.get_book_by_isbn13(book) if not book_data else book_data
        if not book_data:
            embed = nextcord.Embed(color=config.ERROR_COLOR)
            embed.description = ":x: The book specified does not exist in the database. Please check you have entered a valid book title or ISBN."
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = nextcord.Embed(
            title=book_data.title, color=config.EMBED_COLOR, description=""
        )

        embed.description += f"-# {book_data.subtitle}\n" if book_data.subtitle else ""
        embed.description += (
            f"\n> **Authors**: {', '.join(author for author in book_data.authors)}"
            if book_data.authors
            else ""
        )
        embed.description += (
            f"\n> **Subjects**: {', '.join(subject for subject in book_data.subjects)}"
            if book_data.subjects
            else ""
        )
        embed.description += (
            f"\n> **Pagecount**: {book_data.page_count}" if book_data.page_count else ""
        )
        try:
            embed.description += f"\n> **Published**: <t:{int(datetime.strptime(book_data.published_date, '%Y-%m-%d').timestamp())}:D>"
        except Exception:
            embed.description += (
                f"\n> **Published**: {book_data.published_date}"
                if book_data.published_date
                else ""
            )
        embed.description += (
            f"\n> **Publisher**: {book_data.publisher}" if book_data.publisher else ""
        )
        embed.description += (
            f"\n\n{book_data.description[:300] + '...' if len(book_data.description) > 300 else book_data.description}"
            if book_data.description
            else ""
        )

        embed.set_thumbnail(book_data.small_thumbnail)
        if book_data.ISBN_10 or book_data.ISBN_13:
            embed.set_footer(text=f"ISBN: {book_data.ISBN_13 or book_data.ISBN_10}")
        await ctx.reply(embed=embed, mention_author=False)


class SlashBooks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="book", description="Fetch information on a book title or ISBN."
    )
    async def slash_book(
        self,
        interaction: nextcord.Interaction,
        *,
        book: str = nextcord.SlashOption(
            description="The book title or ISBN to display information on",
            required=True,
        ),
    ):
        await interaction.response.defer()
        api = GoogleBooksAPI()
        book_data = api.get_book_by_title(book)
        book_data = api.get_book_by_isbn13(book) if not book_data else book_data
        if not book_data:
            embed = nextcord.Embed(color=config.ERROR_COLOR)
            embed.description = ":x: The book specified does not exist in the database. Please check you have entered a valid book title or ISBN."
            await interaction.send(embed=embed, ephemeral=True)
            return

        embed = nextcord.Embed(
            title=book_data.title, color=config.EMBED_COLOR, description=""
        )

        embed.description += f"-# {book_data.subtitle}\n" if book_data.subtitle else ""
        embed.description += (
            f"\n> **Authors**: {', '.join(author for author in book_data.authors)}"
            if book_data.authors
            else ""
        )
        embed.description += (
            f"\n> **Subjects**: {', '.join(subject for subject in book_data.subjects)}"
            if book_data.subjects
            else ""
        )
        embed.description += (
            f"\n> **Pagecount**: {book_data.page_count}" if book_data.page_count else ""
        )
        try:
            embed.description += f"\n> **Published**: <t:{int(datetime.strptime(book_data.published_date, '%Y-%m-%d').timestamp())}:D>"
        except Exception:
            embed.description += (
                f"\n> **Published**: {book_data.published_date}"
                if book_data.published_date
                else ""
            )
        embed.description += (
            f"\n> **Publisher**: {book_data.publisher}" if book_data.publisher else ""
        )
        embed.description += (
            f"\n\n{book_data.description[:300] + '...' if len(book_data.description) > 300 else book_data.description}"
            if book_data.description
            else ""
        )

        embed.set_thumbnail(book_data.small_thumbnail)
        if book_data.ISBN_10 or book_data.ISBN_13:
            embed.set_footer(text=f"ISBN: {book_data.ISBN_13 or book_data.ISBN_10}")
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Books(bot))
    bot.add_cog(SlashBooks(bot))
