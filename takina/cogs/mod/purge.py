# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from datetime import timedelta

import nextcord
import config
from nextcord.ext import application_checks, commands

from ..libs import oclib


class Purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        help="Purges messages based on specified criteria. Usage: `purge <number>`, `purge user`, `purge bots`, `purge before`, `purge after`.",
        invoke_without_command=True,
    )
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int):
        if amount <= 0 or amount > 200:
            embed = nextcord.Embed(description=":x: Please specify a number between 1 and 200.", color=config.ERROR_COLOR)
            await ctx.reply(embed=embed, mention_author=False)
            return

        deleted = await ctx.channel.purge(limit=amount + 1, check=lambda m: m.created_at > nextcord.utils.utcnow() - timedelta(weeks=2), bulk=True)

        embed = nextcord.Embed(description=f"✅ Successfully purged {len(deleted) - 1} messages.", color=config.EMBED_COLOR)
        await ctx.send(embed=embed, delete_after=2)

    @purge.command(name="user", help="Purges messages from a specific user. Usage: purge user <user> <number>.")
    async def purge_user(self, ctx: commands.Context, member: str, amount: int):
        if amount <= 0 or amount > 200:
            embed = nextcord.Embed(description=":x: Please specify a number between 1 and 200.", color=config.ERROR_COLOR)
            await ctx.reply(embed=embed, mention_author=False)
            return

        member = oclib.extract_user_id(member, ctx)
        if isinstance(member, nextcord.Embed):
            await ctx.reply(embed=member, mention_author=False)
            return

        def check(message):
            return message.author == member and message.created_at > nextcord.utils.utcnow() - timedelta(weeks=2)

        deleted = await ctx.channel.purge(limit=amount, check=check, bulk=True)

        embed = nextcord.Embed(description=f"✅ Successfully purged {len(deleted)} messages from {member.mention}.", color=config.EMBED_COLOR)
        await ctx.send(embed=embed, delete_after=2)

    @purge.command(name="bots", help="Purges messages sent by bots. Usage: purge bots <number>.")
    async def purge_bots(self, ctx: commands.Context, amount: int):
        if amount <= 0 or amount > 100:
            embed = nextcord.Embed(description=":x: Please specify a number between 1 and 200.", color=config.ERROR_COLOR)
            await ctx.reply(embed=embed, mention_author=False)
            return

        def check(message):
            return message.author.bot and message.created_at > nextcord.utils.utcnow() - timedelta(weeks=2)

        deleted = await ctx.channel.purge(limit=amount, check=check, bulk=True)

        embed = nextcord.Embed(description=f"✅ Successfully purged {len(deleted)} messages sent by bots.", color=config.EMBED_COLOR)
        await ctx.send(embed=embed, delete_after=2)


class SlashPurge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="purge", description="Purge messages.")
    @application_checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: nextcord.Interaction):
        pass

    @purge.subcommand(name="all", description="Purge a number of messages.")
    @application_checks.has_permissions(manage_messages=True)
    async def purge_all(self, interaction: nextcord.Interaction, amount: int):
        await interaction.response.defer()
        if amount <= 0 or amount > 200:
            embed = nextcord.Embed(description=":x: Please specify a number between 1 and 200.", color=config.ERROR_COLOR)
            await interaction.send(embed=embed, ephemeral=True)
            return

        deleted = await interaction.channel.purge(
            limit=amount + 1, check=lambda m: m.created_at > nextcord.utils.utcnow() - timedelta(weeks=2), bulk=True
        )

        embed = nextcord.Embed(description=f"✅ Successfully purged {len(deleted) - 1} messages.", color=config.EMBED_COLOR)
        await interaction.send(embed=embed, ephemeral=True)

    @purge.subcommand(name="user", description="Purge messages from a specific user.")
    @application_checks.has_permissions(manage_messages=True)
    async def purge_user(self, interaction: nextcord.Interaction, user: nextcord.Member, amount: int):
        await interaction.response.defer()
        if amount <= 0 or amount > 200:
            embed = nextcord.Embed(description=":x: Please specify a number between 1 and 200.", color=config.ERROR_COLOR)
            await interaction.send(embed=embed, ephemeral=True)
            return

        def check(message):
            return message.author == user and message.created_at > nextcord.utils.utcnow() - timedelta(weeks=2)

        deleted = await interaction.channel.purge(limit=amount, check=check, bulk=True)

        embed = nextcord.Embed(description=f"✅ Successfully purged {len(deleted)} messages from {user.mention}.", color=config.EMBED_COLOR)
        await interaction.send(embed=embed, ephemeral=True)

    @purge.subcommand(name="bots", description="Purge messages sent by bots.")
    @application_checks.has_permissions(manage_messages=True)
    async def purge_bots(self, interaction: nextcord.Interaction, amount: int):
        await interaction.response.defer()
        if amount <= 0 or amount > 100:
            embed = nextcord.Embed(description=":x: Please specify a number between 1 and 200.", color=config.ERROR_COLOR)
            await interaction.send(embed=embed, ephemeral=True)
            return

        def check(message):
            return message.author.bot and message.created_at > nextcord.utils.utcnow() - timedelta(weeks=2)

        deleted = await interaction.channel.purge(limit=amount, check=check, bulk=True)

        embed = nextcord.Embed(description=f"✅ Successfully purged {len(deleted)} messages sent by bots.", color=config.EMBED_COLOR)
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Purge(bot))
    bot.add_cog(SlashPurge(bot))
