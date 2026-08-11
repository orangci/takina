from takina.libs import lychecks, lyerrors, lyviews, lyhelpers
from takina.cogs.mod.modlog import ModLog
from discord.ext import commands
from takina import config
from typing import cast
import discord


class Warnings(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @property
    def modlog(self) -> ModLog:
        modlog = self._bot.get_cog("ModLog")
        return cast(ModLog, modlog)

    @commands.hybrid_command(description="Warn a member.", usage="@member spamming in #manga")
    @lychecks.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def warn(
        self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"
    ) -> None:
        assert ctx.guild is not None
        await lyhelpers.permissions_check(ctx, member, True, True, True)

        confirmation = lyviews.ModerationConfirmationView(
            ctx=ctx, member=member, action="warn", reason=reason
        )

        if not await confirmation.prompt():
            return

        embed = discord.Embed(colour=config.EMBED_COLOUR)

        try:
            dm_embed = discord.Embed(colour=config.EMBED_COLOUR)
            dm_embed.description = (
                f"You were warned in **{ctx.guild}**.\n\n{config.emojis.NOTE} **Reason**: {reason}"
            )
            await member.send(embed=dm_embed)
        except Exception:
            embed.set_footer(text="I was unable to DM the user.")

        embed.description = f"{config.emojis.SUCCESS} Successfully warned **{member.mention}**."
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: {reason}"
        embed.description += f"\n{config.emojis.MODERATOR} **Moderator**: {ctx.author}"

        await confirmation.edit_success(embed)
        await self.modlog.log_action(ctx, "warn", member, reason, ctx.author)

    @commands.command(
        aliases=["groupwarn"],
        description="Warn multiple members.",
        usage="@member1 @member2 spamming",
    )
    @lychecks.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def masswarn(
        self,
        ctx: commands.Context,
        members: commands.Greedy[discord.Member],
        *,
        reason: str = "No reason provided",
    ) -> None:
        assert ctx.guild is not None

        if not members or len(members) < 2:
            raise lyerrors.TakinaError("You must specify at least two members to warn.")

        if len(members) > 10:
            raise lyerrors.TakinaError("You cannot warn more than 10 members at once.")

        for member in members:
            await lyhelpers.permissions_check(ctx, member, True, True, True)

        confirmation = lyviews.ModerationConfirmationView(
            ctx=ctx,
            member=", ".join(member.mention for member in members),
            action="mass warn",
            reason=reason,
        )

        if not await confirmation.prompt():
            return

        embed = discord.Embed(colour=config.EMBED_COLOUR)

        failed_dms = 0
        for member in members:
            try:
                dm_embed = discord.Embed(colour=config.EMBED_COLOUR)
                dm_embed.description = f"You were warned in **{ctx.guild}**.\n\n{config.emojis.NOTE} **Reason**: {reason}"
                await member.send(embed=dm_embed)
            except Exception:
                failed_dms += 1

        embed.description = f"{config.emojis.SUCCESS} Successfully warned the following {len(members)} members: {', '.join(member.mention for member in members)}."
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: {reason}"
        embed.description += f"\n{config.emojis.MODERATOR} **Moderator**: {ctx.author}"

        if failed_dms:
            embed.set_footer(text=f"I was unable to DM {failed_dms} user(s).")

        await confirmation.edit_success(embed)
        await self.modlog.log_action(ctx, "mass warn", list(members), reason, ctx.author)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Warnings(bot))
