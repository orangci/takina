from takina.libs import lyerrors, lyhelpers, lychecks
from discord.ext import commands
from takina import config
import discord


class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @lychecks.is_user_app()
    @commands.hybrid_command(
        name="mcskin",
        description="Fetch and display a Minecraft player's skin.",
        usage="orangci",
    )
    async def mcskin(self, ctx: commands.Context, username: str):
        data = await lyhelpers.request(
            f"https://api.mojang.com/users/profiles/minecraft/{username}"
        )
        if not data:
            raise lyerrors.TakinaNotFoundError(
                f"Could not find a Minecraft player with the username `{username}`."
            )

        uuid = data["id"]

        embed = discord.Embed(
            title=await lyhelpers.fetch_random_emoji() + username,
            color=config.EMBED_COLOR,
        )
        embed.set_image(url=f"https://visage.surgeplay.com/full/384/{uuid}")
        embed.set_footer(text=f"UUID: {uuid}")
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Minecraft(bot))
