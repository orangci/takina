from sqlmodel import Field, SQLModel
from sqlalchemy import BigInteger
from discord.ext import commands
from takina.libs import lychecks


class UserSettingsModel(SQLModel, table=True):
    __tablename__ = "user_settings"
    user_id: int = Field(sa_type=BigInteger, primary_key=True)


class GuildSettingsModel(SQLModel, table=True):
    __tablename__ = "guild_settings"
    guild_id: int = Field(sa_type=BigInteger, primary_key=True)


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(
        name="settings", description="Configure Takina.", invoke_without_command=True
    )
    async def settings(self, ctx: commands.Context):
        pass

    @commands.guild_only()
    @lychecks.has_permissions(administrator=True)
    @settings.command(
        name="guild", aliases=["server"], description="Manage settings for this server."
    )
    async def guild_settings(self, ctx: commands.Context):
        pass

    @lychecks.is_user_app()
    @settings.command(name="user", description="Manage user settings.")
    async def user_settings(self, ctx: commands.Context):
        pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot))
