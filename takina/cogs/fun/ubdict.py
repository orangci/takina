# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import urllib

import aiohttp
import nextcord
import config
import re
from nextcord.ext import commands


class UrbanDictionary(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.command(help="Query Urban Dictionary for a definition.", usage="anime")
    async def ubdict(self, ctx: commands.Context, *, word: str):
        params = {"term": word}
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.urbandictionary.com/v0/define", params=params) as response:
                data = await response.json()
        if not data["list"]:
            embed = nextcord.Embed(color=config.ERROR_COLOR)
            embed.description = "❌ No results found."
            await ctx.reply(embed=embed, mention_author=False)
            return

        def format_text(text: str) -> str:
            """Trims the text to 300 characters and formats [anything] links."""
            # Replace [anything] with markdown-style links to Urban Dictionary
            text = re.sub(
                r"\[(.*?)\]",
                lambda match: f"[{match.group(1)}](https://www.urbandictionary.com/define.php?term={urllib.parse.quote(match.group(1))})",
                text,
            )
            # Trim the text to 300 characters, adding "..." if necessary
            return text[:300] + "..." if len(text) > 300 else text

        definition = format_text(data["list"][0]["definition"])
        example = format_text(data["list"][0]["example"]) if data["list"][0]["example"] else "No examples provided."

        embed = nextcord.Embed(title=data["list"][0]["word"], description=definition, url=data["list"][0]["permalink"], color=config.EMBED_COLOR)
        embed.add_field(name="Example", value=example, inline=False)
        embed.set_footer(text=f"👍 {data['list'][0]['thumbs_up']} | 👎 {data['list'][0]['thumbs_down']} | Powered by Urban Dictionary")
        embed.set_thumbnail(url="https://www.urbandictionary.com/favicon-32x32.png")
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="ubdict", description="Query Urban Dictionary for a definition.")
    async def slash_ubdict(
        self, interaction: nextcord.Interaction, word: str = nextcord.SlashOption(description="The word to define", required=True)
    ) -> None:
        await interaction.response.defer()
        params = {"term": word}
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.urbandictionary.com/v0/define", params=params) as response:
                data = await response.json()
        if not data["list"]:
            embed = nextcord.Embed(color=config.ERROR_COLOR)
            embed.description = "❌ No results found."
            await interaction.send(embed=embed, ephemeral=True)
            return

        def format_text(text: str) -> str:
            """Trims the text to 300 characters and formats [anything] links."""
            # Replace [anything] with markdown-style links to Urban Dictionary
            text = re.sub(
                r"\[(.*?)\]",
                lambda match: f"[{match.group(1)}](https://www.urbandictionary.com/define.php?term={urllib.parse.quote(match.group(1))})",
                text,
            )
            # Trim the text to 300 characters, adding "..." if necessary
            return text[:300] + "..." if len(text) > 300 else text

        definition = format_text(data["list"][0]["definition"])
        example = format_text(data["list"][0]["example"]) if data["list"][0]["example"] else "No examples provided."

        embed = nextcord.Embed(title=data["list"][0]["word"], description=definition, url=data["list"][0]["permalink"], color=config.EMBED_COLOR)
        embed.add_field(name="Example", value=example, inline=False)
        embed.set_footer(text=f"👍 {data['list'][0]['thumbs_up']} | 👎 {data['list'][0]['thumbs_down']} | Powered by Urban Dictionary")
        embed.set_thumbnail(url="https://www.urbandictionary.com/favicon-32x32.png")
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(UrbanDictionary(bot))
