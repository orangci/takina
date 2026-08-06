from takina.database import initiate_database
from takina.prefix import get_prefix
from takina.libs import lychecks
from discord.ext import commands
import discord
import os

start_time = discord.utils.utcnow()


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()

        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            case_insensitive=True,
            help_command=None,
            owner_ids={961063229168164864, 716306888492318790},
            # in order: orangc, iostpa
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=True, replied_user=True
            ),
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="the stars"
            ),
        )

    async def setup_hook(self):
        if not os.getenv("HASDB"):
            raise RuntimeError("No PostgreSQL database configured.")

        await initiate_database()

        for cog in cogs:
            if cog not in cogs_blacklist:
                try:
                    await self.load_extension(f"takina.cogs.{cog}")
                except Exception as e:
                    print(f"Failed to load {cog}: {e}")


bot = Bot()
# our lovely checks
lychecks.setup(bot)


# this will automatically load cogs in from the different subfolders
def load_exts(directory):
    # the folders to NOT load cogs from
    blacklist_subfolders = []

    cogs = []
    for root, dirs, files in os.walk(directory):
        if any(blacklisted in root for blacklisted in blacklist_subfolders):
            continue

        for file in files:
            if file.endswith(".py"):
                relative_path = os.path.relpath(os.path.join(root, file), directory)
                cog_name = relative_path[:-3].replace(os.sep, ".")
                print(f"DEBUG: loaded {cog_name}")
                cogs.append(cog_name)
    return cogs


# these are required for the bot to function
REQUIRED_ENV_VARS = ["TOKEN", "HASDB", "POSTGRESQL_URI", "BOT_NAME", "DB_NAME"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    # raise an error if one of the required variables are missing
    raise EnvironmentError(
        f"Missing required environment variables: {', '.join(missing_vars)}."
    )

# these are *individual* cogs to be blacklisted. e.g. "util.dns"
cogs_blacklist = ["core.settings"]
cogs = load_exts("takina/cogs")

if __name__ == "__main__":
    bot.run(os.environ["TOKEN"])
