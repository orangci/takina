from __future__ import annotations
from ..libs.oclib import *
import dotenv
import nextcord
from nextcord.ext import commands
from __main__ import EMBED_COLOR
import urllib
import random

dotenv.load_dotenv()


class Fun(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.command(
        name="fact",
        description="Fetch a random fact.",
        help="Usage: `fact`. This command utilizes the [uselessfacts](https://uselessfacts.jsph.pl) API.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def fact(self, ctx: commands.Context):
        data = await request("https://uselessfacts.jsph.pl/api/v2/facts/random")
        fact = data.get("text")
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            description=f"{fact} {emoji}",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="joke",
        aliases=["dadjoke"],
        description="Fetch a random joke.",
        help="Usage: `joke`. This command utlizes both the [Joke API](https://jokeapi.dev) and the [icanhazdadjoke](https://icanhazdadjoke.com) API.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
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

    @commands.command(
        name="commit",
        description="Fetch a random typical git commit message.",
        help="Usage: `commit`. This command utilizes the [whatthecommit](https://whatthecommit.com) API.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
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

    @commands.command(
        name="avatar",
        aliases=["av"],
        description="Fetch the Discord user avatar of any member including yourself.",
        help="Usage: `avatar username` or just `avatar`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def avatar(self, ctx: commands.Context, member: str = None):
        if member is None:
            member = ctx.author
        else:
            member = extract_user_id(member, ctx)
            if isinstance(member, str):
                embed = nextcord.Embed(description=member, color=0xFF0037)
                await ctx.reply(embed=embed, mention_author=False)
                return

        embed = nextcord.Embed(title=f"{member.name}'s Avatar", color=EMBED_COLOR)
        if member.avatar:
            embed.set_image(url=member.avatar.url)
        else:
            error_embed = nextcord.Embed(color=0xFF0037)
            error_embed.description = "❌ This user does not have an avatar set."
            await ctx.reply(embed=error_embed, mention_author=False)
            return
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="google",
        description="Google anything!",
        help="Usage: `google shawarma restaurants near me`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def google(self, ctx: commands.Context, *, query: str):
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

    @commands.command(
        name="roll",
        description="Roll a random number from 1-100.",
        help="Usage: `roll`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def roll(self, ctx: commands.Context):
        embed = nextcord.Embed(
            title=f"What number did you roll? {await fetch_random_emoji()}",
            description=f"You rolled {random.randint(1, 100)}!",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="8ball",
        description="Ask the 8ball anything.",
        help="Usage: `8ball are you sentient`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
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
            embed = nextcord.Embed(color=0xFF0037)
            embed.description = (
                "You need to ask a question to the 8ball for this command to work!"
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        response = random.choice(responses)
        embed = nextcord.Embed(
            title="🎱 The 8ball",
            description=f"**Question:** {question}\n**Answer:** {response}",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)


class SlashFun(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @nextcord.slash_command(name="fact", description="Fetch a random fact.")
    async def fact(self, interaction: nextcord.Interaction):
        data = await request("https://uselessfacts.jsph.pl/api/v2/facts/random")
        fact = data.get("text")
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            description=f"{fact} {emoji}",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed)

    @nextcord.slash_command(name="joke", description="Fetch a random joke.")
    async def joke(self, interaction: nextcord.Interaction):
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

    @nextcord.slash_command(
        name="commit", description="Fetch a random typical git commit message."
    )
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

    @nextcord.slash_command(
        name="avatar",
        description="Fetch the Discord user avatar of any member including yourself.",
    )
    async def avatar(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(
            description="The user whose avatar you would like to fetch", required=False
        ),
    ):
        if member is None:
            member = interaction.user

        embed = nextcord.Embed(title=f"{member.name}'s Avatar", color=EMBED_COLOR)
        if member.avatar:
            embed.set_image(url=member.avatar.url)
        else:
            error_embed = nextcord.Embed(color=0xFF0037)
            error_embed.description = "❌ This user does not have an avatar set."
            await interaction.send(embed=error_embed, ephemeral=True)
            return
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="google", description="Google anything!")
    async def google(
        self,
        interaction: nextcord.Interaction,
        *,
        query: str = nextcord.SlashOption(
            description="Your search query", required=True
        ),
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

    @nextcord.slash_command(
        name="roll",
        description="Roll a random number from 1-100.",
        description="Roll a number!",
    )
    async def roll(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title=f"What number did you roll? {await fetch_random_emoji()}",
            description=f"You rolled {random.randint(1, 100)}!",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(
        name="8ball",
        description="Ask the 8ball anything.",
        description="Ask the 8ball a question!",
    )
    async def eight_ball(
        self,
        interaction: nextcord.Interaction,
        *,
        question: str = nextcord.SlashOption(
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
    bot.add_cog(SlashFun(bot))
