import nextcord
from nextcord.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timedelta
from __main__ import EMBED_COLOR


class RemindMe(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(os.getenv("MONGO")).get_database(
            os.getenv("DB_NAME")
        )
        self.reminders = self.db.reminders
        self.check_reminders.start()

    @commands.command(name="remindme")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def remindme(self, ctx: commands.Context, time: str, *, reminder: str):
        """Set a reminder. Usage: `remindme 10m eat lunch`"""
        user_id = ctx.author.id
        remind_time = self.parse_time(time)

        if remind_time is None:
            embed = nextcord.Embed(
                description="Invalid time format. Use <number>[s|m|h|d].)",
                color=0xFF0037,
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        remind_at = datetime.utcnow() + remind_time
        await self.reminders.insert_one(
            {
                "user_id": user_id,
                "reminder": reminder,
                "remind_at": remind_at,
            }
        )
        embed = nextcord.Embed(
            description=f"Reminder set for {time} from now: **{reminder}**",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @nextcord.slash_command(name="remindme")
    async def slash_remindme(
        self,
        interaction: nextcord.Interaction,
        time: str = nextcord.SlashOption(
            description="How long until you want the reminder to be sent", required=True
        ),
        *,
        reminder: str = nextcord.SlashOption(
            description="What you want to be reminded about", required=True
        ),
    ):
        """Set a reminder. Usage: `remindme 10m eat lunch`"""
        user_id = interaction.user.id
        remind_time = self.parse_time(time)

        if remind_time is None:
            embed = nextcord.Embed(
                description="Invalid time format. Use <number>[m|h|d|y].)",
                color=0xFF0037,
            )
            await interaction.send(embed=embed, ephemeral=True)
            return

        remind_at = datetime.utcnow() + remind_time
        await self.reminders.insert_one(
            {
                "user_id": user_id,
                "reminder": reminder,
                "remind_at": remind_at,
            }
        )

        embed = nextcord.Embed(
            description=f"Reminder set for {time} from now: **{reminder}**",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=True)

    def parse_time(self, time_str: str) -> timedelta:
        """Parses time string like '10m', '1h' to timedelta"""
        units = {"m": "minutes", "h": "hours", "d": "days"}
        if time_str[-1] not in units:
            return None

        try:
            amount = int(time_str[:-1])
            return timedelta(**{units[time_str[-1]]: amount})
        except ValueError:
            return None

    @tasks.loop(seconds=600)
    async def check_reminders(self):
        """Check the reminders collection every 600 seconds"""
        now = datetime.utcnow()
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


def setup(bot):
    bot.add_cog(RemindMe(bot))
