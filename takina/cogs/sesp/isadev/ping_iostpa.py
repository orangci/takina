# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import nextcord
from nextcord.ext import commands

from .libs import lib


class PingIostpa(commands.Cog):
    @commands.Cog.listener("on_message")
    async def ping_cutedog(self, message: nextcord.Message) -> None:
        if message.guild.id != lib.SERVER_ID:
            return
        if 740117772566265876 in [pong.id for pong in message.mentions]:
            await message.channel.send("<@716306888492318790>, you were pinged on your alt account.")


def setup(bot):
    bot.add_cog(PingIostpa())
