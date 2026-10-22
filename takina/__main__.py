# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina import database, models
from takina.libs import lychecks, lyhelpers
from discord.ext import commands
from pathlib import Path
import discord
import logging
import aiohttp
import os

logger = logging.getLogger("takina.main")


async def get_prefix(bot: commands.Bot, message: discord.Message) -> list[str]:
    default_prefixes = [".", "takina ", "Takina "]

    if message.guild is None:
        return default_prefixes

    prefix = await database.get(models.PrefixModel, guild_id=message.guild.id)
    if prefix is not None:
        return [prefix.prefix, "takina ", "Takina "]

    if env_prefix := os.getenv("PREFIX"):
        return [env_prefix]

    return default_prefixes


class Bot(commands.Bot):
    def __init__(self):
        # https://discordpy.readthedocs.io/en/stable/api.html?highlight=intent#discord.Intents
        intents = discord.Intents(
            guilds=True,
            messages=True,
            moderation=True,
            expressions=True,
            reactions=True,
            typing=True,
            message_content=True,  # this is a privilaged intent!!!
            polls=True,
        )

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
                type=discord.ActivityType.watching, name=os.getenv("BOT_STATUS") or "the stars"
            ),
        )

        # read by lyhelpers.uptime_fetcher; on the bot so .rx reloading lyhelpers keeps it
        self.start_time = discord.utils.utcnow()
        self.http_session: aiohttp.ClientSession | None = None

    async def setup_hook(self):
        await database.initiate_database()

        # for lyhelpers.request() to work
        self.http_session = aiohttp.ClientSession()

        for cog in cogs:
            if cog not in cogs_blacklist:
                try:
                    await self.load_extension(f"takina.cogs.{cog}")
                except commands.ExtensionError:
                    logger.exception(f"failed to load {cog}")

    async def close(self):
        if self.http_session is not None:
            await self.http_session.close()
        await super().close()


bot = Bot()
# our lovely checks
lychecks.setup(bot)
lyhelpers.setup(bot)


# this will automatically load cogs in from the different subfolders
def load_exts(directory: Path) -> list[str]:
    # the folders to NOT load cogs from
    blacklist_subfolders = {
        category.strip()
        for category in os.getenv("COGS_CATEGORY_BLACKLIST", "").split(",")
        if category.strip()
    }
    # essentially, you gotta WHITELIST sesp (server specific) cogs
    # after all, i am the only one who will use them anyway
    if not os.getenv("ENABLE_SESP_COGS"):
        blacklist_subfolders.add("sesp")

    cogs = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [directory for directory in dirs if directory not in blacklist_subfolders]

        for file in files:
            if file.endswith(".py"):
                relative_path = os.path.relpath(os.path.join(root, file), directory)
                cog_name = relative_path[:-3].replace(os.sep, ".")
                cogs.append(cog_name)

    return cogs


# these are required for the bot to function
REQUIRED_ENV_VARS = ["TOKEN", "POSTGRESQL_URI"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    # raise an error if one of the required variables are missing
    raise OSError(f"Missing required environment variables: {', '.join(missing_vars)}.")

# these are *individual* cogs to be blacklisted. e.g. "util.dns"
cogs_blacklist = [cog.strip() for cog in os.getenv("COGS_BLACKLIST", "").split(",") if cog.strip()]
cogs = load_exts(Path(__file__).parent / "cogs")

if __name__ == "__main__":
    # one handler on the root logger, so takina.* logs share discord.py's format.
    # third-party libraries stay at warnings; only discord.py and takina log at info
    discord.utils.setup_logging(level=logging.WARNING, root=True)
    logging.getLogger("discord").setLevel(logging.INFO)
    logging.getLogger("takina").setLevel(logging.INFO)

    bot.run(os.environ["TOKEN"], log_handler=None)
