from nextcord.ext import commands, application_checks
import nextcord
from __main__ import Bot


class Errors(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(
        self, context: commands.Context, error: commands.CommandError
    ) -> None:
        embed = nextcord.Embed(title="Error", color=nextcord.Color.red())
        detailed_description = "An error occurred while processing your command. Please see the details below:\n\n"

        if isinstance(error, commands.NotOwner):
            detailed_description += "You do not have the required permissions to execute this command. Only Takina's maintainers can run it."
            embed.add_field(name="Error Type:", value="Not Owner", inline=False)

        elif isinstance(error, commands.UserInputError):
            detailed_description += "There was an issue with your input. Please check your command syntax and ensure all required parameters are provided."
            embed.add_field(name="Error Type:", value="User Input Error", inline=False)

        elif isinstance(error, commands.CommandNotFound):
            detailed_description += "The command you entered does not exist. Please ensure you typed it correctly. Type `a?help` for a full list of commands."
            embed.add_field(name="Error Type:", value="Command Not Found", inline=False)

        elif isinstance(error, commands.errors.DisabledCommand):
            detailed_description += "This command has been disabled by Takina's maintainers. If you believe this is an error, please contact a staff member."
            embed.add_field(name="Error Type:", value="Disabled Command", inline=False)

        elif isinstance(error, nextcord.DiscordException):
            detailed_description += "A generic Discord exception occurred. Please try again or report this issue."
            embed.add_field(name="Error Type:", value="Discord Exception", inline=False)

        elif isinstance(error, nextcord.ClientException):
            detailed_description += "A client-related error occurred. This may be due to an invalid action or incorrect usage."
            embed.add_field(name="Error Type:", value="Client Exception", inline=False)

        elif isinstance(error, nextcord.LoginFailure):
            detailed_description += "Failed to log in. Please check your credentials and try again."
            embed.add_field(name="Error Type:", value="Login Failure", inline=False)

        elif isinstance(error, nextcord.NoMoreItems):
            detailed_description += "No more items to iterate over. Please check the operation and try again."
            embed.add_field(name="Error Type:", value="No More Items", inline=False)

        elif isinstance(error, nextcord.HTTPException):
            detailed_description += f"An HTTP error occurred: `{error.text}` (Status Code: {error.status})."
            embed.add_field(name="Error Type:", value="HTTP Exception", inline=False)

        elif isinstance(error, nextcord.Forbidden):
            detailed_description += "You do not have permission to perform this action. Please check your roles and permissions."
            embed.add_field(name="Error Type:", value="Forbidden", inline=False)

        elif isinstance(error, nextcord.NotFound):
            detailed_description += "The requested resource was not found. It may have been deleted or does not exist."
            embed.add_field(name="Error Type:", value="Not Found", inline=False)

        elif isinstance(error, nextcord.DiscordServerError):
            detailed_description += "A server error occurred on Discord's end. Please try again later."
            embed.add_field(name="Error Type:", value="Discord Server Error", inline=False)

        elif isinstance(error, nextcord.InvalidData):
            detailed_description += "Received invalid data from Discord. Please report this issue."
            embed.add_field(name="Error Type:", value="Invalid Data", inline=False)

        elif isinstance(error, nextcord.InvalidArgument):
            detailed_description += "An invalid argument was provided. Please check the command usage and try again."
            embed.add_field(name="Error Type:", value="Invalid Argument", inline=False)

        elif isinstance(error, nextcord.GatewayNotFound):
            detailed_description += "Could not find the gateway for Discord. Please check your connection and try again."
            embed.add_field(name="Error Type:", value="Gateway Not Found", inline=False)

        elif isinstance(error, nextcord.ConnectionClosed):
            detailed_description += "The connection to the gateway was closed. Reason: `{error.reason}` (Code: `{error.code}`)."
            embed.add_field(name="Error Type:", value="Connection Closed", inline=False)

        elif isinstance(error, nextcord.PrivilegedIntentsRequired):
            detailed_description += "Privileged intents are required for this command. Please ensure they are enabled in the Discord Developer Portal."
            embed.add_field(name="Error Type:", value="Privileged Intents Required", inline=False)

        elif isinstance(error, nextcord.InteractionResponded):
            detailed_description += "An interaction response was attempted after one had already been sent. Each interaction can only respond once."
            embed.add_field(name="Error Type:", value="Interaction Responded", inline=False)

        elif isinstance(error, nextcord.opus.OpusError):
            detailed_description += f"An Opus error occurred with code: `{error.code}`. Please check your audio configuration."
            embed.add_field(name="Error Type:", value="Opus Error", inline=False)

        elif isinstance(error, nextcord.opus.OpusNotLoaded):
            detailed_description += "Libopus is not loaded. Please ensure it is correctly set up."
            embed.add_field(name="Error Type:", value="Opus Not Loaded", inline=False)

        elif isinstance(error, nextcord.ApplicationError):
            detailed_description += "An application-level error occurred. This may relate to command usage."
            embed.add_field(name="Error Type:", value="Application Error", inline=False)

        elif isinstance(error, nextcord.ApplicationInvokeError):
            original_error = error.original if error.original else "Unknown error."
            detailed_description += f"An error occurred during command invocation: `{original_error}`."
            embed.add_field(name="Error Type:", value="Application Invoke Error", inline=False)

        elif isinstance(error, nextcord.ApplicationCheckFailure):
            detailed_description += "A prerequisite for this command was not met. Please ensure you meet all conditions to run it."
            embed.add_field(name="Error Type:", value="Application Check Failure", inline=False)

        elif isinstance(error, nextcord.ApplicationCommandOptionMissing):
            detailed_description += "A required option for the application command is missing. Please check the command parameters."
            embed.add_field(name="Error Type:", value="Command Option Missing", inline=False)

        else:
            detailed_description += "An unexpected error occurred. Please report this issue to a maintainer if it persists."
            embed.add_field(name="Error Type:", value="Unknown Error", inline=False)

        embed.description = detailed_description
        await context.send(embed=embed)

    @commands.Cog.listener()
    async def on_application_command_error(
        self, interaction: nextcord.Interaction, error: Exception
    ):
        embed = nextcord.Embed(title="Error", color=nextcord.Color.red())
        detailed_description = "An error occurred while processing your command. Please see the details below:\n\n"

        error = getattr(error, "original", error)

        if isinstance(error, application_checks.errors.ApplicationMissingRole):
            detailed_description += "You do not have the required role to execute this command. Please ensure you have the necessary permissions."
            embed.add_field(name="Error Type:", value="Missing Role", inline=False)

        elif isinstance(error, application_checks.errors.ApplicationNotOwner):
            detailed_description += "You do not have the required permissions to execute this command. Only Takina's maintainers can run it."
            embed.add_field(name="Error Type:", value="Not Owner", inline=False)

        else:
            detailed_description += "An unexpected error occurred while processing your command. Please contact Takina's maintainers if the issue persists."
            embed.add_field(name="Error Type:", value="Unknown Error", inline=False)

            self.bot.logger.error(
                f"An error occurred while processing an application command: {error}"
            )

        embed.description = detailed_description
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(Errors(bot))
