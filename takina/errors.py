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
        if isinstance(error, commands.NotOwner):
            embed = nextcord.Embed(
                title="Error",
                description=f"Only Anna's maintainers can run this command..",
                color=nextcord.Color.red(),
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.UserInputError):
            embed = nextcord.Embed(
                title="Error",
                description=f"User input error. Please double check your command and ensure you are entering it correctly.",
                color=nextcord.Color.red(),
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.CommandNotFound):
            embed = nextcord.Embed(
                title="Error",
                description=f"This command does not exist. Type `a?help` for a full list of commands.",
                color=nextcord.Color.red(),
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.errors.DisabledCommand):
            embed = nextcord.Embed(
                title="Error",
                description=f"This command has been disabled by Anna's maintainers.",
                color=nextcord.Color.red(),
            )
            await context.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="Error",
                description=f"An error was caught while processing your command.",
                color=nextcord.Color.red(),
            )
            await context.send(embed=embed)
            await super().on_command_error(context, error)

    async def on_application_command_error(
        self, interaction: nextcord.Interaction, error: Exception
    ):
        if isinstance(exception, ac.ApplicationMissingRole):
            embed = nextcord.Embed(
                title="Error",
                description=f"You must be a staff member to run this command.",
                color=nextcord.Color.red(),
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        error = getattr(error, "original", error)
        if isinstance(error, application_checks.errors.ApplicationNotOwner):
            embed = nextcord.Embed(
                title="Error",
                description="Only Anna's maintainers can run this command..",
                color=nextcord.Color.red(),
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        else:
            embed = nextcord.Embed(
                title="Error",
                description=f"An unexpected error occurred while processing your command.",
                color=nextcord.Color.red(),
            )
            await interaction.send(embed=embed, ephemeral=True)
            self.bot.logger.error(
                f"An error occurred while processing an application command: {error}"
            )
            raise error


def setup(bot: Bot):
    bot.add_cog(Errors(bot))
