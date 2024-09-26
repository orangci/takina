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


class Takina(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def setup_database(self) -> None:
        """Setup MongoDB connection and collections"""
        if not os.getenv("HASDB"):
            raise Exception("No Mongo found. Set the HASDB variable in case you do have a Mongo instance runnin'.")
        self.db_client = AsyncIOMotorClient(os.getenv("MONGO"))
        self.db = self.db_client.get_database("takina")

    @commands.Cog.listener()
    async def on_ready(self):
        """Event triggered when the bot is ready"""
        print(f"{self.user} is now online!")
        await self.setup_database()

bot = Takina(
    intents=nextcord.Intents.all(),
    command_prefix=os.getenv("PREFIX"),
    case_insensitive=True,
    help_command=help_commands.PaginatedHelpCommand(),
    owner_ids=[961063229168164864],
    allowed_mentions=nextcord.AllowedMentions(
        everyone=False, roles=False, users=True, replied_user=True
    ),
    activity=nextcord.Activity(type=nextcord.ActivityType.watching, name="the stars"),
)


def load_exts(directory):
    blacklist_subfolders = []
        
    extensions = []
    for root, dirs, files in os.walk(directory):
        if any(blacklisted in root for blacklisted in blacklist_subfolders):
            continue
        
        for file in files:
            if file.endswith('.py'):
                relative_path = os.path.relpath(os.path.join(root, file), directory)
                extension_name = relative_path[:-3].replace(os.sep, '.')
                extensions.append(extension_name)
    return extensions

extensions_blacklist = []
extensions = load_exts('takina/extensions')

for extension in extensions:
    if extension not in extensions_blacklist:
        try:
            bot.load_extension("extensions." + extension)
        except Exception as e:
            print(f"Failed to load {extension}: {e}")


if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))
