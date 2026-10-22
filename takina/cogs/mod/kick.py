# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyhelpers, lymodlog
from discord.ext import commands
import discord


class Kick(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(
        aliases=["k", "yeet"],
        description="Kick a member from the server.",
        usage="@member get out!!",
    )
    @lychecks.has_permissions(kick_members=True)
    @lychecks.guild_only()
    async def kick(
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
            "kick",
            reason,
            lambda member, audit_reason: member.kick(reason=audit_reason),
            f"You were kicked from **{ctx.guild}**.",
            dm_first=True,
        )

    @commands.command(
        aliases=["groupkick", "massk", "massyeet"],
        description="Kick multiple members from the server.",
        usage="@member1 @member2 all of you get out!!!",
    )
    @lychecks.has_permissions(kick_members=True)
    @lychecks.guild_only()
    async def masskick(
        self,
        ctx: commands.Context,
        members: commands.Greedy[discord.Member],
        *,
        reason: lymodlog.Reason = "No reason provided",
    ) -> None:
        targets = lymodlog.mass_targets(members, "kick")
        for member in targets:
            await lyhelpers.permissions_check(ctx, member, True, True, True)

        await lymodlog.moderate(
            ctx,
            targets,
            "kick",
            reason,
            lambda member, audit_reason: member.kick(reason=audit_reason),
            f"You were kicked from **{ctx.guild}**.",
            dm_first=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Kick(bot))
