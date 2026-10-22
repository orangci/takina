# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers, lymodlog, lyviews
from datetime import datetime, timedelta, UTC
from takina import config, database, models
from discord.ext import commands
from sqlmodel import col
from typing import cast
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

        target = self._bot.get_user(case.member_ids[0]) if case.member_ids else None
        avatar_url = target.avatar.url if target and target.avatar else None

        await ctx.reply(embed=lymodlog.case_embed(case, avatar_url), mention_author=False)

    @commands.hybrid_command(
        aliases=["caseedit", "editc"],
        description="Edit the reason for a moderation case.",
        usage="11 new reason",
    )
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def edit_case(self, ctx: commands.Context, case_id: int, *, new_reason: lymodlog.Reason):
        assert ctx.guild is not None

        case = await database.get(models.ModLogCaseModel, guild_id=ctx.guild.id, case_id=case_id)
        if case is None:
            raise lyerrors.TakinaNotFoundError(f"Case `#{case_id}` does not exist.")

        case.reason = new_reason
        await database.save(case)
        await lymodlog.update_logged_case(ctx.guild, case, ctx.author)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Case `#{case_id}`'s reason has been updated."

        await ctx.reply(embed=embed, mention_author=False)

    async def send_case_list(
        self,
        ctx: commands.Context,
        cases: list[models.ModLogCaseModel],
        title: str,
        footer: str | None = None,
    ) -> None:
        embeds: list[discord.Embed] = []
        for chunk in lyhelpers.chunked(cases, 10):
            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.title = title
            embed.description = "\n".join(
                f"`#{case.case_id}`: **{case.action.title()}** <t:{int(case.timestamp.timestamp())}:R>"
                for case in chunk
            )

            if footer is not None:
                embed.set_footer(text=footer)

            embeds.append(embed)

        if len(embeds) == 1:
            await ctx.reply(embed=embeds[0], mention_author=False)
            return

        await lyviews.PaginatorView.send(ctx, embeds)

    @commands.hybrid_command(description="List moderation cases for a user.", usage="@user")
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def cases(self, ctx: commands.Context, user: discord.Member | None = None):
        assert ctx.guild is not None

        where = [] if user is None else [col(models.ModLogCaseModel.member_ids).contains([user.id])]
        # sort cases by newest to oldest
        # ..like wick!
        cases = await database.get_all(
            models.ModLogCaseModel,
            guild_id=ctx.guild.id,
            where=where,
            order_by=col(models.ModLogCaseModel.case_id).desc(),
        )
        if not cases:
            raise lyerrors.TakinaNotFoundError("This server has no moderation cases yet.")

        footer = f"Cases for {user}" if user is not None else None
        await self.send_case_list(ctx, cases, "Moderation Cases", footer)

    @commands.hybrid_command(
        description="List moderation cases performed by a moderator.", usage="@user"
    )
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def modcases(self, ctx: commands.Context, moderator: discord.Member | None = None):
        assert ctx.guild is not None
        moderator = moderator or cast(discord.Member, ctx.author)

        cases = await database.get_all(
            models.ModLogCaseModel,
            guild_id=ctx.guild.id,
            moderator_id=moderator.id,
            order_by=col(models.ModLogCaseModel.case_id).desc(),
        )
        if not cases:
            raise lyerrors.TakinaNotFoundError(
                f"{moderator.mention} has not performed any moderation actions."
            )

        await self.send_case_list(ctx, cases, f"Moderation Cases — {moderator.display_name}")

    @commands.hybrid_command(
        aliases=["ms"], description="List moderation statistics for a user.", usage="@user"
    )
    @lychecks.has_permissions(moderate_members=True)
    @lychecks.guild_only()
    async def modstats(self, ctx: commands.Context, user: discord.Member | None = None):
        assert ctx.guild is not None
        user = user or cast(discord.Member, ctx.author)

        user_cases = await database.get_all(
            models.ModLogCaseModel, guild_id=ctx.guild.id, moderator_id=user.id
        )

        now = datetime.now(UTC)
        past_7_days = now - timedelta(days=7)
        past_30_days = now - timedelta(days=30)

        def base_action(case: models.ModLogCaseModel) -> str:
            # a mass ban is still a ban, and so is a hackban
            action = case.action.removeprefix("mass ")
            return "ban" if action == "hackban" else action

        def count_actions(cases: list[models.ModLogCaseModel]) -> str:
            return "\n".join(
                f"> **{action.title()}s**: {sum(base_action(case) == action for case in cases):,}"
                for action in ("warn", "mute", "kick", "ban")
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
