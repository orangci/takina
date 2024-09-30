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
        query = urllib.parse.quote_plus(query)
        lmgtfy_url = f"https://letmegooglethat.com/?q={query}"
        embed = nextcord.Embed(
            title="Let Me Google That For You!",
            description=f"Here is your search result for: **{query}**",
            url=lmgtfy_url,
            color=EMBED_COLOR,
        )
        embed.add_field(name="Click here:", value=lmgtfy_url, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="roll")
    async def roll(self, ctx: commands.Context):
        number = random.randint(1, 100)
        embed = nextcord.Embed(
            title="What number did you roll?",
            description=f"You rolled a {number}!",
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

    @nextcord.slash_command(name="avatar")
    async def slash_avatar(
        self,
        interaction: nextcord.Interaction,
        member: str = SlashOption(
            description="The user whose avatar you would like to fetch", required=False
        ),
    ):
        if member is None:
            member = interaction.user
        else:
            member = extract_user_id(member, interaction)

        if not isinstance(member, nextcord.Member):
            await interaction.send(
                "Member not found. Please provide a valid username, display name, mention, or user ID.",
                ephemeral=True,
            )
            return
        embed = nextcord.Embed(title=f"{member.name}'s Avatar", color=EMBED_COLOR)
        embed.set_image(url=member.avatar.url)
        await interaction.send(embed=embed, mention_author=False)

    @nextcord.slash_command(name="google")
    async def slash_google(
        self,
        interaction: nextcord.Interaction,
        *,
        query: str = SlashOption(description="Your search query", required=True),
    ):
        query = urllib.parse.quote_plus(query)
        lmgtfy_url = f"https://letmegooglethat.com/?q={query}"
        embed = nextcord.Embed(
            title="Let Me Google That For You!",
            description=f"Here is your search result for: **{query}**",
            url=lmgtfy_url,
            color=EMBED_COLOR,
        )
        embed.add_field(name="Click here:", value=lmgtfy_url, inline=False)
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="roll", description="Roll a number!")
    async def slash_roll(self, interaction: nextcord.Interaction):
        number = random.randint(1, 100)
        embed = nextcord.Embed(
            title="What number did you roll?",
            description=f"You rolled a {number}!",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=True)

    # New slash 8ball command
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
