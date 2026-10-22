# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyviews, lyhelpers, lymodlog
from discord.ext import commands
from takina import config
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
        self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"
    ) -> None:
        assert ctx.guild is not None
        await lyhelpers.permissions_check(ctx, member, True, True, True)

        confirmation = lyviews.ModerationConfirmationView(
            ctx=ctx, member=member, action="kick", reason=reason
        )
        if not await confirmation.prompt():
            return

        embed = discord.Embed(colour=config.EMBED_COLOUR)

        try:
            dm_embed = discord.Embed(colour=config.EMBED_COLOUR)
            dm_embed.description = f"You were kicked from **{ctx.guild}**. \n\n{config.emojis.NOTE} **Reason**: {reason}"
            await member.send(embed=dm_embed)
        except discord.HTTPException:
            embed.set_footer(text="I was unable to DM the user.")

        await member.kick(reason=f"Kicked by {ctx.author} for: {reason}")

        embed.description = f"{config.emojis.SUCCESS} Successfully kicked **{member.mention}**."
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: {reason}"
        embed.description += f"\n{config.emojis.MODERATOR} **Moderator**: {ctx.author}"

        await confirmation.edit_success(embed)
        await lymodlog.log_action(ctx.guild, "kick", [member], reason, ctx.author)

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
        reason: str = "No reason provided",
    ) -> None:
        assert ctx.guild is not None

        if not members or len(members) < 2:
            raise lyerrors.TakinaError("You must specify at least two members to kick.")

        if len(members) > 10:
            raise lyerrors.TakinaError("You cannot kick more than 10 members at once.")

        for member in members:
            await lyhelpers.permissions_check(ctx, member, True, True, True)

        confirmation = lyviews.ModerationConfirmationView(
            ctx=ctx,
            member=", ".join(member.mention for member in members),
            action="mass kick",
            reason=reason,
        )

        if not await confirmation.prompt():
            return

        failed_dms = 0
        for member in members:
            try:
                dm_embed = discord.Embed(colour=config.EMBED_COLOUR)
                dm_embed.description = f"You were kicked from **{ctx.guild}**.\n\n{config.emojis.NOTE} **Reason**: {reason}"
                await member.send(embed=dm_embed)
            except discord.HTTPException:
                failed_dms += 1

            await member.kick(reason=f"Kicked by {ctx.author} for: {reason}")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Successfully kicked the following {len(members)} members: {', '.join(member.mention for member in members)}."
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: {reason}"
        embed.description += f"\n{config.emojis.MODERATOR} **Moderator**: {ctx.author}"

        if failed_dms:
            embed.set_footer(text=f"I was unable to DM {failed_dms} user(s).")

        await confirmation.edit_success(embed)
        await lymodlog.log_action(
            ctx.guild, "mass kick", list(members), reason, ctx.author, mass_action=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Kick(bot))
