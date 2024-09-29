from __future__ import annotations
import os
import threading
import nextcord
from nextcord.ext import commands, help_commands, tasks
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from aiohttp import web

load_dotenv()

BOT_NAME = os.getenv("BOT_NAME")
DB_NAME = os.getenv("DB_NAME").lower()
EMBED_COLOR_STR = os.getenv("EMBED_COLOR", "#000000")

if EMBED_COLOR_STR.startswith("#"):
    EMBED_COLOR = int(EMBED_COLOR_STR[1:], 16)  # Remove "#" and convert hex to int
elif EMBED_COLOR_STR.startswith("0x"):
    EMBED_COLOR = int(EMBED_COLOR_STR, 16)  # Directly convert hex to int
else:
    EMBED_COLOR = int(EMBED_COLOR_STR)  # Handle cases where it might be directly an int


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def setup_database(self) -> None:
        """Setup MongoDB connection and collections"""
        if not os.getenv("HASDB"):
            raise Exception("No Mongo found. Set the HASDB variable in case you do have a Mongo instance runnin'.")
        self.db_client = AsyncIOMotorClient(os.getenv("MONGO"))
        self.db = self.db_client.get_database(DB_NAME)

    @commands.Cog.listener()
    async def on_ready(self):
        """Event triggered when the bot is ready"""
        print(f"{self.user} is now online!")
        await self.setup_database()

bot = Bot(
    intents=nextcord.Intents.all(),
    command_prefix=os.getenv("PREFIX"),
    case_insensitive=True,
    help_command=help_commands.PaginatedHelpCommand(),
    owner_ids=[961063229168164864, 716306888492318790],
    allowed_mentions=nextcord.AllowedMentions(
        everyone=False, roles=False, users=True, replied_user=True
    ),
    activity=nextcord.Activity(type=nextcord.ActivityType.watching, name="the stars"),
)


def load_exts(directory):
    blacklist_subfolders = ["libs"]
        
    cogs = []
    for root, dirs, files in os.walk(directory):
        if any(blacklisted in root for blacklisted in blacklist_subfolders):
            continue
        
        for file in files:
            if file.endswith('.py'):
                relative_path = os.path.relpath(os.path.join(root, file), directory)
                cog_name = relative_path[:-3].replace(os.sep, '.')
                cogs.append(cog_name)
    return cogs

cogs_blacklist = []
cogs = load_exts('takina/cogs')

for cog in cogs:
    if cog not in cogs_blacklist:
        try:
            bot.load_extension("cogs." + cog)
        except Exception as e:
            print(f"Failed to load {cog}: {e}")


if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))
