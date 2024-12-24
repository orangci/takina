import nextcord
from nextcord.ext import commands
from config import *
import os
from ..libs.oclib import *


class PingResponse(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.stars = 0
        self.forks = 0
        self.bot.loop.create_task(self.fetch_repo_data())
        self.prefix = os.getenv("PREFIX")

    async def fetch_repo_data(self):
        try:
            repo_data = await request("https://api.github.com/repos/orangci/takina")
            if not repo_data:
                return
            self.stars = repo_data.get("stargazers_count", 0)
            self.forks = repo_data.get("forks_count", 0)
        except Exception as e:
            print(f"Error fetching repository data: {e}")

    async def construct_info_embed(self):
        embed = nextcord.Embed(
            title=f"{await fetch_random_emoji()} Takina",
            url="https://orangc.xyz/takina",
            description="Takina is a multipurpose [opensource](https://github.com/orangci/takina) bot written in Python. More information is available in the [website](https://orangc.xyz/takina).",
            color=EMBED_COLOR,
        )
        embed.add_field(name=":sparkles: Prefix", value=self.prefix, inline=True)
        embed.add_field(name=":star: Stars", value=str(self.stars), inline=True)
        embed.add_field(
            name=":alarm_clock: Uptime", value=await uptime_fetcher(), inline=True
        )
        orangc = await self.bot.fetch_user(961063229168164864)
        embed.set_author(
            name="orangc",
            url="https://orangc.xyz",
            icon_url=orangc.avatar.url
            or "https://cdn.discordapp.com/avatars/961063229168164864/4bfbf378514a9dcc7a619b5ce5e7e57c.webp",
        )
        return embed

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if self.bot.user.mentioned_in(message) and not message.author.bot:
            if message.content.strip() == message.guild.me.mention:
                await message.reply(
                    embed=await construct_info_embed(), mention_author=False
                )

    @commands.command(name="info", help="Information about the bot.")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def info(self, ctx: commands.Context):
        await ctx.reply(embed=await self.construct_info_embed(), mention_author=False)

    @nextcord.slash_command(name="info", description="Information about the bot.")
    async def slash_info(self, interaction: nextcord.Interaction):
        await interaction.send(embed=await self.construct_info_embed(), ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(PingResponse(bot))
