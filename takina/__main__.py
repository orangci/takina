from __future__ import annotations
import os
import threading
from os import environ
import nextcord
from nextcord.ext import commands, help_commands, tasks
from nextcord.ext import application_checks as ac
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from aiohttp import web
from web import app

load_dotenv()

def run_flask():
    app.run(host="0.0.0.0", port=5000)


class Bot(commands.Bot):
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

bot = Bot(
    intents=nextcord.Intents.all(),
    command_prefix=os.getenv("PREFIX"),
    case_insensitive=True,
    help_command=help_commands.PaginatedHelpCommand(),
    owner_ids=[961063229168164864],
    allowed_mentions=nextcord.AllowedMentions(
        everyone=False, roles=False, users=True, replied_user=True
    ),
    activity=nextcord.Activity(type=nextcord.ActivityType.watching, name="MyAnimeList"),
)

extensions = [
    "errors",
    "onami",
    "extensions.antiphishing",
    "extensions.owner-utils",
    "extensions.utils",
    "extensions.starboard",
    "extensions.mal_profiles",
    "extensions.anime",
    "extensions.manga",
    "extensions.mal_linking_system",
    "extensions.info",
    "extensions.moderation",
    "extensions.moderation_slash",
    "extensions.roles",
    "extensions.seasonals",
    "extensions.character",
]

for extension in extensions:
    bot.load_extension(extension)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    bot.run(environ["TOKEN"])
