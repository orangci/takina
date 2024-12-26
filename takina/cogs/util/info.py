import nextcord
from nextcord.ext import commands
from ..libs.oclib import *
from config import *


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="userinfo",
        help="Fetch information about a user. \nUsage: `userinfo <user>` or just `userinfo` if you want to fetch information about yourself.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def userinfo(self, ctx: commands.Context, *, member: str = None):
        if member is None:
            member = ctx.author
        else:
            member = extract_user_id(member, ctx)
            if isinstance(member, nextcord.Embed):
                await ctx.reply(embed=member, mention_author=False)
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
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        if member.bot:
            embed.set_footer(text="This user is a bot account.")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="roleinfo",
        help="Fetch information about a role. \nUsage: `Usage: roleinfo <role>`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def roleinfo(self, ctx: commands.Context, *, role: nextcord.Role):
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
                f"> **Permissions:** {', '.join([perm[0].replace('_', ' ').title() for perm in role.permissions if perm[1]])}"
            ),
        )
        embed.set_thumbnail(url=role.icon.url if role.icon else None)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="serverinfo",
        help="Fetch information about the server. \nUsage: `serverinfo`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def serverinfo(self, ctx: commands.Context):
        guild = ctx.guild
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"{emoji} {guild.name}",
            color=EMBED_COLOR,
            description=(
                f"> **Server ID:** {guild.id}\n"
                f"> **Server Name:** {guild.name}\n"
                f"> **Owner:** {guild.owner.mention}\n"
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

    @nextcord.slash_command(
        name="userinfo", description="Fetch information about a user."
    )
    async def userinfo(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = nextcord.SlashOption(
            description="The user to fetch information on", required=False
        ),
    ):
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
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        if member.bot:
            embed.set_footer(text="This user is a bot account.")

        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(
        name="roleinfo", description="Fetch information about a role."
    )
    async def roleinfo(
        self,
        interaction: nextcord.Interaction,
        role: nextcord.Role = nextcord.SlashOption(
            description="The role to fetch information on", required=True
        ),
    ):
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
                f"> **Permissions:** {', '.join([perm[0].replace('_', ' ').title() for perm in role.permissions if perm[1]])}"
            ),
        )
        embed.set_thumbnail(url=role.icon.url if role.icon else None)
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(
        name="serverinfo", description="Fetch information about the server."
    )
    async def serverinfo(self, interaction: nextcord.Interaction):
        guild = interaction.guild
        emoji = await fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"{emoji} {guild.name}",
            color=EMBED_COLOR,
            description=(
                f"> **Server ID:** {guild.id}\n"
                f"> **Server Name:** {guild.name}\n"
                f"> **Owner:** {guild.owner.mention}\n"
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
