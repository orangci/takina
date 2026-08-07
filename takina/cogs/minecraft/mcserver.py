from takina.libs import lyerrors, lyhelpers, lychecks
from discord.ext import commands
from takina import config
import discord


class MinecraftServerStatus(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @lychecks.is_user_app()
    @commands.hybrid_command(
        help="Display a Minecraft server's status.",
        usage="hypixel.net",
        aliases=["mcserver"],
    )
    async def mcstatus(self, ctx: commands.Context, *, server_name: str):
        data = await lyhelpers.request(
            f"https://api.mcstatus.io/v2/status/java/{server_name}"
        )

        if not data or not data.get("online"):
            raise lyerrors.TakinaNotFoundError("Server not found or is offline.")

        embed = discord.Embed(color=config.EMBED_COLOR)
        embed.title = await lyhelpers.fetch_random_emoji() + data.get("host")
        embed.set_image(url=f"https://api.mcstatus.io/v2/widget/java/{server_name}")
        embed.description = ""

        if data.get("version"):
            embed.description += f"-# {data['version']['name_clean']} (Java)"
        if data.get("motd"):
            embed.description += f"\n\n**MOTD**:\n```{data['motd']['clean']}```"

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(MinecraftServerStatus(bot))
