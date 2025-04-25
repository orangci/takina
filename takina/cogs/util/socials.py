# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import asyncpraw
import nextcord
import config
from github import Github
from nextcord.ext import commands


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
        username = username[1:] if username.startswith("@") else username
        embed = nextcord.Embed(color=config.EMBED_COLOR, description="", title=username)
        github = Github(config.GITHUB_AUTH_TOKEN)
        try:
            user = github.get_user(username)
        except Exception:
            github.close()
            embed.title = None
            embed.color = config.ERROR_COLOR
            embed.description = ":x: That GitHub account does not exist."
            return embed

        embed.set_thumbnail(url=user.avatar_url)
        embed.set_footer(text=f"User ID: {user.id}")

        if user.blog:
            if user.blog.startswith("https://"):
                website = user.blog[8:]
            else:
                website = user.blog[7:]

        embed.url = user.html_url
        embed.description += f"{user.bio}\n" if user.bio else ""
        embed.description += (
            f"\n**Website**: [{website}]({user.blog})" if user.blog else ""
        )
        embed.description += (
            f"\n**Email**: [{user.email}](mailto:{user.email})" if user.email else ""
        )
        embed.description += f"\n**Location**: {user.location}" if user.location else ""
        embed.description += (
            "\n**Hireable**: This user is available for hire." if user.hireable else ""
        )
        embed.description += f"\n**Company**: {user.company}" if user.company else ""
        embed.description += (
            f"\n**Followers**: {user.followers}" if user.followers else ""
        )
        embed.description += (
            f"\n**Following**: {user.following}" if user.following else ""
        )
        embed.description += (
            f"\n**Joined GitHub**: <t:{int(user.created_at.timestamp())}:D>"
            if user.created_at
            else ""
        )
        embed.description += (
            f"\n**Public Repositories**: {user.public_repos}"
            if user.public_repos
            else ""
        )
        embed.description += (
            f"\n**Public Gists**: {user.public_gists}" if user.public_gists else ""
        )
        embed.description += (
            "\n\nThis user has set their profile as private."
            if user.user_view_type != "public"
            else ""
        )
        embed.description += (
            "\n\n**This user is a GitHub site administrator.**"
            if user.site_admin
            else ""
        )

        github.close()
        return embed


class SocialsReddit(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        help="Social information command for Reddit. Usage: `reddit orangci`.",
    )
    async def reddit(self, ctx: commands.Context, *, username: str):
        embed = await self.fetch_user_information(username)
        await ctx.reply(embed=embed, mention_author=False)
        pass

    @nextcord.slash_command(
        name="reddit", description="Social information command for Reddit."
    )
    async def slash_reddit(
        self,
        interaction: nextcord.Interaction,
        *,
        username: str = nextcord.SlashOption(
            description="The Reddit username to fetch information on.",
            required=True,
        ),
    ):
        await interaction.response.defer()
        embed = await self.fetch_user_information(username)
        await interaction.send(embed=embed)

    async def fetch_user_information(self, username):
        username = username[3:] if username.startswith("/u/") else username
        username = username[2:] if username.startswith("u/") else username

        reddit = asyncpraw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            user_agent=config.BOT_NAME,
        )

        embed = nextcord.Embed(color=0xFF4500, description="")

        try:
            user = await reddit.redditor(username)
            await user.load()
        except Exception:
            embed.color = config.ERROR_COLOR
            embed.description = ":x: That Reddit account does not exist."
            return embed

        embed.set_thumbnail(url=user.icon_img)
        embed.title = f"u/{user.name}"
        embed.description += (
            f"{user.subreddit.public_description}\n"
            if user.subreddit.public_description
            else ""
        )
        embed.description += f"\n**Joined Reddit**: <t:{int(user.created_utc)}:D>"
        embed.description += f"\n**Post Karma**: {user.link_karma}"
        embed.description += f"\n**Comment Karma**: {user.comment_karma}"
        embed.description += f"\n**Total Posts**: {user.link_karma}"
        embed.description += f"\n**Total Comments**: {user.comment_karma}"
        moderated_subreddits = await user.moderated()
        moderated_subreddit_names = [
            f"r/{sub.display_name}" for sub in moderated_subreddits
        ]
        embed.description += (
            f"\n**Moderator in**: {', '.join(moderated_subreddit_names)}"
            if moderated_subreddit_names
            else ""
        )
        return embed


def setup(bot: commands.Bot):
    if config.GITHUB_AUTH_TOKEN:
        bot.add_cog(SocialsGitHub(bot))
    else:
        print(
            "You must set the config.GITHUB_AUTH_TOKEN environment variable if you want the github command to work. Skipping loading the github command. \nTo get your own github auth token, visit <https://github.com/settings/tokens/new>."
        )
    if config.REDDIT_CLIENT_ID and config.REDDIT_CLIENT_SECRET:
        bot.add_cog(SocialsReddit(bot))
    else:
        print(
            "You must set the config.REDDIT_CLIENT_ID and config.REDDIT_CLIENT_SECRET environment variables if you would like the reddit command to work. Skipping loading the reddit command. \nTo get your own Reddit application visit <https://www.reddit.com/prefs/apps>."
        )
