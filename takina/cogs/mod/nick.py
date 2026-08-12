# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyhelpers, lyerrors
from discord.ext import commands
from takina import config
import discord


class Nick(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(
        aliases=["setnick"],
        description="Change a member's nickname.",
        usage='@member "new nickname"',
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
        assert ctx.guild is not None
        if member is None:
            if not isinstance(ctx.author, discord.Member):
                raise lyerrors.TakinaError("This command can only be used in a server.")
            member = ctx.author

        await lyhelpers.permissions_check(ctx, member, True, True, True)

        if not nickname:
            nickname = member.global_name
        await member.edit(nick=nickname)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} **{member.mention}**'s nickname has been changed to **{nickname}**."
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Nick(bot))
