# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors
from discord.ext import commands
from takina import config
import logging
import discord
import aiohttp
import os

DEBUG = os.getenv("TAKINA_DEBUG") == "1"


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self.logger = logging.getLogger("takina.errors")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if DEBUG:
            self.logger.exception("Unhandled command exception", exc_info=error)

        error = getattr(error, "original", error)

        if isinstance(error, commands.CommandNotFound):
            return

        # discord.py's permission and owner checks are check failures too, but they deserve a message
        if isinstance(error, commands.CheckFailure) and not isinstance(
            error,
            (
                lyerrors.TakinaError,
                commands.MissingPermissions,
                commands.BotMissingPermissions,
                commands.NotOwner,
            ),
        ):
            # prefix commands fail quietly, but an unanswered interaction says it did not respond
            if ctx.interaction is None:
                return

            error = lyerrors.TakinaUserInputError("This command is not available here.")

        if isinstance(error, commands.CommandOnCooldown):
            await self.notify_cooldown(ctx, error)
            return

        if isinstance(error, commands.DisabledCommand):
            error = lyerrors.TakinaDisabledError(
                "This command has been disabled by Takina's maintainers (`/maintainers`)."
            )

        elif isinstance(error, commands.NotOwner):
            error = lyerrors.TakinaMaintainerOnlyError(
                "This command is restricted to Takina's maintainers (`/maintainers`)."
            )

        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(perm.replace("_", " ").title() for perm in error.missing_permissions)
            error = lyerrors.TakinaBotPermissionError(
                f"I am missing the following permissions required to use this command: {perms}."
            )

        elif isinstance(error, discord.Forbidden):
            error = lyerrors.TakinaBotPermissionError(
                "I do not have the sufficient permissions required to perform this action."
            )

        elif isinstance(error, commands.MissingPermissions):
            perms = ", ".join(perm.replace("_", " ").title() for perm in error.missing_permissions)
            error = lyerrors.TakinaPermissionError(
                f"You are missing the following permissions required to use this command: {perms}."
            )

        elif isinstance(error, commands.MissingRequiredArgument):
            error = lyerrors.TakinaUserInputError(
                f"Missing required argument: `{error.param.name}`."
            )

        elif isinstance(error, commands.UserInputError):
            # discord.py words these for users already, e.g. 'Member "Cirno" not found.'
            error = lyerrors.TakinaUserInputError(str(error))

        elif isinstance(error, TimeoutError):
            error = lyerrors.TakinaError(
                "The service took too long to respond. Please try again later."
            )

        elif not isinstance(error, lyerrors.TakinaError):
            # if *not* because if *yes* is handled earlier in this file
            if not DEBUG:
                self.logger.exception("Unhandled command exception", exc_info=error)
            if isinstance(error, aiohttp.ClientResponseError):
                error = lyerrors.TakinaError(
                    f"Error [{error.status}](https://http.cat/{error.status}.png): {error.message}."
                )
            else:
                # the details are in the log; users only need to know it was not their fault
                error = lyerrors.TakinaError(
                    "Something went wrong on our end. It has been logged; please report it if it keeps happening."
                )

        if isinstance(error, lyerrors.TakinaError):
            embed = discord.Embed(colour=config.ERROR_COLOUR)
            if error.message:
                embed.description = f"{config.emojis.ERROR} {error.message}"
            else:
                embed.description = f"{config.emojis.ERROR} {error.error_name}"

            if ctx.interaction:
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.reply(embed=embed, mention_author=False)
            return

    async def notify_cooldown(
        self, ctx: commands.Context, error: commands.CommandOnCooldown
    ) -> None:
        if ctx.interaction:
            embed = discord.Embed(colour=config.ERROR_COLOUR)
            embed.description = f"⏳ Slow down! Try again in {error.retry_after:.1f}s."
            await ctx.send(embed=embed, ephemeral=True)
            return

        # a reaction rather than a reply, so spamming a prefix command doesn't spam the channel
        try:
            await ctx.message.add_reaction("⏳")
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Errors(bot))
