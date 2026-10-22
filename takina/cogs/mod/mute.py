# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers, lymodlog
from discord.ext import commands
from datetime import timedelta
import discord

# discord caps timeouts at 28 days
MAX_TIMEOUT = timedelta(days=28)
MIN_TIMEOUT = timedelta(seconds=30)


def parse_timeout(duration: str) -> timedelta:
    timeout = timedelta(seconds=lyhelpers.duration_calculator(duration))

    if timeout > MAX_TIMEOUT:
        raise lyerrors.TakinaUserInputError(
            "The duration you've specified is too long. The maximum timeout you may set is 28 days."
        )

    if timeout < MIN_TIMEOUT:
        raise lyerrors.TakinaUserInputError("You must specify a minimum duration of 30 seconds.")

    return timeout


class Mute(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(
        aliases=["timeout"],
        description="Timeout a member.",
        usage="@member 12h spamming in #help-forum",
    )
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def mute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: str,
        *,
        reason: lymodlog.Reason = "No reason provided",
    ) -> None:
        timeout = parse_timeout(duration)
        await lyhelpers.permissions_check(ctx, member, True, True, True)

        await lymodlog.moderate(
            ctx,
            [member],
            "mute",
            reason,
            lambda member, audit_reason: member.timeout(timeout, reason=audit_reason),
            f"You were muted in **{ctx.guild}** for {duration}.",
            duration=duration,
        )

    @commands.command(
        aliases=["groupmute"],
        description="Timeout multiple members.",
        usage="@member1 @member2 12h spamming",
    )
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def massmute(
        self,
        ctx: commands.Context,
        members: commands.Greedy[discord.Member],
        duration: str,
        *,
        reason: lymodlog.Reason = "No reason provided",
    ) -> None:
        targets = lymodlog.mass_targets(members, "mute")
        timeout = parse_timeout(duration)
        for member in targets:
            await lyhelpers.permissions_check(ctx, member, True, True, True)

        await lymodlog.moderate(
            ctx,
            targets,
            "mute",
            reason,
            lambda member, audit_reason: member.timeout(timeout, reason=audit_reason),
            f"You were muted in **{ctx.guild}** for {duration}.",
            duration=duration,
        )

    @commands.hybrid_command(
        aliases=["untimeout"],
        description="Remove a timeout from a member.",
        usage="@member we muted you by accident sorry",
    )
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def unmute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: lymodlog.Reason = "No reason provided",
    ) -> None:
        await lyhelpers.permissions_check(ctx, member, True, True, True)
        await lymodlog.moderate(
            ctx,
            [member],
            "unmute",
            reason,
            lambda member, audit_reason: member.timeout(None, reason=audit_reason),
            f"You were unmuted in **{ctx.guild}**.",
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Mute(bot))
