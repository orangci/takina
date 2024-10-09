import nextcord
from nextcord.ext import commands
import re
from ..libs.oclib import *
from __main__ import EMBED_COLOR
from nextcord.utils import utcnow


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="userinfo")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def userinfo(self, ctx: commands.Context, member: str = None):
        """Fetch user information. Usage: `userinfo member`."""
        if member is None:
            member = ctx.author
        else:
            member = extract_user_id(member, ctx)

        if not isinstance(member, nextcord.Member):
            await ctx.reply(
                "Member not found. Please provide a valid username, display name, mention, or user ID.",
                mention_author=False,
            )
            return

        roles = [role for role in member.roles if role != ctx.guild.default_role]

        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            color=EMBED_COLOR,
            timestamp=ctx.message.created_at,
            title=f"{emoji} {member}",
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.add_field(name="ID:", value=member.id, inline=True)
        embed.add_field(name="Name:", value=member.display_name, inline=True)
        embed.add_field(
            name="Created on:",
            value=member.created_at.strftime("%a, %#d %B %Y"),
            inline=True,
        )
        embed.add_field(
            name="Joined on:",
            value=member.joined_at.strftime("%a, %#d %B %Y"),
            inline=True,
        )
        embed.add_field(
            name=f"Roles ({len(roles)}):",
            value=" ".join([role.mention for role in roles]),
            inline=True,
        )
        embed.add_field(name="Top Role:", value=member.top_role.mention, inline=True)

        if member.bot:
            embed.set_footer(text="This user is a bot account.")

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="roleinfo")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def roleinfo(self, ctx: commands.Context, role: nextcord.Role):
        """Fetch role information. `roleinfo role`."""
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"{emoji} Role Info - {role.name}", color=role.color
        )
        embed.add_field(name="ID", value=role.id)
        embed.add_field(name="Name", value=role.name)
        embed.add_field(name="Color", value=str(role.color))
        embed.add_field(name="Position", value=role.position)
        embed.add_field(name="Mentionable", value=role.mentionable)
        embed.add_field(
            name="Permissions",
            value=", ".join([perm[0] for perm in role.permissions if perm[1]]),
        )
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="serverinfo")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def serverinfo(self, ctx: commands.Context):
        """Fetch server information. `serverinfo`."""
        guild = ctx.guild
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(title=f"{emoji} {guild.name}", color=EMBED_COLOR)

        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Server Name", value=guild.name, inline=True)
        embed.add_field(name="Owner", value=guild.owner, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.set_thumbnail(url=guild.icon.url)

        await ctx.reply(embed=embed, mention_author=False)


class SlashInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="userinfo")
    async def userinfo(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(
            description="The user to fetch information on", required=False
        ),
    ):
        """Fetch user information. Usage: `userinfo member`."""
        if member is None:
            member = interaction.user

        roles = [
            role for role in member.roles if role != interaction.guild.default_role
        ]

        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            color=EMBED_COLOR,
            timestamp=utcnow(),
            title=f"{emoji} {member}",
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.add_field(name="ID:", value=member.id, inline=True)
        embed.add_field(name="Name:", value=member.display_name, inline=True)
        embed.add_field(
            name="Created on:",
            value=member.created_at.strftime("%a, %#d %B %Y"),
            inline=True,
        )
        embed.add_field(
            name="Joined on:",
            value=member.joined_at.strftime("%a, %#d %B %Y"),
            inline=True,
        )
        embed.add_field(
            name=f"Roles ({len(roles)}):",
            value=" ".join([role.mention for role in roles]),
            inline=True,
        )
        embed.add_field(name="Top Role:", value=member.top_role.mention, inline=True)

        if member.bot:
            embed.set_footer(text="This user is a bot account.")

        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="roleinfo")
    async def roleinfo(
        self,
        interaction: nextcord.Interaction,
        role: nextcord.Role = nextcord.SlashOption(
            description="The role to fetch information on", required=True
        ),
    ):
        """Fetch role information. `roleinfo role`."""
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"{emoji} Role Info - {role.name}", color=role.color
        )
        embed.add_field(name="ID", value=role.id)
        embed.add_field(name="Name", value=role.name)
        embed.add_field(name="Color", value=str(role.color))
        embed.add_field(name="Position", value=role.position)
        embed.add_field(name="Mentionable", value=role.mentionable)
        embed.add_field(
            name="Permissions",
            value=", ".join([perm[0] for perm in role.permissions if perm[1]]),
        )
        embed.set_thumbnail(url=interaction.guild.icon.url)
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="serverinfo")
    async def serverinfo(self, interaction: nextcord.Interaction):
        """Fetch server information. `serverinfo`."""
        guild = interaction.guild
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(title=f"{emoji} {guild.name}", color=EMBED_COLOR)

        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Server Name", value=guild.name, inline=True)
        embed.add_field(name="Owner", value=guild.owner, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.set_thumbnail(url=guild.icon.url)

        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Info(bot))
    bot.add_cog(SlashInfo(bot))
