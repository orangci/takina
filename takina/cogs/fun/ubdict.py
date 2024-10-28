from __future__ import annotations
from ..libs.oclib import *
import aiohttp
import nextcord
from nextcord.ext import commands
from __main__ import EMBED_COLOR


class UrbanDictionary(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.command()
    async def ubdict(self, ctx: commands.Context, *, word: str):
        """Query Urban Dictionary. Usage: `ubdict word`."""
        params = {"term": word}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.urbandictionary.com/v0/define", params=params
            ) as response:
                data = await response.json()
        if not data["list"]:
            embed = nextcord.Embed(color=0xFF0037)
            embed.description = "❌ No results found."
            await ctx.reply(embed=embed, mention_author=False)
        embed = nextcord.Embed(
            title=data["list"][0]["word"],
            description=data["list"][0]["definition"],
            url=data["list"][0]["permalink"],
            color=EMBED_COLOR,
        )
        embed.set_footer(
            text=f"👍 {data['list'][0]['thumbs_up']} | 👎 {data['list'][0]['thumbs_down']} | Powered by: Urban Dictionary"
        )
        embed.set_thumbnail(url="https://www.urbandictionary.com/favicon-32x32.png")
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="ubdict")
    async def ubdict_slash(
        self,
        interaction: nextcord.Interaction,
        word: str = nextcord.SlashOption(
            description="The word to search for", required=True
        ),
    ) -> None:
        params = {"term": word}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.urbandictionary.com/v0/define", params=params
            ) as response:
                data = await response.json()
        if not data["list"]:
            embed = nextcord.Embed(color=0xFF0037)
            embed.description = "❌ No results found."
            await interaction.send(embed=embed, ephemeral=True)
            return
        embed = nextcord.Embed(
            title=data["list"][0]["word"],
            description=data["list"][0]["definition"],
            url=data["list"][0]["permalink"],
            color=EMBED_COLOR,
        )
        embed.set_footer(
            text=f"👍 {data['list'][0]['thumbs_up']} | 👎 {data['list'][0]['thumbs_down']} | Powered by: Urban Dictionary"
        )
        embed.set_thumbnail(url="https://www.urbandictionary.com/favicon-32x32.png")
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(UrbanDictionary(bot))
