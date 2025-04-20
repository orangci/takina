# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from ..libs.oclib import *
import nextcord
import base64
from nextcord.ext import commands
from io import BytesIO
from config import *


class MinecraftServerStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_server_info(self, server_name: str):
        url = f"https://api.mcstatus.io/v2/status/java/{server_name}"

        try:
            data = await request(url)
            if data:
                return data

        except Exception as e:
            raise e

    @commands.command(
        help="Display a Minecraft server's status. \nUsage: `mcstatus hypixel.net`.",
        aliases=["mcserver"],
    )
    async def mcstatus(self, ctx: commands.Context, *, server_name: str):
        try:
            server = await self.fetch_server_info(server_name)
        except:
            raise commands.UserInputError

        if not server.get("online"):
            error_embed = nextcord.Embed(
                description=":x: Server not found or is offline.", color=ERROR_COLOR
            )
            await ctx.reply(embed=error_embed, mention_author=False)
            return

        title = server.get("host")
        emoji = await fetch_random_emoji()
        title = emoji + title
        embed = nextcord.Embed(title=title, color=EMBED_COLOR)
        embed.description = ""

        try:
            embed.set_image(f"https://api.mcstatus.io/v2/widget/java/{server_name}")
        except:
            raise commands.DiscordException

        if server.get("version"):
            embed.description += f"-# {server["version"]["name_clean"]} (Java)"
        if server.get("motd"):
            embed.description += f"\n\n**MOTD**:\n```{server["motd"]["clean"]}```"

        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(
        name="mcstatus", description="Display a Minecraft server's status."
    )
    async def slash_mcstatus(
        self,
        interaction: nextcord.Interaction,
        *,
        server_name: str = nextcord.SlashOption(
            description="The Minecraft server IP to fetch information on", required=True
        ),
    ):
        await interaction.response.defer()
        try:
            server = await self.fetch_server_info(server_name)
        except:
            raise commands.UserInputError

        if not server.get("online"):
            error_embed = nextcord.Embed(
                description=":x: Server not found or is offline.", color=ERROR_COLOR
            )
            await interaction.send(embed=error_embed, ephemeral=True)
            return

        title = server.get("host")
        emoji = await fetch_random_emoji()
        title = emoji + title
        embed = nextcord.Embed(title=title, color=EMBED_COLOR)
        embed.description = ""

        try:
            embed.set_image(f"https://api.mcstatus.io/v2/widget/java/{server_name}")
        except:
            raise commands.DiscordException

        if server.get("version"):
            embed.description += f"-# {server["version"]["name_clean"]} (Java)"
        if server.get("motd"):
            embed.description += f"\n\n**MOTD**:\n```{server["motd"]["clean"]}```"

        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(MinecraftServerStatus(bot))
