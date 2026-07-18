# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: okcoder1, orangc
from nextcord.ext import commands
import wikipediaapi
import nextcord
import config


def format_text(text: str) -> str:
    """Trims the text to 500 characters."""
    # Trim the text to 500 characters, adding "..." if necessary
    return text[:500].strip() + "..." if len(text) > 500 else text


class Wikipedia(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def build_wikipedia_embed(self, page_name: str, bot_id: int) -> nextcord.Embed:
        """Fetches a Wikipedia page and returns an embed with the page's title, summary, and thumbnail."""
        wiki = wikipediaapi.AsyncWikipedia(
            user_agent=f"{config.BOT_NAME}-{str(bot_id)}/{config.BOT_VERSION} (https://takina.orangc.net)", language="en"
        )

        wiki_page = wiki.page(page_name)

        if not await wiki_page.exists():  # Check if page exists
            embed = nextcord.Embed(color=config.ERROR_COLOR)
            embed.description = (
                ":x: That Wikipedia page does not exist. Try adjusting your capitalisation, as results are occasionally case-sensitive!"
            )
            return embed

        elif "Category:All disambiguation pages" in (await wiki_page.categories):  # Check for disambiguation pages
            page_summary = f'Disambiguations for "{page_name}":'

            page_links = await wiki_page.links
            for name in page_links:
                page_summary += f"\n- {name}"

            page_images = {}
            page_summary = format_text(page_summary)
        else:
            page_images = await wiki_page.images
            page_summary = format_text(await wiki_page.summary)

        embed = nextcord.Embed(title=wiki_page.title, description=page_summary, url=(await wiki_page.fullurl), color=config.EMBED_COLOR)
        embed.set_footer(text="Powered by Wikipedia")
        if page_images:
            img = next(iter(page_images.values()))
            embed.set_thumbnail(url=await img.url)
        else:
            embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/2/2e/Wikipedia_W_favicon_on_white_background.png")

        return embed

    async def build_randomwiki_embed(self, bot_id: int) -> nextcord.Embed:
        wiki = wikipediaapi.AsyncWikipedia(
            user_agent=f"{config.BOT_NAME}-{str(bot_id)}/{config.BOT_VERSION} (https://takina.orangc.net)", language="en"
        )

        random_page = await wiki.random()  # Gets a random Wikipedia page
        wiki_page = next(iter(random_page.values()))

        page_images = await wiki_page.images
        page_summary = format_text(await wiki_page.summary)
        embed = nextcord.Embed(title=wiki_page.title, description=page_summary, url=(await wiki_page.fullurl), color=config.EMBED_COLOR)
        embed.set_footer(text="Powered by Wikipedia")
        if page_images:
            img = next(iter(page_images.values()))
            embed.set_thumbnail(url=await img.url)
        else:
            embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/2/2e/Wikipedia_W_favicon_on_white_background.png")
        return embed

    @commands.command(aliases=["wikipedia"], help="Query Wikipedia.", usage="Python (programming language)")
    async def wiki(self, ctx: commands.Context, *, page_name: str):
        embed = await self.build_wikipedia_embed(page_name, self.bot.application_id)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="wiki", description="Query Wikipedia.")
    async def slash_wiki(
        self, interaction: nextcord.Interaction, page_name: str = nextcord.SlashOption(description="The Wikipedia page to query", required=True)
    ) -> None:
        await interaction.response.defer()
        embed = await self.build_wikipedia_embed(page_name, self.bot.application_id)
        await interaction.send(embed=embed)

    @commands.command(aliases=["rwiki", "randomwikipedia"], help="Get a random Wikipedia page.")
    async def randomwiki(self, ctx: commands.Context):
        embed = await self.build_randomwiki_embed(self.bot.application_id)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="randomwiki", description="Get a random Wikipedia page.")
    async def slash_randomwiki(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        embed = await self.build_randomwiki_embed(self.bot.application_id)
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(Wikipedia(bot))
