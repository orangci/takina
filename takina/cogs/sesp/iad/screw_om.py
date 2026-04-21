# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
import nextcord


class ScrewOm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: nextcord.abc.GuildChannel, after: nextcord.abc.GuildChannel):
        if after.id != 830872854677422153:
            return

        if before.name == after.name:
            return

        async for entry in after.guild.audit_logs(limit=5, action=nextcord.AuditLogAction.channel_update):
            if not entry.target or entry.target.id != after.id:
                continue

            if entry.user.id != 248470317540966443:
                continue

            # revert the name (screw u om)
            await after.edit(name=before.name, reason="Screw you, Om <3")


def setup(bot):
    bot.add_cog(ScrewOm(bot))
