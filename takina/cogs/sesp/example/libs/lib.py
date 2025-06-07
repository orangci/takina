# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands


def is_in_guild():
    def predicate(ctx: commands.Context):
        return ctx.guild and ctx.guild.id == SERVER_ID

    return commands.check(predicate)


SERVER_ID = 1281898369236602903
