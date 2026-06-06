# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
from ..libs import oclib
import nextcord
import config

class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncMongoClient(host=config.MONGO_URI).get_database(config.DB_NAME)


def setup(bot: commands.Bot):
    bot.add_cog(Settings(bot))