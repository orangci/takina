# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from discord.ext import commands
from takina import config
import discord


def check_assignable(ctx: commands.Context, member: discord.Member, role: discord.Role) -> None:
    assert ctx.guild is not None and isinstance(ctx.author, discord.Member)

    if role.is_default() or role.managed:
        raise lyerrors.TakinaUserInputError(
            f"{role.mention} is managed by Discord or an integration, so it cannot be given out."
        )

    # without this, manage roles alone would let anyone hand out roles above their own
    if ctx.author != ctx.guild.owner and role >= ctx.author.top_role:
        raise lyerrors.TakinaPermissionError(
            f"You cannot manage {role.mention}, as it is higher than or equal to your top role."
        )

    if (
        ctx.author != ctx.guild.owner
        and member != ctx.author
        and member.top_role >= ctx.author.top_role
    ):
        raise lyerrors.TakinaPermissionError(
            f"You cannot manage the roles of {member.mention}, who is higher than or equal to you."
        )

    if role >= ctx.guild.me.top_role:
        raise lyerrors.TakinaBotPermissionError(
            f"I cannot manage {role.mention}, as it is higher than or equal to my top role."
        )


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_group(name="role", aliases=["rank"], description="Role management commands.")
    @lychecks.guild_only()
    async def role(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @role.command(name="add", description="Add a role to a member.", usage="@member Moderator")
    @lychecks.has_permissions(manage_roles=True)
    @lychecks.guild_only()
    async def add(
        self, ctx: commands.Context, member: discord.Member | None = None, *, role: discord.Role
    ):
        assert isinstance(ctx.author, discord.Member)
        member = member or ctx.author
        check_assignable(ctx, member, role)

        if role in member.roles:
            raise lyerrors.TakinaError(f"{member.mention} already has the {role.mention} role.")

        await member.add_roles(role, reason=f"Role added by {ctx.author}")

        embed = discord.Embed(
            description=f"{config.emojis.SUCCESS} Added role {role.mention} to {member.mention}.",
            colour=config.EMBED_COLOUR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @role.command(
        name="remove", description="Remove a role from member.", usage="@member Moderator"
    )
    @lychecks.has_permissions(manage_roles=True)
    @lychecks.guild_only()
    async def remove(
        self, ctx: commands.Context, member: discord.Member | None = None, *, role: discord.Role
    ):
        assert isinstance(ctx.author, discord.Member)
        member = member or ctx.author
        check_assignable(ctx, member, role)

        if role not in member.roles:
            raise lyerrors.TakinaError(
                f"Nothing was removed, as {member.mention} did not have the {role.mention} role."
            )

        await member.remove_roles(role, reason=f"Role removed by {ctx.author}")

        embed = discord.Embed(
            description=f"{config.emojis.SUCCESS} Removed role {role.mention} from {member.mention}.",
            colour=config.EMBED_COLOUR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @role.command(name="info", description="Fetch information about a role.", usage="Moderator")
    @lychecks.guild_only()
    async def info(self, ctx: commands.Context, *, role: discord.Role):
        await lyhelpers.invoke_moved(ctx, "roleinfo", role=role)


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
