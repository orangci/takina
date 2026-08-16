# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from discord.ui import Button, View, Select
from discord.ext import commands
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
            f"{config.emojis.ERROR} You cannot interact with someone else's message."
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, (Button, Select)):
                item.disabled = True

        if self.message is not None:
            await self.message.edit(view=self)


class ModerationConfirmationView(AuthorView):
    def __init__(
        self,
        *,
        ctx: commands.Context,
        member: discord.User | discord.Member | str,
        action: str,
        reason: str,
    ):
        super().__init__(ctx.author, timeout=60)

        self.ctx = ctx
        self.action = action
        self.reason = reason
        self.confirmed = False
        self.message: discord.Message
        self.member = member.mention if not isinstance(member, str) else member

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        await interaction.response.edit_message(view=None)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        await interaction.response.edit_message(view=None)
        self.stop()

    async def prompt(self) -> bool:
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"Are you sure you want to **{self.action}** {self.member}?"
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: {self.reason}"

        message = await self.ctx.reply(embed=embed, view=self, mention_author=False)
        self.message = message

        await self.wait()
        return self.confirmed

    async def edit_success(self, embed: discord.Embed) -> None:
        await self.message.edit(embed=embed, view=None)


class PaginatorView(AuthorView):
    """
    Very small embed paginator.

    Example:
        view = PaginatorView(ctx.author, embeds)
        view.message = await ctx.reply(embed=embeds[0], view=view, mention_author=False)
    """

    def __init__(self, author: discord.abc.User, embeds: list[discord.Embed]):
        super().__init__(author)

        if not embeds:
            raise ValueError("PaginatorView requires at least one embed.")

        self.embeds = embeds
        self.page = 0
        self._update_buttons()

    def _update_buttons(self):
        self.first.disabled = self.page == 0
        self.previous.disabled = self.page == 0
        self.next.disabled = self.page == len(self.embeds) - 1
        self.last.disabled = self.page == len(self.embeds) - 1

    @discord.ui.button(label="«", style=discord.ButtonStyle.secondary)
    async def first(self, interaction: discord.Interaction, button: Button):
        self.page = 0
        self._update_buttons()

        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @discord.ui.button(label="‹", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: Button):
        self.page -= 1
        self._update_buttons()

        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @discord.ui.button(label="›", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: Button):
        self.page += 1
        self._update_buttons()

        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @discord.ui.button(label="»", style=discord.ButtonStyle.secondary)
    async def last(self, interaction: discord.Interaction, button: Button):
        self.page = len(self.embeds) - 1
        self._update_buttons()

        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)
