from takina.libs import lychecks
from discord.ext import commands
from takina import config
import discord


class EmbedBuilder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @discord.app_commands.command(name="embed", description="Create an embed.")
    @lychecks.has_permissions(manage_channels=True)
    async def embed_command(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EmbedModal())


class EmbedModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Embed Builder")

        self.title_input = discord.ui.TextInput(
            label="Title", placeholder="Enter embed title", required=False
        )
        self.description_input = discord.ui.TextInput(
            label="Description",
            placeholder="Enter embed description",
            style=discord.TextStyle.paragraph,
        )
        self.color_input = discord.ui.TextInput(
            label="Color (Hex)", placeholder="#FFFFFF", required=False
        )
        self.footer_input = discord.ui.TextInput(
            label="Footer", placeholder="Enter footer text", required=False
        )
        self.fields_input = discord.ui.TextInput(
            label="Fields (key:value; key:value)",
            placeholder=("Enter fields in key:value format, separated by semicolons"),
            required=False,
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.color_input)
        self.add_item(self.footer_input)
        self.add_item(self.fields_input)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(color=config.EMBED_COLOR)
        embed.title = self.title_input.value or None
        embed.description = self.description_input.value or None

        if self.color_input.value:
            try:
                embed.color = int(self.color_input.value.lstrip("#"), 16)
            except ValueError:
                return

        if self.footer_input.value:
            embed.set_footer(text=self.footer_input.value)

        if self.fields_input.value:
            for field in self.fields_input.value.split(";"):
                if ":" not in field:
                    continue

                name, value = field.split(":", 1)
                embed.add_field(name=name.strip(), value=value.strip(), inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EmbedBuilder(bot))
