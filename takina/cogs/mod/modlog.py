# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyviews
from datetime import datetime, timedelta, UTC
from takina import config, database, models
from discord.ext import commands
import discord


class ModLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_group(
        name="modlog",
        description="Manage the server's moderation log.",
        invoke_without_command=True,
    )
    @lychecks.guild_only()
    async def modlog(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @modlog.command(
        name="channel",
        description="Set the channel where moderation actions are logged.",
        usage="#channel",
    )
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel):
        assert ctx.guild is not None

        settings = await database.get_or_create(models.GuildSettingsModel, guild_id=ctx.guild.id)
        settings.modlog_channel_id = channel.id
        await database.save(settings)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = (
            f"{config.emojis.SUCCESS} Modlog channel has been set to {channel.mention}."
        )

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(description="Fetch information on a moderation case.", usage="42")
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def case(self, ctx: commands.Context, case_id: int):
        assert ctx.guild is not None

        case = await database.get(models.ModLogCaseModel, guild_id=ctx.guild.id, case_id=case_id)
        if case is None:
            raise lyerrors.TakinaNotFoundError(f"Case `#{case_id}` does not exist.")

        action = (
            f"{case.action.title()} ({case.duration})" if case.duration else case.action.title()
        )

        if case.mass_action:
            targets = ", ".join(f"<@{member_id}>" for member_id in case.member_ids)
        else:
            targets = f"<@{case.member_ids[0]}>"

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.timestamp = case.timestamp

        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="Case", value=f"#{case.case_id}", inline=True)
        embed.add_field(name="Moderator", value=f"<@{case.moderator_id}>", inline=True)
        embed.add_field(
            name="Targets" if case.mass_action else "Target", value=targets, inline=False
        )
        embed.add_field(name="Reason", value=case.reason, inline=False)

        if not case.mass_action:
            target = self._bot.get_user(case.member_ids[0])

            if target is not None and target.avatar:
                embed.set_thumbnail(url=target.avatar.url)

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        aliases=["caseedit", "editc"],
        description="Edit the reason for a moderation case.",
        usage="11 new reason",
    )
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def edit_case(self, ctx: commands.Context, case_id: int, *, new_reason: str):
        assert ctx.guild is not None

        case = await database.get(models.ModLogCaseModel, guild_id=ctx.guild.id, case_id=case_id)
        if case is None:
            raise lyerrors.TakinaNotFoundError(f"Case `#{case_id}` does not exist.")

        case.reason = new_reason
        await database.save(case)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"Case `#{case_id}`'s reason has been updated."

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(description="List moderation cases for a user.", usage="@user")
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def cases(self, ctx: commands.Context, user: discord.Member | None = None):
        assert ctx.guild is not None

        cases = await database.get_all(models.ModLogCaseModel, guild_id=ctx.guild.id)
        if user is not None:
            cases = [case for case in cases if user.id in case.member_ids]

        # sort cases by newest to oldest
        # ..like wick!
        cases.sort(key=lambda case: case.case_id, reverse=True)
        if not cases:
            raise lyerrors.TakinaNotFoundError("This server has no moderation cases yet.")

        embeds: list[discord.Embed] = []
        for chunk_start in range(0, len(cases), 10):
            chunk = cases[chunk_start : chunk_start + 10]

            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.title = "Moderation Cases"
            embed.description = "\n".join(
                f"`#{case.case_id}`: **{case.action.title()}** <t:{int(case.timestamp.timestamp())}:R>"
                for case in chunk
            )

            if user is not None:
                embed.set_footer(text=f"Cases for {user}")

            embeds.append(embed)

        if len(embeds) == 1:
            await ctx.reply(embed=embeds[0], mention_author=False)
            return

        await lyviews.PaginatorView.send(ctx, embeds)

    @commands.hybrid_command(
        description="List moderation cases performed by a moderator.", usage="@user"
    )
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def modcases(self, ctx: commands.Context, moderator: discord.Member | None = None):
        assert ctx.guild is not None

        moderator = moderator or ctx.guild.get_member(ctx.author.id)
        if moderator is None:
            raise lyerrors.TakinaNotFoundError("Could not resolve the moderator.")

        cases = await database.get_all(models.ModLogCaseModel, guild_id=ctx.guild.id)
        cases = [case for case in cases if case.moderator_id == moderator.id]
        cases.sort(key=lambda case: case.case_id)

        if not cases:
            raise lyerrors.TakinaNotFoundError(
                f"{moderator.mention} has not performed any moderation actions."
            )

        embeds: list[discord.Embed] = []
        for chunk_start in range(0, len(cases), 10):
            chunk = cases[chunk_start : chunk_start + 10]

            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.title = f"Moderation Cases — {moderator.display_name}"
            embed.description = "\n".join(
                f"`#{case.case_id}`: **{case.action.title()}** <t:{int(case.timestamp.timestamp())}:R>"
                for case in chunk
            )

            embeds.append(embed)

        if len(embeds) == 1:
            await ctx.reply(embed=embeds[0], mention_author=False)
            return

        await lyviews.PaginatorView.send(ctx, embeds)

    @commands.hybrid_command(
        aliases=["ms"], description="List moderation statistics for a user.", usage="@user"
    )
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def modstats(self, ctx: commands.Context, user: discord.Member | None = None):
        assert ctx.guild is not None

        user = user or ctx.guild.get_member(ctx.author.id)
        if user is None:
            raise lyerrors.TakinaNotFoundError("Could not resolve the user.")

        cases = await database.get_all(models.ModLogCaseModel, guild_id=ctx.guild.id)
        user_cases = [case for case in cases if case.moderator_id == user.id]

        now = datetime.now(UTC)
        past_7_days = now - timedelta(days=7)
        past_30_days = now - timedelta(days=30)

        def count_actions(cases: list[models.ModLogCaseModel]) -> str:
            return "\n".join(
                f"> **{action.title()}s**: {sum(case.action == action for case in cases):,}"
                for action in ("warn", "mute", "ban")
            )

        last_7_days = [case for case in user_cases if case.timestamp >= past_7_days]
        last_30_days = [case for case in user_cases if case.timestamp >= past_30_days]

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = f"Modstats for {user.display_name}"

        embed.add_field(name="Last 7 Days", value=count_actions(last_7_days))
        embed.add_field(name="Last 30 Days", value=count_actions(last_30_days))
        embed.add_field(name="All Time", value=count_actions(user_cases))

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(ModLog(bot))
