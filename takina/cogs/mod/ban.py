# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers, lymodlog
from discord.ext import commands
import discord


def parse_user_id(user: str) -> int:
    # slash integer options are capped at 2^53, far below real snowflakes, so ids arrive as text
    user_id = user.strip().removeprefix("<@").removeprefix("!").removesuffix(">")
    if not user_id.isdigit():
        raise lyerrors.TakinaUserInputError("Please provide a valid Discord user ID.")

    return int(user_id)


class Ban(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @commands.hybrid_command(
        aliases=["b"],
        description="Ban a member from the server.",
        usage="@member posting NSFW repeatedly",
    )
    @lychecks.has_permissions(ban_members=True)
    @lychecks.guild_only()
    async def ban(
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
            "ban",
            reason,
            lambda member, audit_reason: member.ban(reason=audit_reason),
            f"You were banned in **{ctx.guild}**.",
            dm_first=True,
        )

    @commands.command(
        aliases=["groupban", "massb"],
        description="Ban multiple members from the server.",
        usage="@member1 @member2 posting gore",
    )
    @lychecks.has_permissions(ban_members=True)
    @lychecks.guild_only()
    async def massban(
        self,
        ctx: commands.Context,
        members: commands.Greedy[discord.Member],
        *,
        reason: lymodlog.Reason = "No reason provided",
    ) -> None:
        targets = lymodlog.mass_targets(members, "ban")
        for member in targets:
            await lyhelpers.permissions_check(ctx, member, True, True, True)

        await lymodlog.moderate(
            ctx,
            targets,
            "ban",
            reason,
            lambda member, audit_reason: member.ban(reason=audit_reason),
            f"You were banned in **{ctx.guild}**.",
            dm_first=True,
        )

    @commands.hybrid_command(
        aliases=["hb"],
        description="Ban a user by their Discord account ID, even if they are not in the server.",
        usage="716306888492318790 get banned, baldie!",
    )
    @lychecks.has_permissions(ban_members=True)
    @lychecks.guild_only()
    async def hackban(
        self, ctx: commands.Context, user: str, *, reason: lymodlog.Reason = "No reason provided"
    ) -> None:
        assert ctx.guild is not None
        user_id = parse_user_id(user)
        if user_id == ctx.me.id:
            raise lyerrors.TakinaUserInputError("I cannot ban myself.")

        # without the members intent the cache misses most members, so ask discord directly
        member = ctx.guild.get_member(user_id)
        if member is None:
            try:
                member = await ctx.guild.fetch_member(user_id)
            except discord.NotFound:
                member = None

        if member is not None:
            await lyhelpers.permissions_check(ctx, member, True, True, True)

        try:
            user_obj = await self._bot.fetch_user(user_id)
        except discord.NotFound:
            raise lyerrors.TakinaNotFoundError("That Discord user could not be found.")

        try:
            await ctx.guild.fetch_ban(user_obj)
        except discord.NotFound:
            pass
        else:
            raise lyerrors.TakinaError(f"**{user_obj}** (`{user_obj.id}`) is already banned.")

        guild = ctx.guild
        await lymodlog.moderate(
            ctx,
            [user_obj],
            "hackban",
            reason,
            lambda user, audit_reason: guild.ban(user, reason=audit_reason),
            None,
        )

    @commands.hybrid_command(
        aliases=["pardon"],
        description="Unban a user from the server.",
        usage="716306888492318790 we're sorry for calling you bald",
    )
    @lychecks.has_permissions(ban_members=True)
    @lychecks.guild_only()
    async def unban(
        self, ctx: commands.Context, user: str, *, reason: lymodlog.Reason = "No reason provided"
    ) -> None:
        assert ctx.guild is not None
        guild = ctx.guild

        try:
            user_obj = await self._bot.fetch_user(parse_user_id(user))
        except discord.NotFound as error:
            raise lyerrors.TakinaNotFoundError("That Discord user could not be found.") from error

        async def unban_user(user: discord.User, audit_reason: str) -> None:
            try:
                await guild.unban(user, reason=audit_reason)
            except discord.NotFound as error:
                raise lyerrors.TakinaNotFoundError(f"**{user}** is not banned.") from error

        await lymodlog.moderate(ctx, [user_obj], "unban", reason, unban_user, None)


async def setup(bot: commands.Bot):
    await bot.add_cog(Ban(bot))
