from __future__ import annotations
import aiohttp
import dotenv
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
from __main__ import EMBED_COLOR
import urllib
import random 

dotenv.load_dotenv()

async def request(*args, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request(*args, **kwargs) as ans:
            return await ans.json()


class Fun(commands.Cog):
    def __init__(self, bot):
        self._bot = bot
        latency = bot.latency
    
    @commands.command(name="avatar")
    async def avatar(self, ctx: commands.Context, member: nextcord.Member = None):
        member = member or ctx.author
        embed = nextcord.Embed(title=f"{member.name}'s Avatar", color=EMBED_COLOR)
        embed.set_image(url=member.avatar.url)
        await ctx.reply(embed=embed, mention_author=False)
        
    @commands.command(name="google")
    async def google(self, ctx: commands.Context, *, query: str):
        query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={query}"
        await ctx.reply(f"Here are the Google search results for: {query}\n{url}", mention_author=False)
        
    @commands.command(name="roll")
    async def roll(self, ctx: commands.Context):
        number = random.randint(1, 100)
        embed = nextcord.Embed(
            title="What number did you roll?",
            description=f"You rolled a {number}!",
            color=EMBED_COLOR
        )
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="avatar")
    async def slash_avatar(self, interaction: nextcord.Interaction, member: nextcord.Member = SlashOption(
            description="The user whose avatar you would like to fetch", required=False
        )):
        member = member or ctx.author
        embed = nextcord.Embed(title=f"{member.name}'s Avatar", color=EMBED_COLOR)
        embed.set_image(url=member.avatar.url)
        await interaction.send(embed=embed, mention_author=False)
        
    @nextcord.slash_command(name="google")
    async def slash_google(self, interaction: nextcord.Interaction, *, query: str = SlashOption(
            description="Your search query", required=True
        )):
        query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={query}"
        await interaction.send(f"Here are the Google search results for: {query}\n{url}")
    
    @nextcord.slash_command(name="roll", description="Roll a number!")
    async def slash_roll(self, interaction: nextcord.Interaction):
        number = random.randint(1, 100)
        embed = nextcord.Embed(
            title="What number did you roll?",
            description=f"You rolled a {number}!",
            color=EMBED_COLOR
        )
        await interaction.send(embed=embed)

def setup(bot):
    bot.add_cog(Fun(bot))
