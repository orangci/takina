from nextcord.ext import commands
from nextcord import ui
import nextcord
import config


def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


class HelpView(ui.View):
    def __init__(self, embeds: list[nextcord.Embed], author: nextcord.User):
        super().__init__(timeout=60)
        self.embeds = embeds
        self.author = author
        self.page = 0

    async def update_message(self, interaction: nextcord.Interaction):
        self.children[0].disabled = self.page == 0
        self.children[1].disabled = self.page == len(self.embeds) - 1
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @ui.button(label="Previous", style=nextcord.ButtonStyle.secondary)
    async def previous(self, button: ui.Button, interaction: nextcord.Interaction):
        if interaction.user != self.author:
            embed = nextcord.Embed(color=config.ERROR_COLOR, description=":x: You can't interact with this embed.")
            return await interaction.send(embed=embed, ephemeral=True)
        self.page -= 1
        await self.update_message(interaction)

    @ui.button(label="Next", style=nextcord.ButtonStyle.primary)
    async def next(self, button: ui.Button, interaction: nextcord.Interaction):
        if interaction.user != self.author:
            embed = nextcord.Embed(color=config.ERROR_COLOR, description=":x: You can't interact with this embed.")
            return await interaction.send(embed=embed, ephemeral=True)
        self.page += 1
        await self.update_message(interaction)


class Help(commands.HelpCommand):
    def get_command_signature(self, command: commands.Command):
        return (
            f"**{self.context.clean_prefix}{command.qualified_name}**"
            + (f" {command.signature}" if command.signature else "")
            + (f": {command.help}" if command.help else "")
        )

    async def send_bot_help(self, mapping: dict[commands.Cog | None, list[commands.Command]]):
        lines = []
        for cog, cog_commands in mapping.items():
            filtered = await self.filter_commands(cog_commands, sort=True)
            for command in filtered:
                help_text = command.help or "No description."
                lines.append(f"> **{command.name}**: {help_text}")

        if not lines:
            error_embed = nextcord.Embed(color=config.ERROR_COLOR, description=":x: No command found.")
            return await self.get_destination().send(embed=error_embed)

        chunks = list(chunked(lines, 10))
        total_pages = len(chunks)
        embed_pages = []

        for i, chunk in enumerate(chunks):
            embed = nextcord.Embed(color=config.EMBED_COLOR)
            embed.description = "\n".join(chunk)
            embed.set_footer(text=f"Page {i + 1} of {total_pages}")
            embed_pages.append(embed)

        view = HelpView(embed_pages, self.context.author)
        await self.get_destination().send(embed=embed_pages[0], view=view)

    async def send_command_help(self, command: commands.Command):
        embed = nextcord.Embed(color=config.EMBED_COLOR, description="")
        if command.help:
            embed.description += command.help + "\n\n"

        embed.description += f"> **Command**: {self.context.clean_prefix + command.qualified_name} {command.signature}"
        if command.aliases:
            embed.description += f"\n> **Aliases**: {', '.join(command.aliases)}"

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        embed = nextcord.Embed(color=config.EMBED_COLOR, description="")
        if group.help:
            embed.description += group.help + "\n\n"

        embed.description += f"> **Command**: {self.context.clean_prefix + group.qualified_name} {group.signature}"
        if group.aliases:
            embed.description += f"\n> **Aliases**: {', '.join(group.aliases)}"

        filtered = await self.filter_commands(group.commands, sort=True)
        if filtered:
            subcommands = "\n".join([f"> {self.get_command_signature(c)}" for c in filtered])
            embed.description += "\n\n**Subcommands**:\n" + subcommands

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        filtered = await self.filter_commands(cog.get_commands(), sort=True)

        if filtered:
            embed.description = "\n".join([f"> {self.get_command_signature(c)}" for c in filtered])

        await self.get_destination().send(embed=embed)

    """
    async def command_not_found(self, command: str):
        embed = nextcord.Embed(color=config.ERROR_COLOR)
        embed.description = f":x: Command `{command}` not found."
        await self.get_destination().send(embed=embed)

    async def subcommand_not_found(self, command, subcommand: str):
        embed = nextcord.Embed(color=config.ERROR_COLOR)
        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            embed.description = f':x: Command "{command.qualified_name}" has no subcommand named `{subcommand}`.'
        embed.description = f':x: Command "{command.qualified_name}" has no subcommands.'
        await self.get_destination().send(embed=embed)
    """


def setup(bot):
    bot.help_command = Help()
