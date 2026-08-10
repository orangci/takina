from takina.libs import lychecks, lyerrors, lyviews
from discord.ext import commands
from takina import config
import wikipediaapi
import discord


class Wikipedia(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_command(
        name="wiki",
        aliases=["wikipedia"],
        description="Query Wikipedia.",
        usage="Python (programming language)",
    )
    @lychecks.is_user_app()
    async def wiki(self, ctx: commands.Context, *, page_name: str):
        wiki = wikipediaapi.AsyncWikipedia(user_agent=config.USER_AGENT, language="en")
        wiki_page = wiki.page(page_name)

        if not await wiki_page.exists():
            raise lyerrors.TakinaNotFoundError(
                "That Wikipedia page does not exist. Try adjusting your capitalisation, as results are occasionally case-sensitive!"
            )

        page_images = await wiki_page.images

        if "Category:All disambiguation pages" in (await wiki_page.categories):
            page_links = await wiki_page.links

            embeds: list[discord.Embed] = []
            current_embed = discord.Embed(colour=config.EMBED_COLOUR)
            current_embed.title = f'Disambiguations for "{page_name}"'
            current_embed.description = ""

            for name in page_links:
                entry = f"\n- {name}"

                if len(current_embed.description) + len(entry) > 300:
                    embeds.append(current_embed)
                    current_embed = discord.Embed(colour=config.EMBED_COLOUR)
                    current_embed.title = f'Disambiguations for "{page_name}"'
                    current_embed.description = entry
                else:
                    current_embed.description += entry

            if current_embed.description:
                embeds.append(current_embed)

        else:
            page_summary = await wiki_page.summary
            paragraphs = [paragraph for paragraph in page_summary.split("\n") if paragraph]

            chunks = []
            current = ""
            for paragraph in paragraphs:
                if len(current) + len(paragraph) + 2 > 750:
                    if current:
                        chunks.append(current)
                    current = paragraph
                else:
                    if current:
                        current += "\n\n"
                    current += paragraph

            if current:
                chunks.append(current)

            embeds = []

            for chunk in chunks:
                embed = discord.Embed(colour=config.EMBED_COLOUR)
                embed.title = wiki_page.title
                embed.url = await wiki_page.fullurl
                embed.set_footer(text="Powered by Wikipedia")
                embed.description = chunk
                embeds.append(embed)

        if page_images:
            image = next(iter(page_images.values()))
            thumbnail_url = await image.url
        else:
            thumbnail_url = "https://upload.wikimedia.org/wikipedia/commons/2/2e/Wikipedia_W_favicon_on_white_background.png"

        for embed in embeds:
            embed.set_thumbnail(url=thumbnail_url)

        if len(embeds) == 1:
            await ctx.reply(embed=embeds[0], mention_author=False)
            return

        await ctx.reply(
            embed=embeds[0], view=lyviews.PaginatorView(ctx.author, embeds), mention_author=False
        )

    @commands.hybrid_command(
        name="randomwiki",
        aliases=["rwiki", "randomwikipedia"],
        description="Get a random Wikipedia page.",
    )
    @lychecks.is_user_app()
    async def randomwiki(self, ctx: commands.Context):
        wiki = wikipediaapi.AsyncWikipedia(user_agent=config.USER_AGENT, language="en")
        while True:
            random_page = await wiki.random()
            wiki_page = next(iter(random_page.values()))
            if "Category:All disambiguation pages" not in (await wiki_page.categories):
                break

        page_summary = await wiki_page.summary
        page_images = await wiki_page.images
        paragraphs = [paragraph for paragraph in page_summary.split("\n") if paragraph]

        chunks = []
        current = ""

        for paragraph in paragraphs:
            if len(current) + len(paragraph) + 2 > 750:
                if current:
                    chunks.append(current)
                current = paragraph
            else:
                if current:
                    current += "\n\n"
                current += paragraph

        if current:
            chunks.append(current)

        embeds = []

        for chunk in chunks:
            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.title = wiki_page.title
            embed.url = await wiki_page.fullurl
            embed.set_footer(text="Powered by Wikipedia")
            embed.description = chunk
            embeds.append(embed)

        if page_images:
            image = next(iter(page_images.values()))
            thumbnail_url = await image.url
        else:
            thumbnail_url = "https://upload.wikimedia.org/wikipedia/commons/2/2e/Wikipedia_W_favicon_on_white_background.png"

        for embed in embeds:
            embed.set_thumbnail(url=thumbnail_url)

        if len(embeds) == 1:
            await ctx.reply(embed=embeds[0], mention_author=False)
            return

        await ctx.reply(
            embed=embeds[0], view=lyviews.PaginatorView(ctx.author, embeds), mention_author=False
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Wikipedia(bot))
