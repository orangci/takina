import nextcord
from nextcord.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from config import *
from bson.objectid import ObjectId
from ..libs.oclib import *


class RemindMe(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(MONGO_URI).get_database(DB_NAME)
        self.reminders = self.db.reminders
        self.check_reminders.start()

    @commands.command(help="Deprecated alias of `reminder set`.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def remindme(self, ctx: commands.Context):
        embed = nextcord.Embed(
            description=f":x: The `remindme` alias has been deprecated. Use `reminder set` instead.",
            color=ERROR_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.group(
        name="reminder",
        invoke_without_command=True,
        help="Manage your reminders. Use `reminder set`, `reminder list`, or `reminder delete`.",
    )
    async def reminder(self, ctx: commands.Context):
        embed = nextcord.Embed(
            description="No subcommand specified. Usage: `reminder set`, `reminder list`, or `reminder delete`.",
            color=ERROR_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @reminder.command(
        name="set",
        help="Set a reminder. Minimum duration is 10 minutes. Usage: `reminder set <time> <reminder>`.",
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def reminder_set(self, ctx: commands.Context, time: str, *, reminder: str):
        user_id = ctx.author.id
        remind_time = self.parse_time(time)

        if remind_time is None:
            embed = nextcord.Embed(
                description="Invalid time format. Use <number>[m|h|d].",
                color=ERROR_COLOR,
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        remind_at = datetime.datetime.now(datetime.UTC) + remind_time
        result = await self.reminders.insert_one(
            {
                "user_id": user_id,
                "reminder": reminder,
                "remind_at": remind_at,
            }
        )

        embed = nextcord.Embed(
            description=f"{await fetch_random_emoji()} Reminder set for {time} from now: **{reminder}**\n-# ID: `{result.inserted_id}`",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @reminder.command(name="list", help="List all your active reminders.")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def reminder_list(self, ctx: commands.Context):
        user_id = ctx.author.id
        reminders = self.reminders.find({"user_id": user_id}).sort("remind_at", 1)

        embed = nextcord.Embed(title="Your Reminders", color=EMBED_COLOR)
        embed.description = ""

        count = 0
        async for reminder in reminders:
            count += 1
            remind_time = reminder["remind_at"].strftime("%B %d, %Y at %H:%M UTC")
            embed.description += f"\n\n> **ID**: `{reminder['_id']}`"
            embed.description += f"\n> **Reminder:** {reminder['reminder']}"
            embed.description += f"\n> **Reminder time:** {remind_time}"

        if count == 0:
            embed.title = None
            embed.description = ":x: You have no active reminders."
            embed.color = ERROR_COLOR

        await ctx.reply(embed=embed, mention_author=False)

    @reminder.command(
        name="delete",
        help="Delete a reminder by its ID. Usage: `reminder delete <reminder ID>`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def reminder_delete(self, ctx: commands.Context, reminder_id: str):
        user_id = ctx.author.id

        try:
            object_id = ObjectId(reminder_id)
        except Exception:
            embed = nextcord.Embed(
                description="❌ Invalid reminder ID format.",
                color=ERROR_COLOR,
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        result = await self.reminders.delete_one({"_id": object_id, "user_id": user_id})
        if result.deleted_count == 0:
            embed = nextcord.Embed(
                description="❌ No reminder found with that ID.",
                color=ERROR_COLOR,
            )
        else:
            embed = nextcord.Embed(
                description=f"✅ Reminder with ID `{reminder_id}` has been deleted.",
                color=EMBED_COLOR,
            )
        await ctx.reply(embed=embed, mention_author=False)

    # slash commands
    @nextcord.slash_command(
        name="reminder", description="Reminder management commands."
    )
    async def slash_reminder(self, interaction: nextcord.Interaction):
        pass

    @slash_reminder.subcommand(
        name="set",
        description="Set a reminder for yourself.",
    )
    async def slash_reminder_set(
        self, interaction: nextcord.Interaction, time: str, *, reminder: str
    ):
        user_id = interaction.user.id
        remind_time = self.parse_time(time)

        if remind_time is None:
            embed = nextcord.Embed(
                description="Invalid time format. Use <number>[m|h|d].",
                color=ERROR_COLOR,
            )
            await interaction.send(embed=embed, ephemeral=True)
            return

        remind_at = datetime.datetime.now(datetime.UTC) + remind_time
        result = await self.reminders.insert_one(
            {
                "user_id": user_id,
                "reminder": reminder,
                "remind_at": remind_at,
            }
        )

        embed = nextcord.Embed(
            description=f"{await fetch_random_emoji()} Reminder set for {time} from now: **{reminder}**\n-# ID: `{result.inserted_id}`",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=False)

    @slash_reminder.subcommand(
        name="list", description="List all your active reminders."
    )
    async def slash_reminder_list(self, interaction: nextcord.Interaction):
        user_id = interaction.user.id
        reminders = self.reminders.find({"user_id": user_id}).sort("remind_at", 1)

        embed = nextcord.Embed(title="Your Reminders", color=EMBED_COLOR)
        embed.description = ""

        count = 0
        async for reminder in reminders:
            count += 1
            remind_time = reminder["remind_at"].strftime("%B %d, %Y at %H:%M UTC")
            embed.description += f"\n\n> **ID**: `{reminder['_id']}`"
            embed.description += f"\n> **Reminder:** {reminder['reminder']}"
            embed.description += f"\n> **Reminder time:** {remind_time}"

        if count == 0:
            embed.title = None
            embed.description = ":x: You have no active reminders."
            embed.color = ERROR_COLOR

        await interaction.send(embed=embed, ephemeral=True)

    @slash_reminder.subcommand(
        name="delete", description="Delete a reminder by its ID."
    )
    async def slash_reminder_delete(
        self, interaction: nextcord.Interaction, reminder_id: str
    ):
        user_id = interaction.user.id

        try:
            object_id = ObjectId(reminder_id)
        except Exception:
            embed = nextcord.Embed(
                description="❌ Invalid reminder ID format.",
                color=ERROR_COLOR,
            )
            await interaction.send(embed=embed, ephemeral=True)
            return

        result = await self.reminders.delete_one({"_id": object_id, "user_id": user_id})
        if result.deleted_count == 0:
            embed = nextcord.Embed(
                description="❌ No reminder found with that ID.",
                color=ERROR_COLOR,
            )
        else:
            embed = nextcord.Embed(
                description=f"✅ Reminder with ID `{reminder_id}` has been deleted.",
                color=EMBED_COLOR,
            )
        await interaction.send(embed=embed, ephemeral=True)

    @tasks.loop(seconds=600)
    async def check_reminders(self):
        now = datetime.datetime.now(datetime.UTC)
        reminders_to_send = self.reminders.find({"remind_at": {"$lte": now}})

        async for reminder in reminders_to_send:
            user = self.bot.get_user(reminder["user_id"])
            if user:
                try:
                    embed = nextcord.Embed(
                        description=f"⏰ Reminder: **{reminder['reminder']}**",
                        color=EMBED_COLOR,
                    )
                    await user.send(embed=embed)
                except nextcord.Forbidden:
                    pass
            await self.reminders.delete_one({"_id": reminder["_id"]})

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

    def parse_time(self, time_str: str) -> timedelta:
        units = {"m": "minutes", "h": "hours", "d": "days"}
        if time_str[-1] not in units:
            return None

        try:
            amount = int(time_str[:-1])
            return timedelta(**{units[time_str[-1]]: amount})
        except ValueError:
            return None


def setup(bot):
    bot.add_cog(RemindMe(bot))
