# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import nextcord
from nextcord.ext import commands, application_checks
from config import *


class EmbedBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="embed", description="Create an embed.")
    @application_checks.has_permissions(manage_channels=True)
    async def embed_command(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        modal = EmbedModal()
        await interaction.response.send_modal(modal)


class EmbedModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(title="Embed Builder")

        self.title_input = nextcord.ui.TextInput(
            label="Title", placeholder="Enter embed title", required=False
        )
        self.description_input = nextcord.ui.TextInput(
            label="Description",
            placeholder="Enter embed description",
            style=nextcord.TextInputStyle.paragraph,
        )
        self.color_input = nextcord.ui.TextInput(
            label="Color (Hex)", placeholder="#FFFFFF", required=False
        )
        self.footer_input = nextcord.ui.TextInput(
            label="Footer", placeholder="Enter footer text", required=False
        )
        self.fields_input = nextcord.ui.TextInput(
            label="Fields (key:value; key:value)",
            placeholder="Enter fields in key:value format, separated by semicolons",
            required=False,
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.color_input)
        self.add_item(self.footer_input)
        self.add_item(self.fields_input)

    async def callback(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title=self.title_input.value,
            description=self.description_input.value,
            color=(
                int(self.color_input.value.lstrip("#"), 16)
                if self.color_input.value.startswith("#")
                else EMBED_COLOR
            ),
        )

        if self.footer_input.value:
            embed.set_footer(text=self.footer_input.value)

        # Process fields
        if self.fields_input.value:
            fields = self.fields_input.value.split(";")
            for field in fields:
                if ":" in field:
                    key, value = field.split(":", 1)
                    embed.add_field(name=key.strip(), value=value.strip(), inline=False)

        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(EmbedBuilder(bot))
