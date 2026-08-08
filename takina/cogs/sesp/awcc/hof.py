from takina.libs import lyerrors, lychecks, lyhelpers
from discord.ext import commands
from takina import config
import discord


class AWCC_HOF(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @lychecks.sesp_guild_only(275341388554698753)
    @commands.hybrid_command(
        description="Fetch Hall of Fame information on an AWCC member.",
        usage="orangc",
        aliases=["awcc", "mrcc"],
    )
    async def hof(self, ctx: commands.Context, *, username: str):
        embed = discord.Embed(color=config.EMBED_COLOR)
        data = await lyhelpers.request(f"https://anime.jhiday.net/hof/api/user/{username}")
        if not data:
            raise lyerrors.TakinaNotFoundError(
                "This username has no data in the AWCC/MRCC Hall of Fame."
            )

        embed.title = username
        embed.url = f"https://anime.jhiday.net/hof/user/{username}"
        embed.description = f"> **MAL Profile**: https://myanimelist.net/profile/{username}"
        embed.description += f"\n> **Turnins**: {str(data.get('turnins'))}"
        embed.description += f"\n> **Total Score**: {str(data.get('totalScore'))}"
        embed.description += f"\n> **Total Rank**: {str(data.get('totalRank'))}"
        embed.description += f"\n> **Validated Score**: {str(data.get('validatedScore'))}"
        embed.description += f"\n> **Validated Rank**: {str(data.get('validatedRank'))}"
        embed.description += f"\n> **HiScore Level**: {str(data.get('hsacLevel'))}"
        embed.description += f"\n> **LoScore Level**: {str(data.get('lsacLevel'))}"
        embed.set_footer(
            text="Looking for MyAnimeList information or statistics? Try the mal or malstats commands."
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(AWCC_HOF(bot))
