from takina.libs import lychecks, lyerrors, lyhelpers
from discord.ext import commands
from takina import config
import discord


class Steam(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_command(
        name="steam",
        aliases=["game"],
        description="Fetch information about a video game on Steam.",
        usage="Stray",
    )
    @lychecks.is_user_app()
    async def steam(self, ctx: commands.Context, *, game: str):
        search_results = await lyhelpers.request(
            f"https://store.steampowered.com/api/storesearch/?term={game}&l=english&cc={config.STEAM_REGION}"
        )

        items = search_results.get("items", [])

        if not search_results or not items:
            raise lyerrors.TakinaNotFoundError("Game not found.")

        app_id = items[0]["id"]

        response = await lyhelpers.request(
            f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc={config.STEAM_REGION}"
        )

        data = response[str(app_id)]["data"]

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = ""
        embed.title = data["name"]
        embed.url = f"https://store.steampowered.com/app/{app_id}"
        embed.set_footer(text=f"Steam APP ID: {app_id}")

        if thumbnail := data.get("capsule_image") or data.get("header_image"):
            embed.set_thumbnail(url=thumbnail)

        if data.get("is_free"):
            embed.description += "> **Price**: Free"

        elif price := data.get("price_overview", {}).get("final_formatted"):
            embed.description += f"> **Price**: {price}"

        if platforms := ", ".join(
            name.capitalize() for name, supported in data.get("platforms", {}).items() if supported
        ):
            embed.description += f"\n> **Platforms**: {platforms}"

        if genres := ", ".join(genre["description"] for genre in data.get("genres", [])):
            embed.description += f"\n> **Genres**: {genres}"

        if release_date := data.get("release_date", {}).get("date"):
            embed.description += f"\n> **Release Date**: {release_date}"

        if developers := ", ".join(data.get("developers", [])):
            embed.description += f"\n> **Developers**: {developers}"

        if publishers := ", ".join(data.get("publishers", [])):
            embed.description += f"\n> **Publishers**: {publishers}"

        if website := data.get("website"):
            embed.description += f"\n> **Website**: {website}"

        if short_description := data.get("short_description"):
            embed.description += f"\n\n{short_description}"

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Steam(bot))
