from takina.libs import lychecks, lyerrors, lyhelpers
from discord.ext import commands
from takina import config
import discord


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_group(name="role", aliases=["rank"], description="Role management commands.")
    @commands.guild_only()
    async def role(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @role.command(name="add", description="Add a role to a member.", usage="@member Moderator")
    @lychecks.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def add(
        self, ctx: commands.Context, member: discord.Member | None, *, role: discord.Role
    ):
        if member is None:
            if not isinstance(ctx.author, discord.Member):
                raise lyerrors.TakinaError("This command can only be used in a server.")
            member = ctx.author

        if role in member.roles:
            raise lyerrors.TakinaError(f"{member.mention} already has the {role.mention} role.")

        await lyhelpers.permissions_check(ctx, member, False, False, False)
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
    @commands.guild_only()
    async def remove(
        self, ctx: commands.Context, member: discord.Member | None, *, role: discord.Role
    ):
        if member is None:
            if not isinstance(ctx.author, discord.Member):
                raise lyerrors.TakinaError("This command can only be used in a server.")
            member = ctx.author

        if role not in member.roles:
            raise lyerrors.TakinaError(
                f"{member.mention} already didn't have the {role.mention} role."
            )

        await lyhelpers.permissions_check(ctx, member, False, False, False)
        await member.remove_roles(role, reason=f"Role removed by {ctx.author}")

        embed = discord.Embed(
            description=f"{config.emojis.SUCCESS} Removed role {role.mention} from {member.mention}.",
            colour=config.EMBED_COLOUR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @role.command(name="info", description="Fetch information about a role.", usage="Moderator")
    @commands.guild_only()
    async def info(self, ctx: commands.Context, *, role: discord.Role):
        info_cog = self._bot.get_cog("Info")
        if not info_cog:
            return

        await info_cog.roleinfo.callback(ctx, role=role)  # type: ignore


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
