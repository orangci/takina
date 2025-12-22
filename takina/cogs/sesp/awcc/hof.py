# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
from ...libs import oclib
from .libs import lib
import nextcord
import config


class AWCC_HOF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def build_hof_embed(self, username: str) -> nextcord.Embed:
        embed = nextcord.Embed(color=config.EMBED_COLOR, description="")
        data = await oclib.request(f"https://anime.jhiday.net/hof/api/user/{username}")
        if not data:
            embed.description = ":x: This user has no data in the Hall of Fame."
            embed.color = config.ERROR_COLOR
        embed.title = username
        embed.url = f"https://anime.jhiday.net/hof/user/{username}"
        embed.description += f"> **MAL Profile**: https://myanimelist.net/profile/{username}"
        embed.description += f"\n> **Turnins**: {str(data.get('turnins'))}"
        embed.description += f"\n> **Total Score**: {str(data.get('totalScore'))}"
        embed.description += f"\n> **Total Rank**: {str(data.get('totalRank'))}"
        embed.description += f"\n> **Validated Score**: {str(data.get('validatedScore'))}"
        embed.description += f"\n> **Validated Rank**: {str(data.get('validatedRank'))}"
        embed.description += f"\n> **HiScore Level**: {str(data.get('hsacLevel'))}"
        embed.description += f"\n> **LoScore Level**: {str(data.get('lsacLevel'))}"
        embed.set_footer(text="Looking for MyAnimeList information or statistics? Try the mal or malstats commands.")
        return embed

    @lib.is_in_guild()
    @commands.command(help="Fetch Hall of Fame information on an AWCC member.", usage="orangc", aliases=["halloffame"])
    async def hof(self, ctx: commands.Context, *, username: str):
        embed = await self.build_hof_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="hof", description="Fetch Hall of Fame information on an AWCC member.", guild_ids=[lib.SERVER_ID])
    async def slash_hof(
        self,
        interaction: nextcord.Interaction,
        *,
        username: str = nextcord.SlashOption(description="The AWCC member MAL username on which to display information", required=True),
    ):
        await interaction.response.defer()
        embed = await self.build_hof_embed(username)
        await interaction.send(embed=embed, ephemeral=False)


def setup(bot):
    bot.add_cog(AWCC_HOF(bot))
