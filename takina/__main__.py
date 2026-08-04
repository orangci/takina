from discord.ext import commands
import datetime
import discord
import psycopg
import config
import os

start_time = datetime.datetime.now(datetime.UTC)


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()

        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            case_insensitive=True,
            help_command=None,
            owner_ids={961063229168164864, 716306888492318790},
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=True, replied_user=True
            ),
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="the stars"
            ),
        )

        self.db: psycopg.AsyncConnection | None = None

    async def setup_hook(self):
        if not os.getenv("HASDB"):
            raise RuntimeError("No PostgreSQL database configured.")

        self.db = await psycopg.AsyncConnection.connect(config.POSTGRESQL_URI)
        if self.db is None:
            raise RuntimeError("No PostgreSQL database configured.")

        for cog in cogs:
            if cog not in cogs_blacklist:
                try:
                    await self.load_extension(f"cogs.{cog}")
                except Exception as e:
                    print(f"Failed to load {cog}: {e}")


async def get_prefix(self, message: discord.Message):
    prefixes = [".", "takina ", "Takina "]

    if not message.guild:
        return prefixes

    async with self.db.cursor() as cur:
        await cur.execute(
            """
            SELECT prefix
            FROM prefixes
            WHERE guild_id = %s
            """,
            (message.guild.id,),
        )

        row = await cur.fetchone()

    if row:
        return [row[0], "takina ", "Takina "]

    if prefix := os.getenv("PREFIX"):
        return [prefix]

    return prefixes


bot = Bot()

# commands cooldown
cooldown = commands.CooldownMapping.from_cooldown(
    config.COMMANDS_COOLDOWN,  # uses
    5.0,  # per how many seconds
    lambda m: m.author.id,
)


# ignores a command if the user's on cooldown
@bot.check
def global_cooldown(ctx: commands.Context):
    bucket = cooldown.get_bucket(ctx.message)
    if bucket:
        retry_after = bucket.update_rate_limit()
    return retry_after is None


# this will automatically load cogs in from the different subfolders
def load_exts(directory):
    # the folders to NOT load cogs from
    blacklist_subfolders = ["libs"]

    cogs = []
    for root, dirs, files in os.walk(directory):
        if any(blacklisted in root for blacklisted in blacklist_subfolders):
            continue

        for file in files:
            if file.endswith(".py"):
                relative_path = os.path.relpath(os.path.join(root, file), directory)
                cog_name = relative_path[:-3].replace(os.sep, ".")
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
cogs_blacklist = []
cogs = load_exts("cogs") + load_exts("takina/cogs")

if __name__ == "__main__":
    bot.run(os.environ["TOKEN"])
