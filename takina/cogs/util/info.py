import nextcord
from nextcord.ext import commands
import re

def extract_user_id(mention: str) -> str:
    match = re.match(r'<@!?(\d+)>', mention)
    if match:
        return match.group(1)
    return None

class UserInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="userinfo")
    async def userinfo(self, ctx: commands.Context, member: str = None):
        """Fetch user information. Usage: `userinfo member`."""
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
        
        roles = [role for role in member.roles if role != ctx.guild.default_role]
        embed = nextcord.Embed(color=EMBED_COLOR, timestamp=ctx.message.created_at,
                                title=f"User Info - {member}")

        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.add_field(name="ID:", value=member.id, inline=True)
        embed.add_field(name="Name:", value=member.display_name, inline=True)

        embed.add_field(name="Created on:", value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"), inline=True)
        embed.add_field(name="Joined on:", value=member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"), inline=True)

        embed.add_field(name=f"Roles ({len(roles)}):", value=" ".join([role.mention for role in roles]), inline=True)
        embed.add_field(name="Top Role:", value=member.top_role.mention, inline=True)
        if member.bot:
            embed.set_footer(text="This user is a bot account.")

        await ctx.reply(embed=embed, mention_author=False)
    
    # TODO: add the underneath code to every command in anna (i will literally never do this)
    # to anyone reading this: watch lycoris recoil, it's peak fiction
    # @userinfo.error
    # async def userinfo_error(self, ctx: commands.Context, error):
    #     if isinstance(error, commands.BadArgument) or isinstance(error, commands.UserInputError):
    #         await ctx.send("Invalid argument. Use: `a?userinfo` or `a?userinfo member`.")


class RoleInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="roleinfo")
    async def roleinfo(self, ctx: commands.Context, role: nextcord.Role):
        """Fetch role information. `a?roleinfo role`."""
        embed = nextcord.Embed(title=f"Role Info - {role.name}", color=role.color)
        embed.add_field(name="ID", value=role.id)
        embed.add_field(name="Name", value=role.name)
        embed.add_field(name="Color", value=str(role.color))
        embed.add_field(name="Position", value=role.position)
        embed.add_field(name="Mentionable", value=role.mentionable)
        embed.add_field(name="Permissions", value=", ".join([perm[0] for perm in role.permissions if perm[1]]))
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.reply(embed=embed, mention_author=False)

class ServerInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="serverinfo")
    async def serverinfo(self, ctx: commands.Context):
        """Fetch server information. `a?serverinfo`."""
        guild = ctx.guild
        embed = nextcord.Embed(title=f"{guild.name}", color=EMBED_COLOR)

        embed.add_field(name="Server Name", value=guild.name, inline=True)
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.set_thumbnail(url=guild.icon.url)

        await ctx.reply(embed=embed, mention_author=False)


def setup(bot):
    bot.add_cog(UserInfo(bot))
    bot.add_cog(RoleInfo(bot))
    bot.add_cog(ServerInfo(bot))
