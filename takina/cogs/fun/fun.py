# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyhelpers
from takina.libs.topics_list import topics
from discord.ext import commands
from takina import config
from urllib import parse
import discord
import random


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(description="Fetch a random fact.")
    @lychecks.is_user_app()
    async def fact(self, ctx: commands.Context) -> None:
        data = await lyhelpers.request("https://uselessfacts.jsph.pl/api/v2/facts/random")
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{data.get('text')} {await lyhelpers.fetch_random_emoji()}"
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(aliases=["dadjoke"], description="Fetch a random joke.")
    @lychecks.is_user_app()
    async def joke(self, ctx: commands.Context) -> None:
        joke_type = random.choice(["dadjoke", "regular"])

        if joke_type == "dadjoke":
            headers = {"Accept": "application/json"}
            data = await lyhelpers.request("https://icanhazdadjoke.com/", headers=headers)
            joke = data.get("joke")

        else:
            data = await lyhelpers.request("https://v2.jokeapi.dev/joke/Any?safe-mode")
            while data.get("category") == "Christmas":
                data = await lyhelpers.request("https://v2.jokeapi.dev/joke/Any?safe-mode")

            joke = data.get("joke")
            if not joke:
                setup = data.get("setup")
                delivery = data.get("delivery")
                joke = f"{setup}\n{delivery}"

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{joke} {await lyhelpers.fetch_random_emoji()}"
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        description=f"Order {config.BOT_NAME.title()} to do anything.", usage="arson"
    )
    @lychecks.is_user_app()
    async def commit(self, ctx: commands.Context, *, action: str) -> None:
        possible_responses = [
            "Yes, sir!",
            "I don't particularly feel like it.",
            "Why would I do that?",
            "Of course!",
            "Right away.",
            "As your majesty orders.",
            "No, I refuse.",
            "I don't want to, so get lost.",
        ]

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{lyhelpers.randint_from_seed(action, possible_responses)} {await lyhelpers.fetch_random_emoji()}"
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(description="Google anything!", usage="shawarma restaurants near me")
    @lychecks.is_user_app()
    async def google(self, ctx: commands.Context, *, query: str) -> None:
        query_before_conversion = query
        query = parse.quote_plus(query)

        emoji = await lyhelpers.fetch_random_emoji()
        lmgtfy_url = f"https://letmegooglethat.com/?q={query}"

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = f"{emoji}Let Me Google That For You!"
        embed.description = f"Here is your search result for: **{query_before_conversion}**"
        embed.url = lmgtfy_url
        embed.add_field(name="Click here:", value=lmgtfy_url, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="roll", description="Roll a random number from 1—100.")
    @lychecks.is_user_app()
    async def roll(self, ctx: commands.Context) -> None:
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = (
            f"{await lyhelpers.fetch_random_emoji()} You rolled {random.randint(1, 100)}!"
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(description="Fetch a random image of Gary.")
    @lychecks.has_permissions(embed_links=True)
    @lychecks.is_user_app()
    async def gary(self, ctx: commands.Context) -> None:
        data = await lyhelpers.request("https://api.garythe.cat/gary")
        embed = discord.Embed(colour=config.EMBED_COLOUR, title="Gary")
        embed.set_image(url=data.get("url"))
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(description="Fetch a random image of Goober.")
    @lychecks.has_permissions(embed_links=True)
    @lychecks.is_user_app()
    async def goober(self, ctx: commands.Context) -> None:
        data = await lyhelpers.request("https://api.garythe.cat/goober")
        embed = discord.Embed(colour=config.EMBED_COLOUR, title="Goober")
        embed.set_image(url=data.get("url"))
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(description="Get roasted by the bot.")
    @lychecks.is_user_app()
    async def roast(
        self, ctx: commands.Context, target: discord.User | discord.Member | None = None
    ):
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        response = await lyhelpers.request(
            "https://insult.mattbas.org/api/insult", disable_json=True
        )
        embed.description = await lyhelpers.fetch_random_emoji() + response + "."
        await ctx.reply(target.mention if target else None, embed=embed, mention_author=False)

    @commands.hybrid_command(description="Fetch a random conversational topic.")
    @lychecks.is_user_app()
    async def topic(self, ctx: commands.Context) -> None:
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = random.choice(topics) + await lyhelpers.fetch_random_emoji()
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))
