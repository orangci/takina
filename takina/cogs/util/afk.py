from takina.libs import lychecks, lyhelpers
from sqlmodel import Field, SQLModel
from takina import config, database
from sqlalchemy import BigInteger
from discord.ext import commands
import discord


class AFKStatusModel(SQLModel, table=True):
    __tablename__: str = "afk_statuses"
    __table_args__ = {"extend_existing": True}

    user_id: int = Field(sa_type=BigInteger, primary_key=True)
    status: str


class AFK(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @lychecks.is_user_app()
    @commands.hybrid_command(
        description=f"Toggle AFK status. When AFK, {config.BOT_NAME} will notify others if they mention you.",
        usage="reading a book",
    )
    async def afk(self, ctx: commands.Context, *, status: str = "AFK"):
        embed = discord.Embed(color=config.EMBED_COLOR)
        current_status = await database.get(AFKStatusModel, user_id=ctx.author.id)

        if current_status:
            await database.delete(current_status)
            return
        else:
            new_status = AFKStatusModel(user_id=ctx.author.id, status=status)
            await database.save(new_status)
            embed.description = f"{await lyhelpers.fetch_random_emoji()}{ctx.author.mention} is now AFK: {status}"

        await ctx.reply(embed=embed, mention_author=False)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # check if the author is AFK and remove if so
        current_status = await database.get(AFKStatusModel, user_id=message.author.id)
        if current_status:
            await database.delete(current_status)
            embed = discord.Embed(color=config.EMBED_COLOR)
            embed.description = f"{await lyhelpers.fetch_random_emoji()}{message.author.mention} is no longer AFK."
            await message.channel.send(embed=embed, delete_after=5)

        # notify mentions about AFK users
        for user in message.mentions:
            afk_status = await database.get(AFKStatusModel, user_id=user.id)
            if afk_status:
                embed = discord.Embed(color=config.EMBED_COLOR)
                embed.description = f"{await lyhelpers.fetch_random_emoji()}{user.mention} is currently AFK: {afk_status.status}"
                await message.channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AFK(bot))
