from discord.ext import commands
from takina.libs import lychecks


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

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
