# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyhelpers, lymodlog
from discord.ext import commands
import discord


class Warnings(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(description="Warn a member.", usage="@member spamming in #manga")
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def warn(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: lymodlog.Reason = "No reason provided",
    ) -> None:
        await lyhelpers.permissions_check(ctx, member, True, True, True)
        await lymodlog.moderate(
            ctx, [member], "warn", reason, None, f"You were warned in **{ctx.guild}**."
        )

    @commands.command(
        aliases=["groupwarn"],
        description="Warn multiple members.",
        usage="@member1 @member2 spamming",
    )
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def masswarn(
        self,
        ctx: commands.Context,
        members: commands.Greedy[discord.Member],
        *,
        reason: lymodlog.Reason = "No reason provided",
    ) -> None:
        targets = lymodlog.mass_targets(members, "warn")
        for member in targets:
            await lyhelpers.permissions_check(ctx, member, True, True, True)

        await lymodlog.moderate(
            ctx, targets, "warn", reason, None, f"You were warned in **{ctx.guild}**."
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Warnings(bot))
