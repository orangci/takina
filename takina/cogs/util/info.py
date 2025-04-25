# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import nextcord
import config
from nextcord.ext import commands

from ..libs import oclib


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="userinfo",
        help="Fetch information about a user. \nUsage: `userinfo <user>` or just `userinfo` if you want to fetch information about yourself.",
        aliases=["ui"],
    )
    async def userinfo(self, ctx: commands.Context, *, member: str = None):
        if member is None:
            member = ctx.author
        else:
            member = oclib.extract_user_id(member, ctx)
            if isinstance(member, nextcord.Embed):
                await ctx.reply(embed=member, mention_author=False)
                return

        roles = [role for role in member.roles if role != ctx.guild.default_role]

        dangerous_permissions = [
            "manage_events",
            "mention_everyone",
            "create_events",
            "manage_threads",
            "administrator",
            "ban_members",
            "kick_members",
            "manage_channels",
            "manage_guild",
            "manage_roles",
            "manage_webhooks",
            "moderate_members",
        ]

        dangerous_perms = [
            perm[0].replace("_", " ").title()
            for perm in member.guild_permissions
            if perm[1] and perm[0] in dangerous_permissions
        ]

        permissions_str = ", ".join(dangerous_perms) if dangerous_perms else None

        embed = nextcord.Embed(
            color=config.EMBED_COLOR,
            description=(
                f"> **Username:** {member.name}\n"
                f"> **Display Name:** {member.display_name}\n"
                f"> **ID:** {member.id}\n"
                f"> **Created on:** <t:{int(member.created_at.timestamp())}:D> (<t:{int(member.created_at.timestamp())}:R>)\n"
                f"> **Joined on:** <t:{int(member.joined_at.timestamp())}:D> (<t:{int(member.joined_at.timestamp())}:R>)\n"
                f"> **Roles ({len(roles)}):** {' '.join([role.mention for role in reversed(roles)])}"
            ),
        )

        embed.set_author(
            name=member.name,
            icon_url=member.avatar.url if member.avatar.url else None,
            url=f"https://discord.com/users/{member.id}",
        )

        if permissions_str:
            embed.description += f"\n> **Dangerous Permissions:** {permissions_str}"

        if member.communication_disabled_until:
            embed.description += f"\n> **Timed out until:** <t:{int(member.communication_disabled_until.timestamp())}> (<t:{int(member.communication_disabled_until.timestamp())}:R>)"

        if member.banner:
            embed.set_thumbnail(url=member.banner.url)

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        if member.bot:
            embed.set_footer(text="This user is a bot account.")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="roleinfo",
        help="Fetch information about a role. \nUsage: `Usage: roleinfo <role>`.",
        aliases=["ri"],
    )
    async def roleinfo(self, ctx: commands.Context, *, role: str):
        emoji = await oclib.fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"{emoji}{role.name}",
            color=role.color,
            description=(
                f"> **ID:** {role.id}\n"
                f"> **Name:** {role.name}\n"
                f"> **Colour:** {str(role.color)}\n"
                f"> **Position:** {len(ctx.guild.roles) - role.position}\n"
                f"> **Mentionable:** {role.mentionable}\n"
                f"> **Hoisted:** {role.hoist}\n"
                f"> **Managed:** {role.managed}\n"
                f"> **Members:** {len(role.members)}\n"
                f"> **Created:** <t:{int(role.created_at.timestamp())}:D> (<t:{int(role.created_at.timestamp())}:R>)\n"
                f"> **Permissions:** {', '.join([perm[0].replace('_', ' ').title() for perm in role.permissions if perm[1]])}"
            ),
        )

        embed.set_thumbnail(url=role.icon.url if role.icon else None)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="serverinfo",
        help="Fetch information about the server. \nUsage: `serverinfo`.",
        aliases=["si"],
    )
    async def serverinfo(self, ctx: commands.Context):
        guild = ctx.guild
        emoji = await oclib.fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"{emoji}{guild.name}",
            color=config.EMBED_COLOR,
            description=(
                f"> **Server ID:** {guild.id}\n"
                f"> **Server Name:** {guild.name}\n"
                f"> **Owner:** {guild.owner.mention}\n"
                f"> **Created:** <t:{int(guild.created_at.timestamp())}:D> (<t:{int(guild.created_at.timestamp())}:R>)\n"
                f"> **Members:** {guild.member_count}\n"
                f"> **Verification Level:** {guild.verification_level}\n"
                f"> **Roles:** {len(guild.roles)}\n"
                f"> **Channels:** {len(guild.channels)}\n"
                f"> **Emojis:** {len(guild.emojis)} emojis and {len(guild.stickers)} stickers\n"
                f"> **Boosts:** Tier {guild.premium_tier} — {guild.premium_subscription_count} boosts\n"
            ),
        )
        if guild.description:
            embed.description = f"{guild.description}\n\n" + embed.description

        if guild.banner:
            embed.set_image(url=guild.banner.url)

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

        dangerous_permissions = [
            "manage_events",
            "mention_everyone",
            "create_events",
            "manage_threads",
            "administrator",
            "ban_members",
            "kick_members",
            "manage_channels",
            "manage_guild",
            "manage_roles",
            "manage_webhooks",
            "moderate_members",
        ]

        dangerous_perms = [
            perm[0].replace("_", " ").title()
            for perm in member.guild_permissions
            if perm[1] and perm[0] in dangerous_permissions
        ]

        permissions_str = ", ".join(dangerous_perms) if dangerous_perms else None

        embed = nextcord.Embed(
            color=config.EMBED_COLOR,
            description=(
                f"> **Username:** {member.name}\n"
                f"> **Display Name:** {member.display_name}\n"
                f"> **ID:** {member.id}\n"
                f"> **Created on:** <t:{int(member.created_at.timestamp())}:D> (<t:{int(member.created_at.timestamp())}:R>)\n"
                f"> **Joined on:** <t:{int(member.joined_at.timestamp())}:D> (<t:{int(member.joined_at.timestamp())}:R>)\n"
                f"> **Roles ({len(roles)}):** {' '.join([role.mention for role in reversed(roles)])}"
            ),
        )

        embed.set_author(
            name=member.name,
            icon_url=member.avatar.url if member.avatar.url else None,
            url=f"https://discord.com/users/{member.id}",
        )

        if permissions_str:
            embed.description += f"\n> **Dangerous Permissions:** {permissions_str}"

        if member.communication_disabled_until:
            embed.description += f"\n> **Timed out until:** <t:{int(member.communication_disabled_until.timestamp())}> (<t:{int(member.communication_disabled_until.timestamp())}:R>)"

        if member.banner:
            embed.set_thumbnail(url=member.banner.url)

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
        emoji = await oclib.fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"{emoji}{role.name}",
            color=role.color,
            description=(
                f"> **ID:** {role.id}\n"
                f"> **Name:** {role.name}\n"
                f"> **Colour:** {str(role.color)}\n"
                f"> **Position:** {len(interaction.guild.roles) - role.position}\n"
                f"> **Mentionable:** {role.mentionable}\n"
                f"> **Hoisted:** {role.hoist}\n"
                f"> **Managed:** {role.managed}\n"
                f"> **Members:** {len(role.members)}\n"
                f"> **Created:** <t:{int(role.created_at.timestamp())}:D> (<t:{int(role.created_at.timestamp())}:R>)\n"
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
        emoji = await oclib.fetch_random_emoji()
        embed = nextcord.Embed(
            title=f"{emoji}{guild.name}",
            color=config.EMBED_COLOR,
            description=(
                f"> **Server ID:** {guild.id}\n"
                f"> **Server Name:** {guild.name}\n"
                f"> **Owner:** {guild.owner.mention}\n"
                f"> **Created:** <t:{int(guild.created_at.timestamp())}:D> (<t:{int(guild.created_at.timestamp())}:R>)\n"
                f"> **Members:** {guild.member_count}\n"
                f"> **Verification Level:** {guild.verification_level}\n"
                f"> **Roles:** {len(guild.roles)}\n"
                f"> **Channels:** {len(guild.channels)}\n"
                f"> **Emojis:** {len(guild.emojis)} emojis and {len(guild.stickers)} stickers\n"
                f"> **Boosts:** Tier {guild.premium_tier} — {guild.premium_subscription_count} boosts\n"
            ),
        )
        if guild.description:
            embed.description = f"{guild.description}\n\n" + embed.description

        if guild.banner:
            embed.set_image(url=guild.banner.url)

        embed.set_thumbnail(url=guild.icon.url)

        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Info(bot))
    bot.add_cog(SlashInfo(bot))
