import nextcord
from nextcord.ext import commands
import config
from ..libs import oclib

async def request_api(type: str) -> nextcord.Embed:
    url = f"https://api.iostpa.com/{type}"
    data = await oclib.request(url)
    image_url = data.get("image_link")

    embed = nextcord.Embed(color=config.EMBED_COLOR)
    embed.set_image(url=image_url)

    link = data.get("twitter_link")
    embed.set_author(name=f"Source", url=link)

    return embed

class Ias(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="uma", help="Image interaction command that utilizes [iostpa's](https://api.iostpa.com) API.")
    @commands.has_permissions(embed_links=True)
    async def uma(self, ctx: commands.Context):
        embed = await request_api("uma")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="touhou", help="Image interaction command that utilizes [iostpa's](https://api.iostpa.com) API.")
    @commands.has_permissions(embed_links=True)
    async def touhou(self, ctx: commands.Context):
        embed = await request_api("touhou")
        await ctx.reply(embed=embed, mention_author=False)


class SlashIas(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="uma", description="Posts Umamusume artwork")
    async def slash_uma(self, interaction: nextcord.Interaction):
        embed = await request_api("uma")
        await interaction.send(embed=embed)

    @nextcord.slash_command(name="touhou", description="Posts Touhou artwork")
    async def slash_touhou(self, interaction: nextcord.Interaction):
        embed = await request_api("touhou")
        await interaction.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Ias(bot))
    bot.add_cog(SlashIas(bot))