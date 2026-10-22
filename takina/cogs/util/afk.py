# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina import config, database, models
from takina.libs import lychecks, lyhelpers
from discord.ext import commands
from sqlmodel import col
import discord

# beyond this, a mass ping would turn into a wall of afk notices
MAX_LISTED_AFK = 5


class AFK(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.hybrid_command(
        description=f"Toggle AFK status. When AFK, {config.BOT_NAME} will notify others if they mention you, in any server.",
        usage="reading a book",
    )
    @lychecks.is_user_app()
    async def afk(self, ctx: commands.Context, *, status: str = "AFK"):
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        emoji = await lyhelpers.fetch_random_emoji()
        current_status = await database.get(models.AFKStatusModel, user_id=ctx.author.id)

        if current_status:
            await database.delete(current_status)
            embed.description = f"{emoji}{ctx.author.mention} is no longer AFK."
        else:
            await database.save(models.AFKStatusModel(user_id=ctx.author.id, status=status))
            embed.description = f"{emoji}{ctx.author.mention} is now AFK: {status}"

        await ctx.reply(embed=embed, mention_author=False)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # the afk command handles its own message; clearing here would undo it straight away
        if (await self._bot.get_context(message)).valid:
            return

        # check if the author is AFK and remove if so
        current_status = await database.get(models.AFKStatusModel, user_id=message.author.id)
        if current_status:
            await database.delete(current_status)
            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.description = (
                f"{await lyhelpers.fetch_random_emoji()}{message.author.mention} is no longer AFK."
            )
            await message.channel.send(embed=embed, delete_after=5)

        mentioned_ids = {
            user.id for user in message.mentions if not user.bot and user != message.author
        }
        if not mentioned_ids:
            return

        afk_statuses = await database.get_all(
            models.AFKStatusModel, where=[col(models.AFKStatusModel.user_id).in_(mentioned_ids)]
        )
        if not afk_statuses:
            return

        emoji = await lyhelpers.fetch_random_emoji()
        lines = [
            f"{emoji}<@{afk.user_id}> is currently AFK: {afk.status}"
            for afk in afk_statuses[:MAX_LISTED_AFK]
        ]
        if len(afk_statuses) > MAX_LISTED_AFK:
            lines.append(f"…and {len(afk_statuses) - MAX_LISTED_AFK} more.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = "\n".join(lines)
        await message.channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())


async def setup(bot: commands.Bot):
    await bot.add_cog(AFK(bot))
