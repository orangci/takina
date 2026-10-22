# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors
from discord.ext import commands
from datetime import timedelta
from takina import config
import discord

MAX_PURGE = 200
# discord refuses to bulk delete anything older
BULK_DELETE_AGE = timedelta(weeks=2)


class Purge(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(description="Purge/mass delete messages in a channel.", usage="50")
    @lychecks.has_permissions(manage_messages=True)
    @lychecks.guild_only()
    async def purge(self, ctx: commands.Context, amount: commands.Range[int, 1, MAX_PURGE]) -> None:
        channel = ctx.channel
        if not isinstance(channel, discord.TextChannel | discord.Thread | discord.VoiceChannel):
            raise lyerrors.TakinaError("This command can only be used in a text channel or thread.")

        if ctx.interaction is not None:
            await ctx.defer(ephemeral=True)
        else:
            # the command message is not part of the amount
            await ctx.message.delete()

        deleted = await channel.purge(
            limit=amount,
            after=discord.utils.utcnow() - BULK_DELETE_AGE,
            oldest_first=False,
            bulk=True,
        )

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Successfully purged {len(deleted)} messages."

        if ctx.interaction is not None:
            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed, delete_after=2)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Purge(bot))
