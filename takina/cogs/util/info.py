# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyhelpers, lyerrors, lychecks
from discord.ext import commands
from takina import config
import discord


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_command(
        name="userinfo",
        description="Fetch information about a user.",
        aliases=["ui", "profile", "user"],
        usage="@member",
    )
    @lychecks.guild_only()
    async def userinfo(self, ctx: commands.Context, *, member: discord.Member | None = None):
        assert ctx.guild is not None

        if member is None:
            if not isinstance(ctx.author, discord.Member):
                raise lyerrors.TakinaError("This command can only be used in a server.")
            member = ctx.author

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
            permission[0].replace("_", " ").title()
            for permission in member.guild_permissions
            if permission[1] and permission[0] in dangerous_permissions
        ]

        permissions_str = ", ".join(dangerous_perms) if dangerous_perms else None

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"> **Username**: {member.name}"
        embed.description += f"\n> **Display Name**: {member.display_name}"
        embed.description += f"\n> **Account ID**: {member.id}"
        embed.description += f"\n> **Created on**: <t:{int(member.created_at.timestamp())}:D> (<t:{int(member.created_at.timestamp())}:R>)"

        if member.joined_at:
            timestamp = int(member.joined_at.timestamp())
            embed.description += f"\n> **Joined on**: <t:{timestamp}:D> (<t:{timestamp}:R>)"

        embed.description += (
            f"\n> **Roles ({len(roles)})**: {' '.join(role.mention for role in reversed(roles))}"
        )

        embed.set_author(
            name=member.name,
            icon_url=member.avatar.url if member.avatar else None,
            url=f"https://discord.com/users/{member.id}",
        )

        if permissions_str:
            embed.description += f"\n> **Dangerous Permissions**: {permissions_str}"

        if member.timed_out_until:
            timestamp = int(member.timed_out_until.timestamp())
            embed.description += f"\n> **Timed out until**: <t:{timestamp}> (<t:{timestamp}:R>)"

        if member.banner:
            embed.set_image(url=member.banner.url)

        if member.guild_banner:
            embed.set_image(url=member.guild_banner.url)

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        if member.bot:
            embed.set_footer(text="This user is a bot account.")

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="roleinfo",
        description=("Fetch information about a role. Note that this command is case-sensitive."),
        aliases=["ri"],
        usage="Moderator",
    )
    @lychecks.guild_only()
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role):
        assert ctx.guild is not None

        embed = discord.Embed(colour=role.colour)
        embed.title = await lyhelpers.fetch_random_emoji() + role.name
        embed.description = f"> **Role ID**: {role.id}"
        embed.description += f"\n> **Name**: {role.name}"
        embed.description += f"\n> **Colour**: {role.colour}"
        embed.description += f"\n> **Position**: {len(ctx.guild.roles) - role.position}"
        embed.description += f"\n> **Mentionable**: {role.mentionable}"
        embed.description += f"\n> **Hoisted**: {role.hoist}"
        embed.description += f"\n> **Managed**: {role.managed}"
        embed.description += f"\n> **Members**: {len(role.members)}"
        embed.description += f"\n> **Created**: <t:{int(role.created_at.timestamp())}:D> (<t:{int(role.created_at.timestamp())}:R>)"
        if role.permissions:
            embed.description += "\n> **Permissions**: " + ", ".join(
                permission[0].replace("_", " ").title()
                for permission in role.permissions
                if permission[1]
            )

        if role.icon:
            embed.set_thumbnail(url=role.icon.url)

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="serverinfo",
        description="Fetch information about the server.",
        aliases=["si", "server"],
    )
    @lychecks.guild_only()
    async def serverinfo(self, ctx: commands.Context):
        assert ctx.guild is not None
        guild = ctx.guild

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = await lyhelpers.fetch_random_emoji() + guild.name
        embed.description = f"> **Server ID**: {guild.id}"
        embed.description += f"\n> **Server Name**: {guild.name}"

        if guild.owner:
            embed.description += f"\n> **Owner**: {guild.owner.mention}"
        else:
            embed.description += "\n> **Owner**: Unknown"

        embed.description += (
            f"\n> **Created**: <t:{int(guild.created_at.timestamp())}:D>"
            f" (<t:{int(guild.created_at.timestamp())}:R>)"
        )
        embed.description += f"\n> **Members**: {guild.member_count}"
        embed.description += f"\n> **Verification Level**: {guild.verification_level}"
        embed.description += f"\n> **Roles**: {len(guild.roles)}"
        embed.description += f"\n> **Channels**: {len(guild.channels)}"
        embed.description += (
            f"\n> **Emojis**: {len(guild.emojis)} emojis and {len(guild.stickers)} stickers"
        )
        embed.description += (
            f"\n> **Boosts**: Tier {guild.premium_tier} — {guild.premium_subscription_count} boosts"
        )

        if guild.description:
            embed.description = f"{guild.description}\n\n{embed.description}"

        if guild.banner:
            embed.set_image(url=guild.banner.url)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Info(bot))
