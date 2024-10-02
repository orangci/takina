from nextcord.ext import commands, application_checks
import nextcord
from __main__ import Bot, BOT_NAME
import logging


class Errors(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.logger = logging.getLogger("bot.errors")

        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter("%(levelname)s: %(name)s: %(message)s")
            )
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.ERROR)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        error_type = "Unknown Error"

        if isinstance(error, commands.NotOwner):
            description = f"You do not have sufficient permissions to run this command; command is restricted to {BOT_NAME}'s maintainers."
            error_type = "Maintainer Only Command"

        elif isinstance(error, commands.UserInputError) or isinstance(
            error, commands.BadArgument
        ):
            description = "It seems that you've made a mistake while entering the command. Please check your command syntax and ensure all required parameters are provided correctly. **Run `?help command` for information on how to correctly use a command.**"
            error_type = "User Input Error"

        elif isinstance(error, commands.CommandNotFound):
            description = "The command you entered does not exist. Please ensure you typed it correctly. Type `?help` for a full list of commands."
            error_type = "Command Not Found"

        elif isinstance(error, commands.errors.DisabledCommand):
            description = f"This command has been disabled by {BOT_NAME}'s maintainers. If you believe this is an error, please contact a maintainer."
            error_type = "Disabled Command"

        elif isinstance(error, nextcord.DiscordException):
            description = f"{str(error)}"
            error_type = "Discord Exception"

        elif isinstance(error, nextcord.Forbidden):
            description = (
                "You do not have sufficent permissions to perform this action."
            )
            error_type = "Forbidden"

        elif isinstance(error, nextcord.HTTPException):
            description = (
                f"An HTTP error occurred: `{error.text}` (Status Code: {error.status})."
            )
            error_type = "HTTP Exception"

        elif isinstance(error, nextcord.PrivilegedIntentsRequired):
            description = "Privileged intents are required for this command. Please ensure they are enabled in the Discord Developer Portal."
            error_type = "Privileged Intents Required"

        elif isinstance(error, commands.MissingPermissions):
            description = (
                "You do not have sufficent permissions to perform this action."
            )
            error_type = "Missing Permissions"

        else:
            description = "An unexpected error occurred. Please report this issue to a maintainer if it persists."
            error_type = "Unknown Error"

        embed = nextcord.Embed(title=error_type, color=nextcord.Color.red())
        embed.description = description
        await ctx.reply(embed=embed, mention_author=False)

        self.logger.error(f"Command error: {error_type} - {error}")
        self.logger.exception("Full error traceback:")

    @commands.Cog.listener()
    async def on_application_command_error(
        self, interaction: nextcord.Interaction, error: Exception
    ):
        error_type = "Unknown Error"
        error = getattr(error, "original", error)

        if isinstance(error, application_checks.errors.ApplicationMissingRole):
            description = (
                "You do not have the required role necessary to execute this command."
            )
            error_type = "Missing Role"

        elif isinstance(error, application_checks.errors.ApplicationNotOwner):
            description = f"You do not have sufficient permissions to run this command; command is restricted to {BOT_NAME}'s maintainers."
            error_type = "Maintainer Only Command"

        elif isinstance(error, application_checks.errors.ApplicationMissingPermissions):
            description = (
                "You do not have sufficent permissions to perform this action."
            )
            error_type = "Missing Permissions"

        elif isinstance(
            error, application_checks.errors.ApplicationBotMissingPermissions
        ):
            description = f"{BOT_NAME} does not have sufficent permissions to perform this action. Please report this error to {BOT_NAME}'s maintainers."
            error_type = "Bot Missing Permissions"

        else:
            description = f"An unexpected error occurred while processing your command. Please contact {BOT_NAME}'s maintainers if the issue persists."
            error_type = "Unknown Error"

        embed = nextcord.Embed(title=error_type, color=nextcord.Color.red())
        embed.description = description
        await interaction.send(embed=embed, ephemeral=True)

        self.logger.error(f"Application command error: {error_type} - {error}")
        self.logger.exception("Full error traceback:")


def setup(bot: Bot):
    bot.add_cog(Errors(bot))
