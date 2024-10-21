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
            if isinstance(member, str):
                embed = nextcord.Embed(description=member, color=0xFF0037)
                await ctx.reply(embed=embed, mention_author=False)
                return

        roles = [role for role in member.roles if role != ctx.guild.default_role]

        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            color=EMBED_COLOR,
            title=f"{emoji} {member}",
            description=(
                f"> **Username:** {member.name}\n"
                f"> **Display Name:** {member.display_name}\n"
                f"> **ID:** {member.id}\n"
                f"> **Created on:** <t:{int(member.created_at.timestamp())}:D> (<t:{int(member.created_at.timestamp())}:R>)\n"
                f"> **Joined on:** <t:{int(member.joined_at.timestamp())}:D> (<t:{int(member.joined_at.timestamp())}:R>)\n"
                f"> **Roles ({len(roles)}):** {' '.join([role.mention for role in reversed(roles)])}"
            ),
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)

        if member.bot:
            embed.set_footer(text="This user is a bot account.")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="roleinfo")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def roleinfo(self, ctx: commands.Context, *, role: nextcord.Role):
        """Fetch role information. `roleinfo role`."""
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"{emoji} Role Info - {role.name}",
            color=role.color,
            description=(
                f"> **ID:** {role.id}\n"
                f"> **Name:** {role.name}\n"
                f"> **Color:** {str(role.color)}\n"
                f"> **Position:** {role.position}\n"
                f"> **Mentionable:** {role.mentionable}\n"
                f"> **Permissions:** {', '.join([perm[0] for perm in role.permissions if perm[1]])}"
            ),
        )
        embed.set_thumbnail(url=role.icon.url if role.icon else None)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="serverinfo")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def serverinfo(self, ctx: commands.Context):
        """Fetch server information. `serverinfo`."""
        guild = ctx.guild
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"{emoji} {guild.name}",
            color=EMBED_COLOR,
            description=(
                f"> **Server ID:** {guild.id}\n"
                f"> **Server Name:** {guild.name}\n"
                f"> **Owner:** {guild.owner}\n"
                f"> **Created:** <t:{int(guild.created_at.timestamp())}:D> (<t:{int(guild.created_at.timestamp())}:R>)\n"
                f"> **Members:** {guild.member_count}\n"
                f"> **Roles:** {len(guild.roles)}\n"
                f"> **Channels:** {len(guild.channels)}"
            ),
        )
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
            title=f"{emoji} {member}",
            description=(
                f"> **ID:** {member.id}\n"
                f"> **Name:** {member.display_name}\n"
                f"> **Created:** <t:{int(member.created_at.timestamp())}:D> (<t:{int(member.created_at.timestamp())}:R>)\n"
                f"> **Joined:** <t:{int(member.joined_at.timestamp())}:D> (<t:{int(member.joined_at.timestamp())}:R>)\n"
                f"> **Roles ({len(roles)}):** {' '.join([role.mention for role in reversed(roles)])}\n"
                f"> **Top Role:** {member.top_role.mention}"
            ),
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
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
            title=f"{emoji} Role Info - {role.name}",
            color=role.color,
            description=(
                f"> **ID:** {role.id}\n"
                f"> **Name:** {role.name}\n"
                f"> **Color:** {str(role.color)}\n"
                f"> **Position:** {role.position}\n"
                f"> **Mentionable:** {role.mentionable}\n"
                f"> **Permissions:** {', '.join([perm[0] for perm in role.permissions if perm[1]])}"
            ),
        )
        embed.set_thumbnail(url=role.icon.url if role.icon else None)
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="serverinfo")
    async def serverinfo(self, interaction: nextcord.Interaction):
        """Fetch server information. `serverinfo`."""
        guild = interaction.guild
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"{emoji} {guild.name}",
            color=EMBED_COLOR,
            description=(
                f"> **Server ID:** {guild.id}\n"
                f"> **Server Name:** {guild.name}\n"
                f"> **Owner:** {guild.owner}\n"
                f"> **Created:** <t:{int(guild.created_at.timestamp())}:D> (<t:{int(guild.created_at.timestamp())}:R>)\n"
                f"> **Members:** {guild.member_count}\n"
                f"> **Roles:** {len(guild.roles)}\n"
                f"> **Channels:** {len(guild.channels)}"
            ),
        )
        embed.set_thumbnail(url=guild.icon.url)

        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Info(bot))
    bot.add_cog(SlashInfo(bot))
