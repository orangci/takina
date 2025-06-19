# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
from ..libs import oclib
import nextcord
import random
import urllib
import dotenv
import config

dotenv.load_dotenv()


class Fun(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.command(name="fact", help="Fetch a random fact.")
    async def fact(self, ctx: commands.Context):
        data = await oclib.request("https://uselessfacts.jsph.pl/api/v2/facts/random")
        fact = data.get("text")
        emoji = await oclib.fetch_random_emoji()
        embed = nextcord.Embed(description=f"{fact} {emoji}", color=config.EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="joke", aliases=["dadjoke"], help="Fetch a random joke.")
    async def joke(self, ctx: commands.Context):
        joke_type = random.choice(["dadjoke", "regular"])

        if joke_type == "dadjoke":
            headers = {"Accept": "application/json"}
            data = await oclib.request("https://icanhazdadjoke.com/", headers=headers)
            joke = data.get("joke")

        else:
            data = await oclib.request("https://v2.jokeapi.dev/joke/Any?safe-mode")
            while data.get("category") == "Christmas":
                data = await oclib.request("https://v2.jokeapi.dev/joke/Any?safe-mode")

            joke = data.get("joke")
            if not joke:
                setup = data.get("setup")
                delivery = data.get("delivery")
                joke = f"{setup}\n{delivery}"

        emoji = await oclib.fetch_random_emoji()

        embed = nextcord.Embed(description=f"{joke} {emoji}", color=config.EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="commit", help=f"Order {config.BOT_NAME.lower().capitalize()} to do anything.", usage="arson")
    async def commit(self, ctx: commands.Context):
        possible_responses = [
            "Yes, sir!",
            "I don't particularly feel like it.",
            "Why would I do that?",
            "Of course!",
            "Right away.",
            "As your majesty orders.",
            "No, I refuse.",
            "I don't want to, get lost.",
        ]

        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed.description = f"{random.choice(possible_responses)} {await oclib.fetch_random_emoji()}"
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="avatar", aliases=["av", "pfp"], help="Fetch the Discord user avatar of any member including yourself.")
    async def avatar(self, ctx: commands.Context, *, member: str = None):
        if member is None:
            member = ctx.author
        else:
            member = oclib.extract_user_id(member, ctx)
            if isinstance(member, nextcord.Embed):
                await ctx.reply(embed=member, mention_author=False)
                return

        if not isinstance(member, nextcord.Member):
            error_embed = nextcord.Embed(color=config.ERROR_COLOR)
            error_embed.description = ":x: I do not have access to this user's avatar."
            await ctx.reply(embed=error_embed, mention_author=False)
            return

        embed = nextcord.Embed(title=f"{member.name}'s Avatar", color=config.EMBED_COLOR)
        if member.display_avatar:
            embed.set_image(url=member.display_avatar.url)
        else:
            error_embed = nextcord.Embed(color=config.ERROR_COLOR)
            error_embed.description = "❌ This user does not have an avatar set."
            await ctx.reply(embed=error_embed, mention_author=False)
            return
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="google", help="Google anything!", usage="shawarma restaurants near me")
    async def google(self, ctx: commands.Context, *, query: str):
        query_before_conversion = query
        query = urllib.parse.quote_plus(query)
        emoji = await oclib.fetch_random_emoji()
        lmgtfy_url = f"https://letmegooglethat.com/?q={query}"
        embed = nextcord.Embed(
            title=f"{emoji}Let Me Google That For You!",
            description=f"Here is your search result for: **{query_before_conversion}**",
            url=lmgtfy_url,
            color=config.EMBED_COLOR,
        )
        embed.add_field(name="Click here:", value=lmgtfy_url, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="roll", help="Roll a random number from 1-100.")
    async def roll(self, ctx: commands.Context):
        embed = nextcord.Embed(
            title=f"What number did you roll? {await oclib.fetch_random_emoji()}",
            description=f"You rolled {random.randint(1, 100)}!",
            color=config.EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="8ball", help="Ask the 8ball anything.", usage="are you sentient")
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
            embed = nextcord.Embed(color=config.ERROR_COLOR)
            embed.description = "You need to ask a question to the 8ball for this command to work!"
            await ctx.reply(embed=embed, mention_author=False)
            return
        response = random.choice(responses)
        embed = nextcord.Embed(title="🎱 The 8ball", description=f"**Question:** {question}\n**Answer:** {response}", color=config.EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)


