# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from discord.ext import commands
from takina import config
from typing import cast
import discord

# discord's limit for nicknames
MAX_NICKNAME_LENGTH = 32


class Nick(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(
        aliases=["setnick"],
        description="Change a member's nickname, or reset it if no nickname is given.",
        usage="@member Marisa the Ordinary",
    )
    @lychecks.has_permissions(manage_nicknames=True)
    @lychecks.guild_only()
    async def nick(
        self,
        ctx: commands.Context,
        member: discord.Member | None = None,
        *,
        nickname: str | None = None,
    ) -> None:
        # Range does not survive the | None on slash commands, hence the manual check
        if nickname is not None and len(nickname) > MAX_NICKNAME_LENGTH:
            raise lyerrors.TakinaUserInputError(
                f"Nicknames can be at most {MAX_NICKNAME_LENGTH} characters long."
            )

        member = member or cast(discord.Member, ctx.author)

        # your top role never outranks itself, so only compare roles for someone else
        await lyhelpers.permissions_check(ctx, member, False, True, member != ctx.author)
        await member.edit(nick=nickname)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        if nickname is None:
            embed.description = (
                f"{config.emojis.SUCCESS} {member.mention}'s nickname has been reset."
            )
        else:
            embed.description = f"{config.emojis.SUCCESS} {member.mention}'s nickname has been changed to **{nickname}**."

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Nick(bot))
