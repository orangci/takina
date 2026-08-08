from takina.libs import lyerrors
from discord.ext import commands
from takina import config
import logging
import discord
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

        # ignore these two
        if isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.CheckFailure) and not isinstance(
            error, lyerrors.TakinaError
        ):
            return

        if isinstance(error, commands.DisabledCommand):
            error = lyerrors.TakinaDisabledError(
                "This command has been disabled by Takina's maintainers (`/maintainers`)."
            )

        elif isinstance(error, commands.NotOwner):
            error = lyerrors.TakinaMaintainerOnlyError(
                "This command is restricted to Takina's maintainers (`/maintainers`)."
            )

        elif str(error) in {"That command does not exist.", "That subcommand does not exist."}:
            error = lyerrors.TakinaNotFoundError(str(error))

        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(perm.replace("_", " ").title() for perm in error.missing_permissions)
            raise lyerrors.TakinaBotPermissionError(
                f"I am missing the following permissions required to use this command: `{perms}`."
            )

        elif isinstance(error, commands.MissingPermissions):
            print("asdf")
            perms = ", ".join(perm.replace("_", " ").title() for perm in error.missing_permissions)
            error = lyerrors.TakinaPermissionError(
                f"You are missing the following permissions required to use this command: {perms}"
            )

        elif isinstance(error, commands.MissingRequiredArgument):
            error = lyerrors.TakinaUserInputError(
                f"Missing required argument: `{error.param.name}`."
            )

        elif isinstance(error, commands.BadArgument):
            error = lyerrors.TakinaUserInputError("One or more arguments provided are invalid.")

        elif not isinstance(error, lyerrors.TakinaError):
            if not DEBUG:
                self.logger.exception("Unhandled command exception", exc_info=error)
            error = lyerrors.TakinaError(
                "Unexpected Error: An unexpected error occurred. Please report this issue if it persists."
            )

        if isinstance(error, lyerrors.TakinaError):
            embed = discord.Embed(color=config.ERROR_COLOR)
            if error.message:
                embed.description = f"{config.emojis.ERROR} {error.message}"
            else:
                embed.description = f"{config.emojis.ERROR} {error.error_name}"

            if ctx.interaction:
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.reply(embed=embed, mention_author=False)
            return

        if isinstance(error, lyerrors.TakinaMissingEnvironmentVariableError):
            print(error.message)
            return


async def setup(bot: commands.Bot):
    await bot.add_cog(Errors(bot))