class SlashFun(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @nextcord.slash_command(name="fact", description="Fetch a random fact.")
    async def fact(self, interaction: nextcord.Interaction):
        data = await oclib.request("https://uselessfacts.jsph.pl/api/v2/facts/random")
        fact = data.get("text")
        emoji = await oclib.fetch_random_emoji()
        embed = nextcord.Embed(description=f"{fact} {emoji}", color=config.EMBED_COLOR)
        await interaction.send(embed=embed)

    @nextcord.slash_command(name="joke", description="Fetch a random joke.")
    async def joke(self, interaction: nextcord.Interaction):
        joke_type = random.choice(["dadjoke", "regular"])

        if joke_type == "dadjoke":
            headers = {"Accept": "application/json"}
            data = await oclib.request("https://icanhazdadjoke.com/", headers=headers)
            joke = data.get("joke")

        else:
            data = await oclib.request("https://v2.jokeapi.dev/joke/Any?safe-mode")
            while data.get("category") == "Christmas":
                data = await oclib.request("https://v2.jokeapi.dev/joke/Any?safe-mode")

            joke = data.get("joke")
            if not joke:
                setup = data.get("setup")
                delivery = data.get("delivery")
                joke = f"{setup}\n{delivery}"

        emoji = await oclib.fetch_random_emoji()

        embed = nextcord.Embed(description=f"{joke} {emoji}", color=config.EMBED_COLOR)
        await interaction.send(embed=embed)

    @nextcord.slash_command(name="commit", description="Order me to do something.")
    async def commit(
        self, interaction: nextcord.Interaction, action: str = nextcord.SlashOption(description="The action you'd like me to commit", required=True)
    ):
        possible_responses = [
            "Yes, sir!",
            "I don't particularly feel like it.",
            "Why would I do that?",
            "Of course!",
            "Right away.",
            "As your majesty orders.",
            "No, I refuse.",
            "I don't want to, get lost.",
        ]

        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed.description = f"{random.choice(possible_responses)} {await oclib.fetch_random_emoji()}"
        await interaction.send(embed=embed)

    @nextcord.slash_command(name="avatar", description="Fetch the Discord user avatar of any member including yourself.")
    async def avatar(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(description="The user whose avatar you would like to fetch", required=False),
    ):
        if member is None:
            member = interaction.user

        embed = nextcord.Embed(title=f"{member.name}'s Avatar", color=config.EMBED_COLOR)
        if member.display_avatar:
            embed.set_image(url=member.display_avatar.url)
        else:
            error_embed = nextcord.Embed(color=config.ERROR_COLOR)
            error_embed.description = "❌ This user does not have an avatar set."
            await interaction.send(embed=error_embed, ephemeral=True)
            return
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="google", description="Google anything!")
    async def google(self, interaction: nextcord.Interaction, *, query: str = nextcord.SlashOption(description="Your search query", required=True)):
        query_before_conversion = query
        query = urllib.parse.quote_plus(query)
        lmgtfy_url = f"https://letmegooglethat.com/?q={query}"
        emoji = await oclib.fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"{emoji}Let Me Google That For You!",
            description=f"Here is your search result for: **{query_before_conversion}**",
            url=lmgtfy_url,
            color=config.EMBED_COLOR,
        )
        embed.add_field(name="Click here:", value=lmgtfy_url, inline=False)
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="roll", description="Roll a random number from 1-100.")
    async def roll(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title=f"What number did you roll? {await oclib.fetch_random_emoji()}",
            description=f"You rolled {random.randint(1, 100)}!",
            color=config.EMBED_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="8ball", description="Ask the 8ball anything.")
    async def eight_ball(
        self, interaction: nextcord.Interaction, *, question: str = nextcord.SlashOption(description="Ask the 8ball a question!", required=True)
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
        embed = nextcord.Embed(title="🎱 The 8ball", description=f"**Question:** {question}\n**Answer:** {response}", color=config.EMBED_COLOR)
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Fun(bot))
    bot.add_cog(SlashFun(bot))
