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
                description="Only Takina's maintainers can run this command.",
                color=nextcord.Color.red(),
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.UserInputError):
            embed = nextcord.Embed(
                title="Error",
                description="User input error. Please double check your command and ensure you are entering it correctly.",
                color=nextcord.Color.red(),
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.CommandNotFound):
            embed = nextcord.Embed(
                title="Error",
                description="This command does not exist. Type `a?help` for a full list of commands.",
                color=nextcord.Color.red(),
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.errors.DisabledCommand):
            embed = nextcord.Embed(
                title="Error",
                description="This command has been disabled by Takina's maintainers.",
                color=nextcord.Color.red(),
            )
            await context.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="Error",
                description="An error was caught while processing your command.",
                color=nextcord.Color.red(),
            )
            await context.send(embed=embed)

    @commands.Cog.listener()
    async def on_application_command_error(
        self, interaction: nextcord.Interaction, error: Exception
    ):
        if isinstance(error, application_checks.errors.ApplicationMissingRole):
            embed = nextcord.Embed(
                title="Error",
                description="You must be a staff member to run this command.",
                color=nextcord.Color.red(),
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        
        error = getattr(error, "original", error)
        if isinstance(error, application_checks.errors.ApplicationNotOwner):
            embed = nextcord.Embed(
                title="Error",
                description="Only Takina's maintainers can run this command.",
                color=nextcord.Color.red(),
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        else:
            embed = nextcord.Embed(
                title="Error",
                description="An unexpected error occurred while processing your command.",
                color=nextcord.Color.red(),
            )
            await interaction.send(embed=embed, ephemeral=True)
            self.bot.logger.error(
                f"An error occurred while processing an application command: {error}"
            )
            raise error


def setup(bot: Bot):
    bot.add_cog(Errors(bot))
