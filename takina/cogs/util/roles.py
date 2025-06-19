# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import application_checks, commands
from ..libs import oclib
import nextcord
import config


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(
        name="role",
        aliases=["rank"],
        description="Base role command, if no subcommand is passed.",
        invoke_without_command=True,
        help="Role management. Use subcommands `add` and `remove`.",
    )
    async def role(self, ctx: commands.Context):
        embed = nextcord.Embed(description="Please specify a subcommand: `add` or `remove`", color=config.EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)

    @role.command(name="add", help="Add a role to a member.", usage="Moderator @member")
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx: commands.Context, role: nextcord.Role, member: str = None):
        if member is None:
            member = ctx.author
        else:
            member = oclib.extract_user_id(member, ctx)
            if isinstance(member, nextcord.Embed):
                await ctx.reply(embed=member, mention_author=False)
                return

        await member.add_roles(role, reason=f"Role added by {ctx.author}")
        embed = nextcord.Embed(description=f"✅ Added role {role.mention} to {member.mention}.", color=config.EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)

    @role.command(name="remove", help="Remove a role from member.", usage="Moderator @member")
    @commands.has_permissions(manage_roles=True)
    async def remove(self, ctx: commands.Context, role: nextcord.Role, member: str = None):
        if member is None:
            member = ctx.author
        else:
            member = oclib.extract_user_id(member, ctx)
            if isinstance(member, nextcord.Embed):
                await ctx.reply(embed=member, mention_author=False)
                return

        await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
        embed = nextcord.Embed(description=f"✅ Removed role {role.mention} from {member.mention}.", color=config.EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)


class RolesSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="role", description="Role management commands.")
    async def role(self, interaction: nextcord.Interaction):
        pass

    @role.subcommand(name="add", description="Add a role to a member.")
    @application_checks.has_permissions(manage_roles=True)
    async def add(
        self,
        interaction: nextcord.Interaction,
        role: nextcord.Role = nextcord.SlashOption(description="The role to add", required=True),
        member: nextcord.Member = nextcord.SlashOption(description="The member to add the role to", required=True),
    ):
        await interaction.response.defer()
        await member.add_roles(role, reason=f"Role added by {interaction.user}")
        embed = nextcord.Embed(description=f"✅ Added role {role.mention} to {member.mention}.", color=config.EMBED_COLOR)
        await interaction.send(embed=embed)

    @role.subcommand(name="remove", description="Remove a role from member.")
    @application_checks.has_permissions(manage_roles=True)
    async def remove(
        self,
        interaction: nextcord.Interaction,
        role: nextcord.Role = nextcord.SlashOption(description="The role to remove", required=True),
        member: nextcord.Member = nextcord.SlashOption(description="The member to remove the role from", required=True),
    ):
        await interaction.response.defer()
        await member.remove_roles(role, reason=f"Role removed by {interaction.user}")
        embed = nextcord.Embed(description=f"✅ Removed role {role.mention} from {member.mention}.", color=config.EMBED_COLOR)
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(Roles(bot))
    bot.add_cog(RolesSlash(bot))
