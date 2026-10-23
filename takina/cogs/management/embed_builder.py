# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from discord import app_commands
from discord.ext import commands
from takina import config
import logging
import discord

logger = logging.getLogger("takina.embed_builder")

MAX_FIELDS = 25


class EmbedBuilder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @app_commands.command(name="embed", description="Create an embed.")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.guild_only()
    async def embed_command(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EmbedModal())


async def send_error(interaction: discord.Interaction, description: str) -> None:
    embed = discord.Embed(colour=config.EMBED_COLOUR)
    embed.description = f"{config.emojis.ERROR} {description}"
    await interaction.response.send_message(embed=embed, ephemeral=True)


class EmbedModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Embed Builder")

        # max_length mirrors discord's embed limits, so the modal refuses what an embed would
        self.title_input = discord.ui.TextInput(
            label="Title", placeholder="Enter embed title", required=False, max_length=256
        )
        self.description_input = discord.ui.TextInput(
            label="Description",
            placeholder="Enter embed description",
            style=discord.TextStyle.paragraph,
            max_length=4000,
        )
        self.colour_input = discord.ui.TextInput(
            label="Colour (Hex)", placeholder="#FFFFFF", required=False, max_length=7
        )
        self.footer_input = discord.ui.TextInput(
            label="Footer", placeholder="Enter footer text", required=False, max_length=2048
        )
        self.fields_input = discord.ui.TextInput(
            label="Fields (key:value; key:value)",
            placeholder="Enter fields in key:value format, separated by semicolons",
            style=discord.TextStyle.paragraph,
            required=False,
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.colour_input)
        self.add_item(self.footer_input)
        self.add_item(self.fields_input)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = self.title_input.value or None
        embed.description = self.description_input.value or None

        if colour := self.colour_input.value:
            try:
                embed.colour = discord.Colour.from_str(
                    colour if colour.startswith("#") else f"#{colour}"
                )
            except ValueError:
                await send_error(interaction, f"`{colour}` is not a hex colour, such as `#FFFFFF`.")
                return

        if self.footer_input.value:
            embed.set_footer(text=self.footer_input.value)

        fields = [field for field in self.fields_input.value.split(";") if ":" in field]
        if len(fields) > MAX_FIELDS:
            await send_error(interaction, f"An embed can hold at most {MAX_FIELDS} fields.")
            return

        for field in fields:
            name, value = (part.strip() for part in field.split(":", 1))
            if not name or not value or len(name) > 256 or len(value) > 1024:
                await send_error(
                    interaction,
                    "Each field needs a name of up to 256 characters and a value of up to 1,024.",
                )
                return

            embed.add_field(name=name, value=value, inline=False)

        if len(embed) > 6000:
            await send_error(interaction, "An embed can hold at most 6,000 characters in total.")
            return

        await interaction.response.send_message(embed=embed)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        # modals bypass core.errors, so without this a failure shows as "something went wrong"
        logger.exception("embed builder failed", exc_info=error)
        if not interaction.response.is_done():
            await send_error(interaction, "The embed could not be sent.")


async def setup(bot: commands.Bot):
    await bot.add_cog(EmbedBuilder(bot))
