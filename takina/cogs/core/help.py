# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors, lyviews, lyhelpers
from collections.abc import Mapping
from discord.ext import commands
from takina import config
import discord


class Help(commands.HelpCommand):
    def get_command_signature(self, command: commands.Command) -> str:
        signature = f"**{self.context.clean_prefix}{command.qualified_name}**"

        if command.signature:
            signature += f" {command.signature}"

        return signature

    async def send_bot_help(self, mapping: Mapping, /) -> None:
        lines: list[str] = []

        for _, cog_commands in mapping.items():
            filtered = await self.filter_commands(cog_commands, sort=True)

            for command in filtered:
                lines.append(
                    f"> **{command.qualified_name}**: {command.description or 'No description.'}"
                )

        if not lines:
            embed = discord.Embed(colour=config.ERROR_COLOUR)
            embed.description = f"{config.emojis.ERROR} No commands were found."
            return await self.get_destination().send(embed=embed)

        embeds: list[discord.Embed] = []

        for page, chunk in enumerate(lyhelpers.chunked(lines, 10), start=1):
            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.description = "\n".join(chunk)
            embed.set_footer(text=f"Page {page} of {(len(lines) + 9) // 10}")

            embeds.append(embed)

        view = lyviews.PaginatorView(self.context.author, embeds)
        view.message = await self.get_destination().send(embed=embeds[0], view=view)

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(colour=config.EMBED_COLOUR)

        description = []

        if command.description:
            description.append(command.description)
            description.append("")

        description.append(
            f"> **Command**: {self.context.clean_prefix}{command.qualified_name} {command.signature}"
        )

        if command.aliases:
            description.append(f"> **Aliases**: {', '.join(command.aliases)}")

        embed.description = "\n".join(description)

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        embed = discord.Embed(colour=config.EMBED_COLOUR)

        description = []

        if group.description:
            description.append(group.description)
            description.append("")

        description.append(
            f"> **Command**: {self.context.clean_prefix}{group.qualified_name} {group.signature}"
        )

        if group.aliases:
            description.append(f"> **Aliases**: {', '.join(group.aliases)}")

        filtered = await self.filter_commands(group.commands, sort=True)
        if not filtered:
            raise lyerrors.TakinaNotFoundError("That command does not exist.")

        if filtered:
            description.append("")
            description.append("**Subcommands**")

            for command in filtered:
                description.append(f"> {self.get_command_signature(command)}")

        embed.description = "\n".join(description)

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        if not filtered:
            raise lyerrors.TakinaNotFoundError("That command does not exist.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)

        embed.description = "\n".join(
            f"> {self.get_command_signature(command)}" for command in filtered
        )

        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error: str, /):
        raise lyerrors.TakinaError(error)

    def subcommand_not_found(self, command: commands.Command, string: str, /) -> str:
        return "That subcommand does not exist."

    def command_not_found(self, string: str, /) -> str:
        return "That command does not exist."


async def setup(bot: commands.Bot):
    bot.help_command = Help()
