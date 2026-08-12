# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers, lyviews
from datetime import datetime, timedelta, timezone
from takina import config, database, models
from discord.ext import commands, tasks
import discord

MAX_REMINDERS = 25


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
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
        description="Set a reminder. Minimum duration is 10 minutes.",
        usage="4h feed the cat",
    )
    @lychecks.is_user_app()
    async def reminder_set(self, ctx: commands.Context, time: str, *, reminder: str):
        duration = lyhelpers.duration_calculator(time)

        if duration < 300:
            raise lyerrors.TakinaUserInputError(
                "The minimum duration required for a reminder is five minutes."
            )

        reminders = await database.get_all(models.ReminderModel, user_id=ctx.author.id)

        if len(reminders) > MAX_REMINDERS:
            raise lyerrors.TakinaError(f"You can only have {MAX_REMINDERS} active reminders.")

        remind_at = datetime.now(timezone.utc) + timedelta(seconds=duration)
        reminder_model = models.ReminderModel(
            user_id=ctx.author.id, reminder=reminder, remind_at=remind_at
        )
        await database.save(reminder_model)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{await lyhelpers.fetch_random_emoji()} Reminder set for {time} from now: **{reminder}**"
        embed.description += f"\n-# ID: `{reminder_model.id}`"

        await ctx.reply(embed=embed, mention_author=False)

    @reminder.command(name="list", description="List all your active reminders.", usage="")
    @lychecks.is_user_app()
    async def reminder_list(self, ctx: commands.Context):
        reminders = await database.get_all(models.ReminderModel, user_id=ctx.author.id)
        reminders.sort(key=lambda reminder: reminder.remind_at)

        if not reminders:
            raise lyerrors.TakinaNotFoundError("You have no active reminders.")

        embeds: list[discord.Embed] = []
        current_embed = discord.Embed(
            title=f"{await lyhelpers.fetch_random_emoji()} {ctx.author}'s Reminders",
            colour=config.EMBED_COLOUR,
        )
        current_embed.description = ""

        count = 0
        for reminder in reminders:
            remind_at = reminder.remind_at.astimezone(timezone.utc)

            entry = f"\n\n> **ID**: `{reminder.id}`"
            entry += f"\n> **Reminder**: {reminder.reminder}"
            entry += f"\n> **Time**: <t:{int(remind_at.timestamp())}:F> (<t:{int(remind_at.timestamp())}:R>)"

            if len(current_embed.description) + len(entry) > 500:
                embeds.append(current_embed)

                current_embed = discord.Embed(title="Your Reminders", colour=config.EMBED_COLOUR)
                current_embed.description = entry
            else:
                current_embed.description += entry

            count += 1

        embeds.append(current_embed)

        if len(embeds) == 1:
            await ctx.reply(embed=embeds[0], mention_author=False)
            return

        await ctx.reply(
            embed=embeds[0], view=lyviews.PaginatorView(ctx.author, embeds), mention_author=False
        )

    @reminder.command(
        name="delete", description="Delete a reminder by its ID.", usage="c617671342a58aeef597f911"
    )
    @lychecks.is_user_app()
    async def reminder_delete(self, ctx: commands.Context, reminder_id: str):
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
        now = datetime.now(timezone.utc)

        reminders = await database.get_all(models.ReminderModel)

        for reminder in reminders:
            remind_at = reminder.remind_at

            if remind_at.tzinfo is None:
                remind_at = remind_at.replace(tzinfo=timezone.utc)

            if remind_at > now:
                continue

            user = self._bot.get_user(reminder.user_id)

            if user is None:
                try:
                    user = await self._bot.fetch_user(reminder.user_id)
                except discord.NotFound:
                    await database.delete(reminder)
                    continue

            try:
                embed = discord.Embed(colour=config.EMBED_COLOUR)
                embed.description = (
                    f"{await lyhelpers.fetch_random_emoji()} **Reminder**: {reminder.reminder}"
                )

                await user.send(embed=embed)
            except discord.Forbidden:
                pass
            finally:
                await database.delete(reminder)

    @_check_reminders.before_loop
    async def _before_check_reminders(self):
        await self._bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
