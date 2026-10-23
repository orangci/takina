# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from datetime import datetime, UTC
from discord.ext import commands
from takina import config
import discord


def format_published(published_date: str) -> str:
    # google gives 2008, 2008-05 or 2008-05-14, depending on what the publisher listed
    parts = published_date.split("-")
    try:
        if len(parts) == 1:
            return parts[0]

        if len(parts) == 2:
            return datetime(int(parts[0]), int(parts[1]), 1, tzinfo=UTC).strftime("%B %Y")

        published = datetime(int(parts[0]), int(parts[1]), int(parts[2]), tzinfo=UTC)
    except ValueError:
        return published_date

    return f"<t:{int(published.timestamp())}:D>"


class Books(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_command(
        description="Fetch information on a book title or ISBN.",
        usage="Yumi and the Nightmare Painter",
        aliases=["books"],
    )
    @lychecks.is_user_app()
    async def book(self, ctx: commands.Context, *, book: str):
        await ctx.defer()

        book_data = await self.search(f"intitle:{book}")
        if not book_data.get("items"):
            book_data = await self.search(f"isbn:{book}")

        if not book_data.get("items"):
            raise lyerrors.TakinaNotFoundError(
                "The book specified does not exist in the database. Please ensure that you have entered a valid book title or ISBN."
            )

        book_data = book_data["items"][0]["volumeInfo"]

        embed = discord.Embed(
            title=lyhelpers.truncate(book_data["title"], 256), colour=config.EMBED_COLOUR
        )
        embed.description = f"-# {book_data['subtitle']}\n" if book_data.get("subtitle") else ""

        if authors := book_data.get("authors"):
            embed.description += f"> **Authors**: {', '.join(authors)}"
        if subjects := book_data.get("categories"):
            embed.description += f"\n> **Subjects**: {', '.join(subjects)}"

        if page_count := book_data.get("pageCount"):
            embed.description += f"\n> **Pagecount**: {page_count}"

        if published_date := book_data.get("publishedDate"):
            embed.description += f"\n> **Published**: {format_published(published_date)}"

        if publisher := book_data.get("publisher"):
            embed.description += f"\n> **Publisher**: {publisher}"
        if book_description := book_data.get("description"):
            embed.description += (
                f"\n\n{lyhelpers.truncate(lyhelpers.strip_html(book_description), 300)}"
            )
        if thumbnail := book_data.get("imageLinks", {}).get("smallThumbnail"):
            embed.set_thumbnail(url=thumbnail)

        identifiers = {
            identifier["type"]: identifier["identifier"]
            for identifier in book_data.get("industryIdentifiers", [])
        }

        if identifiers:
            embed.set_footer(
                text=f"ISBN: {identifiers.get('ISBN_13') or identifiers.get('ISBN_10')}"
            )

        await ctx.reply(embed=embed, mention_author=False)

    async def search(self, query: str) -> dict:
        return await lyhelpers.request(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": query, "key": config.GOOGLE_API_KEY},
        )


async def setup(bot: commands.Bot):
    if config.GOOGLE_API_KEY:
        await bot.add_cog(Books(bot))
    else:
        raise lyerrors.TakinaMissingEnvironmentVariableError(
            "Visit https://console.cloud.google.com/apis/credentials for an API key."
        )
