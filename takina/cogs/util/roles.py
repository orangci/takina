import nextcord
from nextcord.ext import application_checks, commands
from ..libs.oclib import *
from __main__ import EMBED_COLOR


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="role", invoke_without_command=True)
    async def role(self, ctx: commands.Context):
        """Base role command, if no subcommand is passed."""
        embed = nextcord.Embed(
            description="Please specify a subcommand: `add` or `remove`",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @role.command(name="add")
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx: commands.Context, role: nextcord.Role, member: str = None):
        """Adds a role to a member. Usage: `role add role member`."""
        if member is None:
            member = ctx.author
        else:
            member = extract_user_id(member, ctx)

        await member.add_roles(role)
        embed = nextcord.Embed(
            description=f"✅ Added role {role.mention} to {member.mention}.",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @role.command(name="remove")
    @commands.has_permissions(manage_roles=True)
    async def remove(
        self, ctx: commands.Context, role: nextcord.Role, member: str = None
    ):
        """Removes a role from a member. Usage: `role remove role member`."""
        if member is None:
            member = ctx.author
        else:
            member = extract_user_id(member, ctx)

        await member.remove_roles(role)
        embed = nextcord.Embed(
            description=f"✅ Removed role {role.mention} from {member.mention}.",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)


class RolesSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="role", description="Role management commands.")
    async def role(self, interaction: nextcord.Interaction):
        pass

    @role.subcommand(name="add")
    @application_checks.has_permissions(manage_roles=True)
    async def add(
        self,
        interaction: nextcord.Interaction,
        role: nextcord.Role = nextcord.SlashOption(
            description="The role to add", required=True
        ),
        member: nextcord.Member = nextcord.SlashOption(
            description="The member to add the role to", required=True
        ),
    ):
        """Adds a role to a member. Usage: `role add role member`."""

        await member.add_roles(role)
        embed = nextcord.Embed(
            description=f"✅ Added role {role.mention} to {member.mention}.",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed)

    @role.subcommand(name="remove")
    @application_checks.has_permissions(manage_roles=True)
    async def remove(
        self,
        interaction: nextcord.Interaction,
        role: nextcord.Role = nextcord.SlashOption(
            description="The role to remove", required=True
        ),
        member: nextcord.Member = nextcord.SlashOption(
            description="The member to remove the role from", required=True
        ),
    ):
        """Removes a role from a member. Usage: `role remove role member`."""

        await member.remove_roles(role)
        embed = nextcord.Embed(
            description=f"✅ Removed role {role.mention} from {member.mention}.",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(Roles(bot))
    bot.add_cog(RolesSlash(bot))
