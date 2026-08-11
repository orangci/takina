from takina.libs import lychecks, lyerrors, lyviews, lyhelpers
from takina.cogs.mod.modlog import ModLog
from discord.ext import commands
from datetime import timedelta
from takina import config
from typing import cast
import discord


class Mute(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @property
    def modlog(self) -> ModLog:
        modlog = self._bot.get_cog("ModLog")
        return cast(ModLog, modlog)

    @commands.hybrid_command(
        aliases=["timeout"],
        description="Timeout a member.",
        usage="@member 12h spamming in #help-forum",
    )
    @lychecks.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def mute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: str,
        *,
        reason: str = "No reason provided",
    ) -> None:
        assert ctx.guild is not None
        duration_parsed = lyhelpers.duration_calculator(duration, timeout=True)

        if duration_parsed > 2419200:
            raise lyerrors.TakinaUserInputError(
                "The duration you've specified is too long. The maximum timeout you may set is 28 days."
            )
        elif duration_parsed < 30:
            raise lyerrors.TakinaUserInputError(
                "You must specify a minimum duration of 30 seconds."
            )

        await lyhelpers.permissions_check(ctx, member, True, True, True)

        confirmation = lyviews.ModerationConfirmationView(
            ctx=ctx, member=member, action="mute", reason=reason
        )
        if not await confirmation.prompt():
            return

        embed = discord.Embed(colour=config.EMBED_COLOUR)

        try:
            dm_embed = discord.Embed(colour=config.EMBED_COLOUR)
            dm_embed.description = f"You were muted in **{ctx.guild}** for {duration}.\n\n{config.emojis.NOTE} **Reason**: {reason}"
            await member.send(embed=dm_embed)
        except Exception:
            embed.set_footer(text="I was unable to DM the user.")

        await member.timeout(
            timedelta(seconds=duration_parsed), reason=f"Muted by {ctx.author} for: {reason}"
        )

        embed.description = (
            f"{config.emojis.SUCCESS} Successfully muted **{member.mention}** for {duration}."
        )
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: {reason}"
        embed.description += f"\n{config.emojis.MODERATOR} **Moderator**: {ctx.author}"

        await confirmation.edit_success(embed)
        await self.modlog.log_action(ctx, "mute", member, reason, ctx.author, duration)

    @commands.command(
        aliases=["groupmute"],
        description="Timeout multiple members.",
        usage="@member1 @member2 12h spamming",
    )
    @lychecks.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def massmute(
        self,
        ctx: commands.Context,
        members: commands.Greedy[discord.Member],
        duration: str,
        *,
        reason: str = "No reason provided",
    ) -> None:
        assert ctx.guild is not None

        if not members or len(members) < 2:
            raise lyerrors.TakinaError("You must specify at least two members to mute.")

        if len(members) > 10:
            raise lyerrors.TakinaError("You cannot mute more than 10 members at once.")

        duration_parsed = lyhelpers.duration_calculator(duration, timeout=True)
        if duration_parsed > 2419200:
            raise lyerrors.TakinaUserInputError(
                "The duration you've specified is too long. The maximum timeout you may set is 28 days."
            )
        elif duration_parsed < 30:
            raise lyerrors.TakinaUserInputError(
                "You must specify a minimum duration of 30 seconds."
            )

        for member in members:
            await lyhelpers.permissions_check(ctx, member, True, True, True)

        confirmation = lyviews.ModerationConfirmationView(
            ctx=ctx,
            member=", ".join(member.mention for member in members),
            action="mass mute",
            reason=reason,
        )

        if not await confirmation.prompt():
            return

        failed_dms = 0
        for member in members:
            try:
                dm_embed = discord.Embed(colour=config.EMBED_COLOUR)
                dm_embed.description = f"You were muted in **{ctx.guild}** for {duration}.\n\n{config.emojis.NOTE} **Reason**: {reason}"
                await member.send(embed=dm_embed)
            except Exception:
                failed_dms += 1

            await member.timeout(
                timedelta(seconds=duration_parsed), reason=f"Muted by {ctx.author} for: {reason}"
            )

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Successfully muted the following {len(members)} members for {duration}: {', '.join(member.mention for member in members)}."
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: {reason}"
        embed.description += f"\n{config.emojis.MODERATOR} **Moderator**: {ctx.author}"

        if failed_dms:
            embed.set_footer(text=f"I was unable to DM {failed_dms} user(s).")

        await confirmation.edit_success(embed)
        await self.modlog.log_action(ctx, "mass mute", list(members), reason, ctx.author, duration)

    @commands.hybrid_command(
        aliases=["untimeout"],
        description="Remove a timeout from a member.",
        usage="@member we muted you by accident sorry",
    )
    @lychecks.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def unmute(
        self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"
    ) -> None:
        assert ctx.guild is not None
        await lyhelpers.permissions_check(ctx, member, True, True, True)

        confirmation = lyviews.ModerationConfirmationView(
            ctx=ctx, member=member, action="unmute", reason=reason
        )

        if not await confirmation.prompt():
            return

        embed = discord.Embed(colour=config.EMBED_COLOUR)

        try:
            dm_embed = discord.Embed(colour=config.EMBED_COLOUR)
            dm_embed.description = (
                f"You were unmuted in **{ctx.guild}**.\n\n{config.emojis.NOTE} **Reason**: {reason}"
            )
            await member.send(embed=dm_embed)
        except Exception:
            embed.set_footer(text="I was unable to DM the user.")

        await member.timeout(None, reason=f"Unmuted by {ctx.author} for: {reason}")

        embed.description = f"{config.emojis.SUCCESS} Successfully unmuted **{member.mention}**."
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: {reason}"
        embed.description += f"\n{config.emojis.MODERATOR} **Moderator**: {ctx.author}"

        await confirmation.edit_success(embed)
        await self.modlog.log_action(ctx, "unmute", member, reason, ctx.author)


async def setup(bot: commands.Bot):
    await bot.add_cog(Mute(bot))
