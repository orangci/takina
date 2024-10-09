from __future__ import annotations
from ..libs.oclib import *
import dotenv
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
from __main__ import EMBED_COLOR
import urllib
import random

dotenv.load_dotenv()


class Fun(commands.Cog):
    def __init__(self, bot):
        self._bot = bot
        latency = bot.latency

    @commands.command(name="fact")
    async def fact(self, ctx: commands.Context):
        data = await request("https://uselessfacts.jsph.pl/api/v2/facts/random")
        fact = data.get("text")
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            description=f"{fact} {emoji}",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="joke", aliases=["dadjoke"])
    async def joke(self, ctx: commands.Context):
        joke_type = random.choice(["dadjoke", "regular"])

        if joke_type == "dadjoke":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://icanhazdadjoke.com/",
                    headers={"Accept": "application/json"},
                ) as response:
                    data = await response.json()

            joke = data.get("joke")

        else:
            data = await request("https://v2.jokeapi.dev/joke/Any?safe-mode")
            while data.get("category") == "Christmas":
                data = await request("https://v2.jokeapi.dev/joke/Any?safe-mode")

            joke = data.get("joke")
            if not joke:
                setup = data.get("setup")
                delivery = data.get("delivery")
                joke = f"{setup}\n{delivery}"

        emoji = await fetch_random_emoji()

        embed = nextcord.Embed(
            description=f"{joke} {emoji}",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="commit")
    async def commit(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://whatthecommit.com/index.txt") as response:
                commit_message = await response.text()

        embed = nextcord.Embed(
            title=f"Most normal commit message {await fetch_random_emoji()}",
            description=commit_message,
            color=EMBED_COLOR,
        )

    await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="avatar")
    async def avatar(self, ctx: commands.Context, member: str = None):
        if member is None:
            member = ctx.author
        else:
            member = extract_user_id(member, ctx)

        if not isinstance(member, nextcord.Member):
            await ctx.reply(
                "Member not found. Please provide a valid username, display name, mention, or user ID.",
                mention_author=False,
            )
            return
        embed = nextcord.Embed(title=f"{member.name}'s Avatar", color=EMBED_COLOR)
        embed.set_image(url=member.avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="google")
    async def google(self, ctx: commands.Context, *, query: str):
        """Google a query. Usage: `google query`."""
        query_before_conversion = query
        query = urllib.parse.quote_plus(query)
        emoji = await fetch_random_emoji()
        lmgtfy_url = f"https://letmegooglethat.com/?q={query}"
        embed = nextcord.Embed(
            title=f"{emoji} Let Me Google That For You!",
            description=f"Here is your search result for: **{query_before_conversion}**",
            url=lmgtfy_url,
            color=EMBED_COLOR,
        )
        embed.add_field(name="Click here:", value=lmgtfy_url, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="roll")
    async def roll(self, ctx: commands.Context):
        number = random.randint(1, 100)
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"What number did you roll? {emoji}",
            description=f"You rolled {number}!",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="8ball")
    async def eight_ball(self, ctx: commands.Context, *, question: str = None):
        responses = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes, definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
        ]
        if not question:
            await ctx.reply(
                "You need to ask a question for the 8ball!", mention_author=False
            )
            return
        response = random.choice(responses)
        embed = nextcord.Embed(
            title="🎱 The 8ball",
            description=f"**Question:** {question}\n**Answer:** {response}",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)


class FunSlash(commands.Cog):
    def __init__(self, bot):
        self._bot = bot
        latency = bot.latency

    @nextcord.slash_command(name="fact")
    async def slash_fact(self, interaction: nextcord.Interaction):
        data = await request("https://uselessfacts.jsph.pl/api/v2/facts/random")
        fact = data.get("text")
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            description=f"{fact} {emoji}",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed)

    @nextcord.slash_command(name="joke")
    async def slash_joke(self, interaction: nextcord.Interaction):
        joke_type = random.choice(["dadjoke", "regular"])

        if joke_type == "dadjoke":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://icanhazdadjoke.com/",
                    headers={"Accept": "application/json"},
                ) as response:
                    data = await response.json()

            joke = data.get("joke")

        else:
            data = await request("https://v2.jokeapi.dev/joke/Any?safe-mode")
            while data.get("category") == "Christmas":
                data = await request("https://v2.jokeapi.dev/joke/Any?safe-mode")

            joke = data.get("joke")
            if not joke:
                setup = data.get("setup")
                delivery = data.get("delivery")
                joke = f"{setup}\n{delivery}"

        emoji = await fetch_random_emoji()

        embed = nextcord.Embed(
            description=f"{joke} {emoji}",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed)

    @commands.command(name="commit")
    async def commit(self, interaction: nextcord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://whatthecommit.com/index.txt") as response:
                commit_message = await response.text()

        embed = nextcord.Embed(
            title=f"Most normal commit message {await fetch_random_emoji()}",
            description=commit_message,
            color=EMBED_COLOR,
        )

        await interaction.send(embed=embed)

    @nextcord.slash_command(name="avatar")
    async def slash_avatar(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = SlashOption(
            description="The user whose avatar you would like to fetch", required=False
        ),
    ):
        if member is None:
            member = interaction.user

        embed = nextcord.Embed(title=f"{member.name}'s Avatar", color=EMBED_COLOR)
        embed.set_image(url=member.avatar.url)
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="google")
    async def slash_google(
        self,
        interaction: nextcord.Interaction,
        *,
        query: str = SlashOption(description="Your search query", required=True),
    ):
        query_before_conversion = query
        query = urllib.parse.quote_plus(query)
        lmgtfy_url = f"https://letmegooglethat.com/?q={query}"
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"{emoji} Let Me Google That For You!",
            description=f"Here is your search result for: **{query_before_conversion}**",
            url=lmgtfy_url,
            color=EMBED_COLOR,
        )
        embed.add_field(name="Click here:", value=lmgtfy_url, inline=False)
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="roll", description="Roll a number!")
    async def slash_roll(self, interaction: nextcord.Interaction):
        number = random.randint(1, 100)
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"What number did you roll? {emoji}",
            description=f"You rolled {number}!",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="8ball", description="Ask the 8ball a question!")
    async def slash_eight_ball(
        self,
        interaction: nextcord.Interaction,
        *,
        question: str = SlashOption(
            description="Ask the 8ball a question!", required=True
        ),
    ):
        responses = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes, definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
        ]
        response = random.choice(responses)
        embed = nextcord.Embed(
            title="🎱 The 8ball",
            description=f"**Question:** {question}\n**Answer:** {response}",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Fun(bot))
    bot.add_cog(FunSlash(bot))
