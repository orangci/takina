# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors
from discord.ext import commands
from datetime import timedelta
from takina import config
import discord


class Purge(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(description="Purge/mass delete messages in a channel.")
    @lychecks.has_permissions(manage_messages=True)
    @lychecks.guild_only()
    async def purge(self, ctx: commands.Context, amount: int) -> None:
        if amount <= 0 or amount > 200:
            raise lyerrors.TakinaUserInputError("Please specify a number between 1 and 200.")

        assert ctx.channel is not None
        if not isinstance(ctx.channel, discord.TextChannel):
            raise lyerrors.TakinaError("This command can only be used in a text channel.")

        deleted = await ctx.channel.purge(
            limit=amount + 1,
            check=lambda message: message.created_at > discord.utils.utcnow() - timedelta(weeks=2),
            bulk=True,
        )

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = (
            f"{config.emojis.SUCCESS} Successfully purged {len(deleted) - 1} messages."
        )

        await ctx.send(embed=embed, delete_after=2)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Purge(bot))
