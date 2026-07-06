# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
from urllib.parse import quote
from ..libs import oclib
import nextcord
import config


class Steam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def build_game_embed(self, game: str) -> nextcord.Embed:
        embed = nextcord.Embed(color=config.EMBED_COLOR, description="")
        game_encoded = quote(game)
        try:
            search_results = await oclib.request(
                f"https://store.steampowered.com/api/storesearch/?term={game_encoded}&l=english&cc={config.STEAM_REGION}"
            )
            items = search_results.get("items", [])
            if not items:
                embed.description = ":x: Game not found."
                embed.color = config.ERROR_COLOR
                return embed

            app_id = items[0]["id"]

            response = await oclib.request(f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc={config.STEAM_REGION}")
            data = response[str(app_id)]["data"]
            platforms = ", ".join(name.capitalize() for name, supported in data.get("platforms", {}).items() if supported)
            genres = ", ".join(g["description"] for g in data.get("genres", []))
            price = data.get("price_overview", {}).get("final_formatted")
            release_date = data.get("release_date", {}).get("date", "")
            developers = ", ".join(data.get("developers", []))
            publishers = ", ".join(data.get("publishers", []))
            short_description = data.get("short_description")
            website = data.get("website", "")

            embed.title = data["name"]
            embed.set_footer(text="Steam APP ID: " + str(app_id))
            embed.set_thumbnail(url=data.get("capsule_image") or data.get("header_image"))
            lines = []

            if data.get("is_free"):
                lines.append("> **Price**: Free")
            elif price:
                lines.append(f"> **Price**: {price}")
            if platforms != "":
                lines.append(f"> **Platforms**: {platforms}")
            if genres != "":
                lines.append(f"> **Genres**: {genres}")
            if release_date:
                lines.append(f"> **Release Date**: {release_date}")
            if developers != "":
                lines.append(f"> **Developers**: {developers}")
            if publishers != "":
                lines.append(f"> **Publishers**: {publishers}")
            if website:
                lines.append(f"> **Website**: {website}")

            embed.description = "\n".join(lines)
            if short_description:
                embed.description += f"\n\n{short_description}"
            return embed

        except Exception as e:
            embed.title = None
            embed.description = ":x: " + str(e)
            embed.color = config.ERROR_COLOR
            return embed

    @commands.command(aliases=["game"], help="Fetch information about a video game on Steam.", usage="Stray")
    async def steam(self, ctx: commands.Context, *, game: str):
        embed = await self.build_game_embed(game)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="steam", description="Fetch information about a video game on Steam.")
    async def slash_steam(
        self, interaction: nextcord.Interaction, *, game: str = nextcord.SlashOption(description="Title of the video game on Steam to look up")
    ):
        await interaction.response.defer()
        embed = await self.build_game_embed(game)
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(Steam(bot))
