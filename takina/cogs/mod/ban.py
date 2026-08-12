# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyviews, lyhelpers
from takina.cogs.mod.modlog import ModLog
from discord.ext import commands
from takina import config
from typing import cast
import discord


class Ban(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @property
    def modlog(self) -> ModLog:
        modlog = self._bot.get_cog("ModLog")
        return cast(ModLog, modlog)

    @commands.hybrid_command(
        aliases=["b"],
        description="Ban a member from the server.",
        usage="@member posting NSFW repeatedly",
    )
    @lychecks.has_permissions(ban_members=True)
    @lychecks.guild_only()
    async def ban(
        self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"
    ) -> None:
        assert ctx.guild is not None
        await lyhelpers.permissions_check(ctx, member, True, True, True)

        confirmation = lyviews.ModerationConfirmationView(
            ctx=ctx, member=member, action="ban", reason=reason
        )
        if not await confirmation.prompt():
            return

        embed = discord.Embed(colour=config.EMBED_COLOUR)

        try:
            dm_embed = discord.Embed(colour=config.EMBED_COLOUR)
            dm_embed.description = (
                f"You were banned in **{ctx.guild}**. \n\n{config.emojis.NOTE} **Reason**: {reason}"
            )
            await member.send(embed=dm_embed)
        except Exception:
            embed.set_footer(text="I was unable to DM the user.")

        await member.ban(reason=f"Banned by {ctx.author} for: {reason}")

        embed.description = f"{config.emojis.SUCCESS} Successfully banned **{member.mention}**."
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: {reason}"
        embed.description += f"\n{config.emojis.MODERATOR} **Moderator**: {ctx.author}"

        await confirmation.edit_success(embed)
        await self.modlog.log_action(ctx, "ban", member, reason, ctx.author)

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
        reason: str = "No reason provided",
    ) -> None:
        assert ctx.guild is not None

        if not members or len(members) < 2:
            raise lyerrors.TakinaError("You must specify at least two members to ban.")

        if len(members) > 10:
            raise lyerrors.TakinaError("You cannot ban more than 10 members at once.")

        for member in members:
            await lyhelpers.permissions_check(ctx, member, True, True, True)

        confirmation = lyviews.ModerationConfirmationView(
            ctx=ctx,
            member=", ".join(member.mention for member in members),
            action="mass ban",
            reason=reason,
        )

        if not await confirmation.prompt():
            return

        failed_dms = 0
        for member in members:
            try:
                dm_embed = discord.Embed(colour=config.EMBED_COLOUR)
                dm_embed.description = f"You were banned in **{ctx.guild}**.\n\n{config.emojis.NOTE} **Reason**: {reason}"
                await member.send(embed=dm_embed)
            except Exception:
                failed_dms += 1

            await member.ban(reason=f"Banned by {ctx.author} for: {reason}")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Successfully banned the following {len(members)} members: {', '.join(member.mention for member in members)}."
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: {reason}"
        embed.description += f"\n{config.emojis.MODERATOR} **Moderator**: {ctx.author}"

        if failed_dms:
            embed.set_footer(text=f"I was unable to DM {failed_dms} user(s).")

        await confirmation.edit_success(embed)
        await self.modlog.log_action(ctx, "mass ban", list(members), reason, ctx.author)

    @commands.hybrid_command(
        aliases=["hb"],
        description="Ban a user by their Discord account ID, even if they are not in the server.",
        usage="716306888492318790 get banned, baldie!",
    )
    @lychecks.has_permissions(ban_members=True)
    @lychecks.guild_only()
    async def hackban(
        self, ctx: commands.Context, user: int, *, reason: str = "No reason provided"
    ) -> None:
        assert ctx.guild is not None

        try:
            user_obj = await self._bot.fetch_user(user)
        except discord.NotFound:
            raise lyerrors.TakinaNotFoundError("That Discord user could not be found.")

        try:
            await ctx.guild.fetch_ban(user_obj)
        except discord.NotFound:
            pass
        else:
            raise lyerrors.TakinaError(f"**{user_obj}** (`{user_obj.id}`) is already banned.")

        confirmation = lyviews.ModerationConfirmationView(
            ctx=ctx, member=user_obj, action="hackban", reason=reason
        )
        if not await confirmation.prompt():
            return

        await ctx.guild.ban(user_obj, reason=f"Hackbanned by {ctx.author} for: {reason}")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = (
            f"{config.emojis.SUCCESS} Successfully hackbanned **{user_obj}** (`{user_obj.id}`)."
        )
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: {reason}"
        embed.description += f"\n{config.emojis.MODERATOR} **Moderator**: {ctx.author}"

        await confirmation.edit_success(embed)
        await self.modlog.log_action(ctx, "hackban", user_obj, reason, ctx.author)

    @commands.hybrid_command(
        aliases=["pardon"],
        description="Unban a user from the server.",
        usage="716306888492318790 we're sorry for calling you bald",
    )
    @lychecks.has_permissions(ban_members=True)
    @lychecks.guild_only()
    async def unban(
        self, ctx: commands.Context, user: int, *, reason: str = "No reason provided"
    ) -> None:
        assert ctx.guild is not None

        try:
            user_obj = await self._bot.fetch_user(user)
        except discord.NotFound as error:
            raise lyerrors.TakinaNotFoundError("That Discord user could not be found.") from error

        confirmation = lyviews.ModerationConfirmationView(
            ctx=ctx, member=user_obj, action="hackban", reason=reason
        )
        if not await confirmation.prompt():
            return

        try:
            await ctx.guild.unban(user_obj, reason=f"Unbanned by {ctx.author} for: {reason}")
        except discord.NotFound as error:
            raise lyerrors.TakinaNotFoundError(f"**{user_obj}** is not banned.") from error

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Successfully unbanned **{user_obj}**."
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: {reason}"
        embed.description += f"\n{config.emojis.MODERATOR} **Moderator**: {ctx.author}"

        await confirmation.edit_success(embed)
        await self.modlog.log_action(ctx, "unban", user_obj, reason, ctx.author)


async def setup(bot: commands.Bot):
    await bot.add_cog(Ban(bot))
