# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks
from discord.ext import commands
from takina import config
import discord


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_group(
        name="settings", description="Configure Takina.", invoke_without_command=True
    )
    async def settings(self, ctx: commands.Context):
        await self.not_ready(ctx)

    @settings.command(
        name="guild", aliases=["server"], description="Manage settings for this server."
    )
    @lychecks.has_permissions(administrator=True)
    @lychecks.guild_only()
    async def guild_settings(self, ctx: commands.Context):
        await self.not_ready(ctx)

    @settings.command(name="user", description="Manage user settings.")
    @lychecks.is_user_app()
    async def user_settings(self, ctx: commands.Context):
        await self.not_ready(ctx)

    async def not_ready(self, ctx: commands.Context) -> None:
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.NOTE} Settings are not available yet. Stay tuned!"
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot))
