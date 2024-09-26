import nextcord
from nextcord.ext import commands
import re

def extract_user_id(mention: str) -> str:
    match = re.match(r'<@!?(\d+)>', mention)
    if match:
        return match.group(1)
    return None

class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="role", invoke_without_command=True)
    async def role(self, ctx: commands.Context):
        """Base role command, if no subcommand is passed."""
        await ctx.reply("Please specify a subcommand: `add` or `remove`", mention_author=False)

    @role.command(name="add")
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx: commands.Context, role: nextcord.Role, member: str = None):
        """Adds a role to a member. Usage: `?role add role member`."""
        if member is None:
            member = ctx.author
        else:
            user_id = extract_user_id(member)
            if user_id:
                member = ctx.guild.get_member(int(user_id))
            else:
                member = nextcord.utils.get(ctx.guild.members, name=member) or nextcord.utils.get(ctx.guild.members, display_name=member)

        if member is None:
            await ctx.reply("Member not found. Please provide a valid username or display name.", mention_author=False)
            return

        try:
            await member.add_roles(role)
            await ctx.reply(f"Added role `{role.name}` to **{member.display_name}**.", mention_author=False)
        except nextcord.Forbidden:
            await ctx.reply("I don't have permission to add that role.", mention_author=False)
        except nextcord.HTTPException as e:
            await ctx.reply(f"An error occurred: {str(e)}", mention_author=False)

    @role.command(name="remove")
    @commands.has_permissions(manage_roles=True)
    async def remove(self, ctx: commands.Context, role: nextcord.Role, member: str = None):
        """Removes a role from a member. Usage: `?role remove role member`."""
        if member is None:
            member = ctx.author
        else:
            user_id = extract_user_id(member)
            if user_id:
                member = ctx.guild.get_member(int(user_id))
            else:
                member = nextcord.utils.get(ctx.guild.members, name=member) or nextcord.utils.get(ctx.guild.members, display_name=member)

        if member is None:
            await ctx.reply("Member not found. Please provide a valid username or display name.", mention_author=False)
            return

        try:
            await member.remove_roles(role)
            await ctx.reply(f"Removed role `{role.name}` from **{member.display_name}**.", mention_author=False)
        except nextcord.Forbidden:
            await ctx.reply("I don't have permission to remove that role.", mention_author=False)
        except nextcord.HTTPException as e:
            await ctx.reply(f"An error occurred: {str(e)}", mention_author=False)

    @role.error
    async def role_error(self, ctx: commands.Context, error):
        """Handle errors for the role command group."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("You don't have permission to manage roles.", mention_author=False)
        elif isinstance(error, commands.BadArgument):
            await ctx.reply("Invalid role or user. Please mention the correct role and member.", mention_author=False)
        else:
            await ctx.reply(f"An error occurred: {str(error)}", mention_author=False)

def setup(bot):
    bot.add_cog(Roles(bot))
