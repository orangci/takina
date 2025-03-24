# Takina Code Standards & Contributing Guidelines
Takina does not currently follow *all* of these standards, but as of now does follow the vast majority most of the time. These standards exist because I have a terrible memory and want everything to be uniform.

### Before Contributing
First of all, thanks for considering contributing to Takina! I appreciate it. Please make sure that what you're contributing follows Discord's [Terms of Service](https://discord.com/terms). Please follow the standards after this section, and lastly, if it's a new feature, please contact me ([orangc](https://orangc.net)) or in the least open an issue before starting to write code; confirming that I'll approve your idea is better than wasting your time and finding out later that I can't merge your pull request because of x and y. 💖

### Formatting & Commits
- `black **/*.py` should be run in the `takina` folder before every commit.
- Each commit should follow the Conventional Commits standard, for example: `fix(mod): mute command did not check for perms`. The scope should be the subfolder affected in the cogs dir, and if there is none, use (core) as a scope.
- Every command should have a description and help information.

### Embeds
- all embeds must use the EMBED_COLOR env var as it's color, with the exception of it being an error embed; in which case it should be 0xFF0037
- all mentions of a user should generally be user.mention, not user.name or anything else
- generally field names should be prefixed with an emoji, preferrably a cute one

### Categorization
- the `fun` folder is for fun related commands and cogs
- the `libs` folder is for libraries; all functions that might be used over and over again should be put in here, generally placed in libs/oclib.py
- the `listeners` folder is for listener cogs; ones that are not commands but instead listen for events and respond, like the github or starboard modules
- the `mod` folder is for moderation related commands and cogs
- the `util` folder is for utility related commands and cogs
- the `weebism` folder is for anime/manga related commands and cogs
- the `sesp` folder is for *server specific* cogs, cogs dedicated to a specific Discord server (such as the subdomain utility commands for the [is-a.dev](https://is-a.dev) Discord server.)
- if a cog is not palced in a subfolder, it can be considered a core cog, vital to the functionality of bot

### Responses
For base commands, `ctx.reply(mention_author=False)` should always be used, save for special scenarios.
For slash commands, generally `interaction.send(ephemeral=True)` should be used, except for some places where ephemeral messages shouldn't be ephemeral (e.g. moderation commands.)

### Slash Commands
`await interaction.response.defer()` should be used in all complex slash commands.

### Cooldowns
Generally commands should have at least a one second cooldown.
`@commands.cooldown(1, 1, commands.BucketType.user)`

### Documentation
Every command must have sufficient documentation for help commands.

### Example cog
```py
# takina/cogs/fun/hello.py
import nextcord
from nextcord.ext import commands
from config import * # EMBED_COLOR and other variables are imported from here
from ..libs.oclib import * # various helper functions like fetch_random_emoji() or request() are imported from here

class Hello(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="hello", aliases=["hi", "hey"], help="Say hello! \nUsage: `hello`.")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def hello(self, ctx: commands.Context):
        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = f"{await fetch_random_emoji()} Hello there!"
        await ctx.reply(embed=embed, mention_author=False)

class SlashHello(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="hello", description="Say hello!")
    async def slash_hello(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = f"{await fetch_random_emoji()} Hello there!"
        await interaction.send(embed=embed) # since this is a command with a very short response, we won't make it ephemeral


def setup(bot: commands.Bot):
    bot.add_cog(Hello(bot))
    bot.add_cog(SlashHello(bot))
```