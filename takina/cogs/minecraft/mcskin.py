# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import aiohttp
import nextcord
import config
from nextcord.ext import commands

from ..libs import oclib


class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_uuid(self, username: str) -> str:
        """Fetch the UUID of a Minecraft player by username."""
        url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("id")
                else:
                    return None

    async def fetch_skin_url(self, uuid: str) -> str:
        """Fetch the skin image URL of a Minecraft player by UUID."""
        skin_url = f"https://visage.surgeplay.com/full/384/{uuid}"
        return skin_url

    @commands.command(name="mcskin", help="Fetch and display a Minecraft player's skin.", usage="orangci")
    async def mcskin(self, ctx: commands.Context, username: str):
        uuid = await self.fetch_uuid(username)

        if not uuid:
            error_embed = nextcord.Embed(color=config.ERROR_COLOR)
            error_embed.description = f":x: Could not find a Minecraft player with the username `{username}`."
            await ctx.reply(embed=error_embed, mention_author=False)
            return

        skin_url = await self.fetch_skin_url(uuid)

        embed = nextcord.Embed(title=await oclib.fetch_random_emoji() + username, color=config.EMBED_COLOR)
        embed.set_image(url=skin_url)
        embed.set_footer(text=f"UUID: {uuid}")
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="mcskin", description="Fetch and display a Minecraft player's skin.")
    async def slash_mcskin(
        self,
        interaction: nextcord.Interaction,
        username: str = nextcord.SlashOption(description="The Minecraft player whose skin you'd like to fetch", required=True),
    ):
        await interaction.response.defer()
        uuid = await self.fetch_uuid(username)

        if not uuid:
            error_embed = nextcord.Embed(color=config.ERROR_COLOR)
            error_embed.description = f":x: Could not find a Minecraft player with the username `{username}`."
            await interaction.send(embed=error_embed, ephemeral=True)
            return

        skin_url = await self.fetch_skin_url(uuid)

        embed = nextcord.Embed(title=await oclib.fetch_random_emoji() + username, color=config.EMBED_COLOR)
        embed.set_image(url=skin_url)
        embed.set_footer(text=f"UUID: {uuid}")
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Minecraft(bot))
