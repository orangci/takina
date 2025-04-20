# SPDX-License-Identifier: AGPL-3.0-or-later
import nextcord
from nextcord.ext import commands


def is_in_guild():
    def predicate(ctx: commands.Context):
        return ctx.guild and ctx.guild.id == SERVER_ID

    return commands.check(predicate)


# is-a.dev
SUGGESTION_CHANNEL_ID = 1236200920317169695
MAINTAINER_ROLE_ID = 830875873027817484
SERVER_ID = 830872854677422150
COUNTING_CHANNEL_ID = 1006903455916507187
BOOSTER_ROLE_ID = 834807222676619325
POSITION_ROLE_ID = 1295386316464328806  # Role ID to place new roles under
STAFF_ROLE_ID = 1197475623745110109
PR_CHANNEL_ID = 1130858271620726784

# celebrating cirno's power
# SERVER_ID = 1281898369236602903
