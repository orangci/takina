# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyhelpers, lychecks
from discord.ext import commands
from takina import config
import discord


class PingResponse(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot
        self.stars = 0
        self.forks = 0
        bot.loop.create_task(self.fetch_repo_data())

    async def fetch_repo_data(self) -> None:
        try:
            repo_data = await lyhelpers.request("https://api.github.com/repos/orangci/takina")
            if not repo_data:
                return

            self.stars = repo_data.get("stargazers_count", 0)
            self.forks = repo_data.get("forks_count", 0)
        except Exception:
            return

    async def construct_info_embed(self, ctx: discord.Message) -> discord.Embed:
        embed = discord.Embed(
            title=f"{await lyhelpers.fetch_random_emoji()} Takina",
            url="https://takina.orangc.net",
            colour=config.EMBED_COLOUR,
        )
        embed.description = (
            "-# Open a [bug report](https://git.orangc.net/c/takina/issues/new?template=.forgejo%2fISSUE_TEMPLATE%2fbug_report.md)"
            " • Make a [feature request](https://git.orangc.net/c/takina/issues/new?template=.forgejo%2fISSUE_TEMPLATE%2ffeature_request.md)"
        )
        embed.description += (
            "\n\nTakina is a [open source](https://git.orangc.net/c/takina), multi-purpose"
            " Discord bot written in Python with [discord.py](https://discordpy.readthedocs.io) by [orangc](https://orangc.net)."
            " More information is available on the [website](https://takina.is-a.bot)."
        )

        guild_count = len(self._bot.guilds)
        embed.description += f"\n> **Prefix**: `{'`, `'.join(await self._bot.get_prefix(ctx))}`"
        embed.description += (
            f"\n> **Guilds**: Takina is in {guild_count:,} server{'s' if guild_count != 1 else ''}"
        )
        embed.description += (
            f"\n> **Stars**: [{self.stars:,}](https://github.com/orangci/takina/stargazers)"
        )
        embed.description += f"\n> **Uptime**: {await lyhelpers.uptime_fetcher()}"
        embed.description += f"\n> **Version**: [{config.BOT_VERSION}](https://git.orangc.net/c/takina/src/branch/master/CHANGELOG.md#{config.BOT_VERSION.replace('.', '-')})"

        orangc = await self._bot.fetch_user(961063229168164864)
        embed.set_author(
            name="orangc",
            url="https://orangc.net",
            icon_url=orangc.avatar.url if orangc.avatar else "https://orangc.net/leaf.png",
        )

        return embed

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if not self._bot.user or not self._bot.user.mentioned_in(message):
            return

        if message.guild is None or message.guild.me is None:
            return

        if message.content.strip() != message.guild.me.mention:
            return

        await message.reply(embed=await self.construct_info_embed(message), mention_author=False)

    @commands.hybrid_command(name="info", description="Fetch information about the bot.")
    @lychecks.guild_only()
    async def info(self, ctx: commands.Context) -> None:
        await ctx.reply(embed=await self.construct_info_embed(ctx.message), mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PingResponse(bot))
