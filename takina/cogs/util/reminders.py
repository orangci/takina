# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers, lyviews
from datetime import datetime, timedelta, UTC
from takina import config, database, models
from discord.ext import commands, tasks
import logging
import discord
import re

MAX_REMINDERS = 25
MIN_DURATION = 5 * 60
MAX_DURATION = lyhelpers.DURATION_UNITS["y"]
MAX_REMINDER_LENGTH = 1000
PAGE_LENGTH = 1000

DURATION_WORD = re.compile(r"(?:\d+[ywdhms])+", re.IGNORECASE)

logger = logging.getLogger("takina.reminders")


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def cog_load(self):
        self._check_reminders.start()

    def cog_unload(self):
        self._check_reminders.cancel()

    @commands.hybrid_group(
        name="reminder",
        description="Manage your reminders.",
        aliases=["reminders", "remind", "todo"],
    )
    @lychecks.is_user_app()
    async def reminder(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @reminder.command(
        name="set",
        description="Set a reminder. Minimum duration is 5 minutes.",
        usage="4h feed the cat",
    )
    @lychecks.is_user_app()
    async def reminder_set(
        self,
        ctx: commands.Context,
        time: str,
        *,
        reminder: commands.Range[str, 1, MAX_REMINDER_LENGTH],
    ):
        # a prefix invocation splits "1h 30m feed the cat" after "1h"
        if ctx.interaction is None:
            while len(parts := reminder.split(maxsplit=1)) == 2 and DURATION_WORD.fullmatch(
                parts[0]
            ):
                time += parts[0]
                reminder = parts[1]

        duration = lyhelpers.duration_calculator(time)

        if duration < MIN_DURATION:
            raise lyerrors.TakinaUserInputError(
                "The minimum duration required for a reminder is five minutes."
            )

        if duration > MAX_DURATION:
            raise lyerrors.TakinaUserInputError("Reminders can be at most a year away.")

        reminders = await database.get_all(models.ReminderModel, user_id=ctx.author.id)

        if len(reminders) >= MAX_REMINDERS:
            raise lyerrors.TakinaError(f"You can only have {MAX_REMINDERS} active reminders.")

        remind_at = datetime.now(UTC) + timedelta(seconds=duration)
        reminder_model = models.ReminderModel(
            user_id=ctx.author.id, reminder=reminder, remind_at=remind_at
        )
        await database.save(reminder_model)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{await lyhelpers.fetch_random_emoji()} Reminder set for {lyhelpers.reverse_duration_calculator(duration)} from now (<t:{int(remind_at.timestamp())}:R>): **{reminder}**"
        embed.description += f"\n-# ID: `{reminder_model.id}`. It arrives by DM, so keep them open."

        await ctx.reply(embed=embed, mention_author=False)

    @reminder.command(name="list", description="List all your active reminders.", usage="")
    @lychecks.is_user_app()
    async def reminder_list(self, ctx: commands.Context):
        reminders = await database.get_all(models.ReminderModel, user_id=ctx.author.id)
        reminders.sort(key=lambda reminder: reminder.remind_at)

        if not reminders:
            raise lyerrors.TakinaNotFoundError("You have no active reminders.")

        title = f"{await lyhelpers.fetch_random_emoji()} {ctx.author}'s Reminders"
        embeds: list[discord.Embed] = []
        current_embed = discord.Embed(title=title, colour=config.EMBED_COLOUR)
        current_embed.description = ""

        for reminder in reminders:
            remind_at = reminder.remind_at.astimezone(UTC)

            entry = f"\n\n> **ID**: `{reminder.id}`"
            entry += f"\n> **Reminder**: {reminder.reminder}"
            entry += f"\n> **Time**: <t:{int(remind_at.timestamp())}:F> (<t:{int(remind_at.timestamp())}:R>)"

            if (
                current_embed.description
                and len(current_embed.description) + len(entry) > PAGE_LENGTH
            ):
                embeds.append(current_embed)

                current_embed = discord.Embed(title=title, colour=config.EMBED_COLOUR)
                current_embed.description = entry
            else:
                current_embed.description += entry

        embeds.append(current_embed)

        if len(embeds) == 1:
            await ctx.reply(embed=embeds[0], mention_author=False)
            return

        await lyviews.PaginatorView.send(ctx, embeds)

    @reminder.command(
        name="delete", description="Delete a reminder by its ID.", usage="c617671342a58aeef597f911"
    )
    @lychecks.is_user_app()
    async def reminder_delete(self, ctx: commands.Context, reminder_id: commands.Range[str, 1, 24]):
        reminder = await database.get(models.ReminderModel, id=reminder_id, user_id=ctx.author.id)

        if not reminder:
            raise lyerrors.TakinaNotFoundError(f"No reminder found with ID `{reminder_id}`.")

        await database.delete(reminder)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = (
            f"{config.emojis.SUCCESS} Reminder with ID `{reminder_id}` has been deleted."
        )

        await ctx.reply(embed=embed, mention_author=False)

    @tasks.loop(seconds=60)
    async def _check_reminders(self):
        try:
            reminders = await database.get_all(
                models.ReminderModel,
                where=[models.ReminderModel.remind_at <= datetime.now(UTC)],
                order_by=models.ReminderModel.remind_at,
            )
        except Exception:
            # an unhandled error stops tasks.loop for good, so wait for the next tick instead
            logger.exception("failed to fetch reminders")
            return

        for reminder in reminders:
            try:
                await self._deliver_reminder(reminder)
            except Exception:
                # keep the reminder for the next tick and keep the loop alive
                logger.exception(f"failed to deliver reminder {reminder.id}")

    async def _deliver_reminder(self, reminder: models.ReminderModel) -> None:
        user = self._bot.get_user(reminder.user_id)

        if user is None:
            try:
                user = await self._bot.fetch_user(reminder.user_id)
            except discord.NotFound:
                await database.delete(reminder)
                return

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = (
            f"{await lyhelpers.fetch_random_emoji()} **Reminder**: {reminder.reminder}"
        )

        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            # dms are closed, so delivery can never succeed; set warns about this
            logger.info(f"dropped reminder {reminder.id}, as {reminder.user_id} has dms closed")

        await database.delete(reminder)

    @_check_reminders.before_loop
    async def _before_check_reminders(self):
        await self._bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
