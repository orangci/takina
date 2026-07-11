# Takina Code Standards & Contributing Guidelines
Takina does not currently follow *all* of these standards, but as of now does follow them the vast majority most of the time. These standards exist because I have a terrible memory and want everything to be uniform.

### Before Contributing
First of all, thanks for considering contributing to Takina! I appreciate it. Please make sure that what you're contributing follows Discord's [Terms of Service](https://discord.com/terms). Please follow the standards after this section, and lastly, if it's a new feature, please contact me ([orangc](https://orangc.net)) or in the least open an issue before starting to write code; confirming that I'll approve your idea is better than wasting your time and finding out later that I can't merge your pull request because of x and y. 💖

### AI Contributions
The door is that way. Leave.

### Formatting/Linting & Commits
The `ruff format` and `ruff check` commands should be run pre-commit. If `ruff check` raises any errors, they must be addressed.

Each commit should follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard, for example: `fix(mod.mute): mute command did not check for perms`. The scope should be the cog path; `util.qalc`, `fun.dictionary`, et cetera. Please use [atomic commits](https://en.wikipedia.org/wiki/Atomic_commit#Atomic_commit_convention).

### Embeds
- All embeds must use the config.EMBED_COLOR variable as its color, with the exception of it being an error embed; in which case it should be config.ERROR_COLOR.
- All mentions of a user should generally be user.mention, not user.name or anything else.
- Generally field names should be prefixed with an emoji, preferrably a cute one.

### Categorisation
Only cog categories with names that are not self explanatory are listed here.
- The `libs` folder is for libraries; all functions that might be used over and over again should be put in here, generally placed in `libs.oclib`.
- The `listeners` folder is for listener cogs; ones that are not commands but instead listen for events and respond, like the github or starboard modules.
- The `sesp` folder is for *server specific* cogs, cogs dedicated to a specific Discord server.
- If a cog is not placed in a subfolder, it can be considered a core cog that is vital to the functionality of the bot.

### Responses
For base commands, `ctx.reply(mention_author=False)` should always be used, save for special scenarios.
For slash commands, generally `interaction.send(ephemeral=True)` should be used, except for some places where ephemeral messages shouldn't be ephemeral (e.g. moderation commands).

### Slash Commands
`await interaction.response.defer()` should be used in all complex slash commands.

### Documentation
Every command must have sufficient documentation for help commands. You must also strive to thoroughly comment your code and ensure that it is readable and understandable. You must use readable variable/function names; instead of `for i in x`, do `for user in members`.

### Example cog that hooks into the database
```py
# takina/cogs/fun/hello.py
from nextcord.ext import commands
from ..libs import oclib # various helper functions like fetch_random_emoji() or request() are imported from here
import nextcord
import config # EMBED_COLOR and other variables are imported from here

class Hello(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="hello", aliases=["hi", "hey"], help="Say hello!", usage="<name you wish to have the bot greet>")
    async def hello(self, ctx: commands.Context, name: str):
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed.description = f"{await oclib.fetch_random_emoji()} Hello there {name}!"
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="hello", description="Say hello!")
    async def slash_hello(self, interaction: nextcord.Interaction):
        # await interaction.response.defer() # since this is a very basic command that will respond instantly, we won't defer this 
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        embed.description = f"{await oclib.fetch_random_emoji()} Hello there!"
        await interaction.send(embed=embed) # since this is a command with a very short response, we won't make it ephemeral


def setup(bot: commands.Bot):
    bot.add_cog(Hello(bot))
```

### Submitting A Contribution
You have two options. Firstly, you can request that I create an account for you on my Git instance; email orangc at c@orangc.net, and then fork the repository and make a pull request.

Secondly, you may also email us a patch directly if you don't want to go through the hassle of waiting for orangc to make you an account. To create a patch file:
```fish
git format-patch -1 HEAD
ls *.patch # the file you see is the patch file
```
This creates a patch file in the current directory containing the latest commit. Replace -1 with -2 for the latest *two* commits, ad infinitum. If you have `git send-email` configured, then I will assume you already know how to use it. If you do not, then manually email takina@orangc.net the patch file.