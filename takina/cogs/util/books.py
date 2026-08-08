from takina.libs import lychecks, lyerrors, lyhelpers
from discord.ext import commands
from datetime import datetime
from takina import config
import discord


class Books(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @lychecks.is_user_app()
    @commands.hybrid_command(
        description="Fetch information on a book title or ISBN.",
        usage="Yumi and the Nightmare Painter",
        aliases=["books"],
    )
    async def book(self, ctx: commands.Context, *, book: str):
        book_data = await lyhelpers.request(
            f"https://www.googleapis.com/books/v1/volumes?q=intitle:{book}&key={config.GOOGLE_BOOKS_API_KEY}"
        )

        if not book_data.get("items"):
            book_data = await lyhelpers.request(
                f"https://www.googleapis.com/books/v1/volumes?q=isbn:{book}&key={config.GOOGLE_BOOKS_API_KEY}"
            )

        if not book_data.get("items"):
            raise lyerrors.TakinaNotFoundError(
                "The book specified does not exist in the database. Please ensure that you have entered a valid book title or ISBN."
            )

        book_data = book_data["items"][0]["volumeInfo"]

        embed = discord.Embed(title=book_data["title"], color=config.EMBED_COLOR)
        embed.description = (
            f"-# {book_data['subtitle']}\n" if book_data.get("subtitle") else ""
        )

        if authors := book_data.get("authors"):
            embed.description += (
                f"> **Authors**: {', '.join(author for author in authors)}"
            )
        if subjects := book_data.get("categories"):
            embed.description += (
                f"\n> **Subjects**: {', '.join(subject for subject in subjects)}"
            )

        if page_count := book_data.get("pageCount"):
            embed.description += f"\n> **Pagecount**: {page_count}"

        if published_date := book_data.get("publishedDate"):
            published = datetime.fromisoformat(
                published_date + ("-01-01" if len(published_date) == 4 else "")
            ).date()

            embed.description += f"\n> **Published**: <t:{int(datetime.combine(published, datetime.min.time()).timestamp())}:D>"

        if publisher := book_data.get("publisher"):
            embed.description += f"\n> **Publisher**: {publisher}"
        if book_description := book_data.get("description"):
            embed.description += f"\n\n{book_description[:300] + '...' if len(book_description) > 300 else book_description}"
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


async def setup(bot: commands.Bot):
    if config.GOOGLE_BOOKS_API_KEY:
        await bot.add_cog(Books(bot))
    else:
        raise lyerrors.TakinaMissingEnvironmentVariableError(
            "Visit https://console.cloud.google.com/apis/credentials for an API key."
        )
