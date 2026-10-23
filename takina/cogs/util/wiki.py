# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers, lyviews
from discord.ext import commands
from takina import config
from typing import cast
import wikipediaapi
import discord

WIKIPEDIA_ICON = "https://upload.wikimedia.org/wikipedia/commons/2/2e/Wikipedia_W_favicon_on_white_background.png"
DISAMBIGUATION_CATEGORY = "Category:All disambiguation pages"
MAX_RANDOM_ATTEMPTS = 5
SUMMARY_PAGE_LENGTH = 750
LINKS_PAGE_LENGTH = 300


def paginate(lines: list[str], limit: int, separator: str) -> list[str]:
    pages: list[str] = []
    current = ""

    for line in lines:
        if current and len(current) + len(separator) + len(line) > limit:
            pages.append(current)
            current = line
        else:
            current = f"{current}{separator}{line}" if current else line

    if current:
        pages.append(current)

    # one overlong paragraph still has to fit an embed
    return [lyhelpers.truncate(page, 4096) for page in pages]


class Wikipedia(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        # one client for the cog, as each AsyncWikipedia opens its own connection pool
        self._wiki = wikipediaapi.AsyncWikipedia(user_agent=config.USER_AGENT, language="en")

    async def cog_unload(self):
        # the library offers no public way to close it
        await self._wiki._client.aclose()

    async def thumbnail_url(self, page: wikipediaapi.AsyncWikipediaPage) -> str:
        if images := await page.images:
            return await next(iter(images.values())).url

        return WIKIPEDIA_ICON

    async def summary_embeds(self, page: wikipediaapi.AsyncWikipediaPage) -> list[discord.Embed]:
        summary = await page.summary
        paragraphs = [paragraph for paragraph in summary.split("\n") if paragraph]
        chunks = paginate(paragraphs, SUMMARY_PAGE_LENGTH, "\n\n") or ["No summary available."]

        url = await page.fullurl
        thumbnail_url = await self.thumbnail_url(page)

        embeds: list[discord.Embed] = []
        for chunk in chunks:
            embed = discord.Embed(
                title=page.title, url=url, description=chunk, colour=config.EMBED_COLOUR
            )
            embed.set_footer(text="Powered by Wikipedia")
            embed.set_thumbnail(url=thumbnail_url)
            embeds.append(embed)

        return embeds

    async def disambiguation_embeds(
        self, page: wikipediaapi.AsyncWikipediaPage, page_name: str
    ) -> list[discord.Embed]:
        links = await page.links
        if not links:
            raise lyerrors.TakinaNotFoundError(
                "That is a disambiguation page, but it links to nothing."
            )

        title = lyhelpers.truncate(f'Disambiguations for "{page_name}"', 256)
        thumbnail_url = await self.thumbnail_url(page)

        embeds: list[discord.Embed] = []
        for chunk in paginate([f"- {name}" for name in links], LINKS_PAGE_LENGTH, "\n"):
            embed = discord.Embed(title=title, description=chunk, colour=config.EMBED_COLOUR)
            embed.set_thumbnail(url=thumbnail_url)
            embeds.append(embed)

        return embeds

    async def send_embeds(self, ctx: commands.Context, embeds: list[discord.Embed]) -> None:
        if len(embeds) == 1:
            await ctx.reply(embed=embeds[0], mention_author=False)
            return

        await lyviews.PaginatorView.send(ctx, embeds)

    @commands.hybrid_command(
        name="wiki",
        aliases=["wikipedia"],
        description="Query Wikipedia.",
        usage="Python (programming language)",
    )
    @lychecks.is_user_app()
    async def wiki(self, ctx: commands.Context, *, page_name: commands.Range[str, 1, 300]):
        await ctx.defer()

        wiki_page = self._wiki.page(page_name)

        if not await wiki_page.exists():
            raise lyerrors.TakinaNotFoundError(
                "That Wikipedia page does not exist. Try adjusting your capitalisation, as results are occasionally case-sensitive!"
            )

        if DISAMBIGUATION_CATEGORY in await wiki_page.categories:
            embeds = await self.disambiguation_embeds(wiki_page, page_name)
        else:
            embeds = await self.summary_embeds(wiki_page)

        await self.send_embeds(ctx, embeds)

    @commands.hybrid_command(
        name="randomwiki",
        aliases=["rwiki", "randomwikipedia"],
        description="Get a random Wikipedia page.",
    )
    @lychecks.is_user_app()
    async def randomwiki(self, ctx: commands.Context):
        await ctx.defer()

        for _ in range(MAX_RANDOM_ATTEMPTS):
            random_page = await self._wiki.random()
            # typed as the base page, though the async client always returns async pages
            wiki_page = cast(wikipediaapi.AsyncWikipediaPage, next(iter(random_page.values())))
            if DISAMBIGUATION_CATEGORY not in await wiki_page.categories:
                break
        else:
            raise lyerrors.TakinaError("Wikipedia kept offering disambiguation pages. Try again!")

        await self.send_embeds(ctx, await self.summary_embeds(wiki_page))


async def setup(bot: commands.Bot):
    await bot.add_cog(Wikipedia(bot))
