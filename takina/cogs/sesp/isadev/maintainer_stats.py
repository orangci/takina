import nextcord
from nextcord.ext import commands
from config import *
from .libs.lib import *
from ...libs.oclib import *
from github import Github, Auth


async def build_maintainer_stats_embed(username) -> nextcord.Embed:
    embed = nextcord.Embed(description="")
    maintainer_name = None
    maintainers = {
        961063229168164864: "orangci",
        716306888492318790: "iostpa",
        757296951925538856: "DEV-DIBSTER",
        1350435011509223464: "21Z",
        882595027132493864: "SX-9",
        694986201739952229: "Stef-00012",
        853158265466257448: "wdhdev",
    }

    if isinstance(username, nextcord.User) and username.id in maintainers:
        maintainer_name = maintainers[username.id]
    elif username in maintainers.values():
        maintainer_name = username
    else:
        embed.color = ERROR_COLOR
        embed.description = ":x: The specified user is not an is-a.dev maintainer."
        return embed

    github = Github(auth=Auth.Token(GITHUB_AUTH_TOKEN))
    repo = github.get_repo("is-a-dev/register")
    contributors = repo.get_contributors()

    contributors_list = [(contributor.login, contributor.contributions) for contributor in contributors]
    contributors_list.sort(key=lambda x: x[1], reverse=True)
    commits = 0
    maintainer_rank = None

    for rank, (login, count) in enumerate(contributors_list, start=1):
        if login == maintainer_name:
            commits = count
            maintainer_rank = rank
            break

    embed.color = EMBED_COLOR
    embed.description = f"> **Maintainer:** {maintainer_name}\n"
    embed.description += f"> **Commits:** {commits}\n"
    embed.description += f"> **Rank:** #{maintainer_rank if maintainer_rank else 'N/A'}\n"
    github.close()
    return embed


class MaintainerStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases=["mstats"],
        help="Fetch an is-a.dev maintainer's statistics. \nUsage: `mstats orangc`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    @is_in_guild()
    async def maintainer_stats(
        self, ctx: commands.Context, maintainer: nextcord.User | str
    ):
        embed = await build_maintainer_stats_embed(maintainer)
        await ctx.reply(embed=embed, mention_author=False)


class SlashMaintainerStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(
        name="maintainer_stats",
        guild_ids=[SERVER_ID],
        description="Fetch an is-a.dev maintainer's statistics.",
    )
    async def maintainer_stats(
        self, interaction: nextcord.Interaction, maintainer: nextcord.Member
    ):
        await interaction.response.defer()
        embed = await build_maintainer_stats_embed(maintainer)
        await interaction.send(embed=embed)


def setup(bot: commands.Bot):
    if GITHUB_AUTH_TOKEN:
        bot.add_cog(MaintainerStats(bot))
        bot.add_cog(SlashMaintainerStats(bot))
    else:
        print(
            "You have not set a GitHub authentication token in the environment variables. If you would like the sesp.isadev.maintainer_stats cog to be loaded, please set that environment variable; otherwise, ignore this message."
        )
