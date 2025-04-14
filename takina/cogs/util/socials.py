import nextcord
from nextcord.ext import commands
from config import *
from ..libs.oclib import *
from github import Github


class SocialsGitHub(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases=["gh"],
        help="Social information command for GitHub. Usage: `github orangci`.",
    )
    async def github(self, ctx: commands.Context, *, username: str):
        embed = await self.fetch_user_information(username)
        await ctx.reply(embed=embed, mention_author=False)
        pass

    @nextcord.slash_command(
        name="github", description="Social information command for GitHub."
    )
    async def slash_github(
        self,
        interaction: nextcord.Interaction,
        *,
        username: str = nextcord.SlashOption(
            description="The GitHub username to fetch information on.", required=True
        ),
    ):
        await interaction.response.defer()
        embed = await self.fetch_user_information(username)
        await interaction.send(embed=embed)

    async def fetch_user_information(self, username):
        embed = nextcord.Embed(color=EMBED_COLOR, description="", title=username)
        github = Github(GITHUB_AUTH_TOKEN)
        try:
            user = github.get_user(username)
        except:
            github.close()
            embed.title = None
            embed.color = ERROR_COLOR
            embed.description = ":x: That GitHub account does not exist."
            return embed

        embed.set_thumbnail(url=user.avatar_url)
        embed.set_footer(text=f"User ID: {user.id}")

        if user.blog:
            if user.blog.startswith("https://"):
                website = user.blog[8:]
            else:
                website = user.blog[7:]

        # fmt: off
        embed.url = user.html_url
        embed.description += f"{user.bio}\n" if user.bio else ""
        embed.description += f"\n**Website**: [{website}]({user.blog})" if user.blog else ""
        embed.description += f"\n**Email**: [{user.email}](mailto:{user.email})" if user.email else ""
        embed.description += f"\n**Location**: {user.location}" if user.location else ""
        embed.description += f"\n**Hireable**: This user is available for hire." if user.hireable else ""
        embed.description += f"\n**Company**: {user.company}" if user.company else ""
        embed.description += f"\n**Followers**: {user.followers}" if user.followers else ""
        embed.description += f"\n**Following**: {user.following}" if user.following else ""
        embed.description += f"\n**Joined GitHub**: <t:{int(user.created_at.timestamp())}:D>" if user.created_at else ""
        embed.description += f"\n**Public Repositories**: {user.public_repos}" if user.public_repos else ""
        embed.description += f"\n**Public Gists**: {user.public_gists}" if user.public_gists else ""
        embed.description += f"\n\nThis user has set their profile as private." if user.user_view_type != "public" else ""
        embed.description += "\n\n**This user is a GitHub site administrator.**" if user.site_admin else ""

        github.close()
        return embed
        # fmt: on


def setup(bot: commands.Bot):
    bot.add_cog(SocialsGitHub(bot))
