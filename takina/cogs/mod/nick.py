# SPDX-License-Identifier: AGPL-3.0-or-later
from nextcord.ext import application_checks, commands
import nextcord
from nextcord import SlashOption
from config import *
from ..libs.oclib import *


class Nick(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.command(
        aliases=["setnick"],
        help="Change a member's nickname. \nUsage: `setnick <member> <new nickname>`.",
    )
    @commands.has_permissions(manage_nicknames=True)
    async def nick(
        self, ctx: commands.Context, member: str = None, *, nickname: str = None
    ):
        if member is None:
            member = ctx.author
        else:
            member = extract_user_id(member, ctx)
            if isinstance(member, nextcord.Embed):
                await ctx.reply(embed=member, mention_author=False)
                return

        # Check permissions
        can_proceed, message = perms_check(member, ctx=ctx, author_check=False)
        if not can_proceed:
            await ctx.reply(embed=message, mention_author=False)
            return

        if not nickname:
            nickname = member.global_name

        await member.edit(nick=nickname)
        embed = nextcord.Embed(
            description=f"✅ **{member.mention}**'s nickname has been changed to **{nickname}**."
        )
        await ctx.reply(
            embed=embed,
            mention_author=False,
        )

    @nextcord.slash_command(name="nickname", description="Change a member's nickname.")
    @application_checks.has_permissions(manage_nicknames=True)
    async def slash_nick(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = SlashOption(
            description="Member to change the nickname for", required=True
        ),
        nickname: str = SlashOption(description="New nickname", required=False),
    ):
        await interaction.response.defer()
        can_proceed, message = perms_check(member, ctx=interaction, author_check=False)
        if not can_proceed:
            await interaction.send(embed=message, ephemeral=True)
            return

        if not nickname:
            nickname = member.global_name

        await member.edit(nick=nickname)
        embed = nextcord.Embed(
            description=f"✅ **{member.mention}**'s nickname has been changed to **{nickname}**."
        )
        await interaction.send(
            embed=embed,
            ephemeral=True,
        )


def setup(bot: commands.Bot):
    bot.add_cog(Nick(bot))
