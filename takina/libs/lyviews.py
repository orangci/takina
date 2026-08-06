from discord.ui import Button, View, Select
from takina import config
import discord


class AuthorView(View):
    """A view that can only be interacted with by the command invoker."""

    def __init__(self, author: discord.abc.User, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.author = author
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.author.id:
            return True

        embed = discord.Embed()
        embed.description = (
            f"{config.emojis.ERROR} You cannot interact with somebody else's message."
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, (Button, Select)):
                item.disabled = True

        if self.message is not None:
            await self.message.edit(view=self)


class ConfirmView(AuthorView):
    """Simple Yes / No confirmation dialog."""

    def __init__(self, author: discord.abc.User, *, timeout: float | None = 60):
        super().__init__(author, timeout=timeout)

        self.value: bool | None = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        self.value = True

        for child in self.children:
            if isinstance(child, (Button, Select)):
                child.disabled = True

        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        self.value = False

        for child in self.children:
            if isinstance(child, (Button, Select)):
                child.disabled = True

        await interaction.response.edit_message(view=self)
        self.stop()


class PaginatorView(AuthorView):
    """
    Very small embed paginator.

    Example:
        view = PaginatorView(ctx.author, embeds)
        view.message = await ctx.reply(embed=embeds[0], view=view)
    """

    def __init__(self, author: discord.abc.User, embeds: list[discord.Embed]):
        super().__init__(author)

        if not embeds:
            raise ValueError("PaginatorView requires at least one embed.")

        self.embeds = embeds
        self.page = 0

        self._update_buttons()

    def _update_buttons(self):
        self.previous.disabled = self.page == 0
        self.next.disabled = self.page == len(self.embeds) - 1

    @discord.ui.button(label="«", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: Button):
        self.page -= 1
        self._update_buttons()

        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @discord.ui.button(label="»", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: Button):
        self.page += 1
        self._update_buttons()

        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)
