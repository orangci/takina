from nextcord.ext import application_checks, commands
import nextcord
from nextcord import SlashOption
from config import *
from ..libs.oclib import *
from datetime import timedelta


class ModUtils(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.command()
    @commands.is_owner()
    async def send(
        self,
        ctx: commands.Context,
        channel: nextcord.TextChannel = None,
        *,
        message: str,
    ):
        if channel and message:
            await channel.send(message)
            embed = nextcord.Embed(
                description="✅ Successfully sent message.", color=EMBED_COLOR
            )
            await ctx.reply(embed=embed, mention_author=False, delete_after=2)
        elif message:
            await ctx.reply(message, mention_author=False)
        else:
            await ctx.reply(
                "Please provide a message and channel to use this command.",
                mention_author=False,
            )

    @commands.command(
        help="Purges a specified number of messages. \nUsage: `purge <number>`.",
    )
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def purge(self, ctx: commands.Context, amount: int):
        if amount <= 0 or amount > 100:
            embed = nextcord.Embed(
                description="Please specify a number between 1 and 100 for messages to purge.",
                color=ERROR_COLOR,
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        deleted = await ctx.channel.purge(
            limit=amount + 1,
            check=lambda m: m.created_at > nextcord.utils.utcnow() - timedelta(weeks=2),
            bulk=True,
        )

        embed = nextcord.Embed(
            description=(
                f"✅ Successfully purged {len(deleted) - 1} messages."
                if len(deleted) > 1
                else ":x: I cannot purge messages older than two weeks."
            ),
            color=EMBED_COLOR if len(deleted) > 1 else ERROR_COLOR,
        )
        await ctx.send(embed=embed, delete_after=2)

    @commands.command(
        aliases=["setnick"],
        help="Change a member's nickname. \nUsage: `setnick <member> <new nickname>`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
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


class SlashModUtils(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @nextcord.slash_command(
        name="purge", description="Purges a specified number of messages."
    )
    @application_checks.has_permissions(manage_messages=True)
    async def purge(
        self,
        interaction: nextcord.Interaction,
        amount: int = SlashOption(
            description="Number of messages to purge", required=True
        ),
    ):
        if amount <= 0 or amount > 100:
            embed = nextcord.Embed(
                description="Please specify a number between 1 and 100 for messages to purge.",
                color=ERROR_COLOR,
            )
            await interaction.send(embed=embed, ephemeral=True)
            return

        deleted = await interaction.channel.purge(
            limit=amount + 1,
            check=lambda m: m.created_at > nextcord.utils.utcnow() - timedelta(weeks=2),
            bulk=True,
        )

        embed = nextcord.Embed(
            description=(
                f"✅ Successfully purged {len(deleted) - 1} messages."
                if len(deleted) > 1
                else ":x: I cannot purge messages older than two weeks."
            ),
            color=EMBED_COLOR if len(deleted) > 1 else ERROR_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="nick", description="Change a member's nickname.")
    @application_checks.has_permissions(manage_nicknames=True)
    async def nick(
        self,
        interaction: nextcord.Interaction,
        member: str = SlashOption(
            description="Member to change the nickname for", required=True
        ),
        nickname: str = SlashOption(description="New nickname"),
    ):
        if member is None:
            member = ctx.author
        else:
            member = extract_user_id(member, ctx)
            if isinstance(member, nextcord.Embed):
                await ctx.reply(embed=member, mention_author=False)
                return

        # Check permissions
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
    bot.add_cog(ModUtils(bot))
    bot.add_cog(SlashModUtils(bot))
