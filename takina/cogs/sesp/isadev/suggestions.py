"""
    BSD 3-Clause License

    Copyright (c) 2024 - present, MaskDuck

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, this
    list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

    3. Neither the name of the copyright holder nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# code has been modified and is not the original code from MaskDuck

from contextlib import suppress
from typing import Literal, cast
from nextcord.ext import commands, application_checks
import nextcord
from config import *
from .libs.lib import *


class ApproveOrDeny(nextcord.ui.Modal):
    def __init__(self, mode: bool, message: nextcord.Message) -> None:
        self._suggestion_msg: nextcord.Message = message
        self._mode: bool = mode
        title = "Approve the suggestion" if mode else "Deny the suggestion"
        super().__init__(title=title, timeout=180)
        self.reas = nextcord.ui.TextInput(
            label="Provide a reason.",
            style=nextcord.TextInputStyle.paragraph,
            required=True,
        )
        self.add_item(self.reas)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        embed = self._suggestion_msg.embeds[0]
        embed.add_field(
            name=f"{'Approved by' if self._mode else 'Denied by'} {str(interaction.user)}",
            value=self.reas.value,
        )
        await self._suggestion_msg.edit(embed=embed)


class Suggestion(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.suggestion_channel = SUGGESTION_CHANNEL_ID

    @nextcord.message_command(name="Approve the suggestion", guild_ids=[SERVER_ID])
    @application_checks.has_role(MAINTAINER_ROLE_ID)
    async def approve_suggestion_msg(
        self, interaction: nextcord.Interaction, message: nextcord.Message
    ) -> None:
        if interaction.channel.id != self.suggestion_channel:
            embed = nextcord.Embed(
                description="You must be in the suggestions channel to use this command.",
                color=ERROR_COLOR,
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        await interaction.response.send_modal(ApproveOrDeny(True, message))

    @nextcord.message_command(name="Deny the suggestion", guild_ids=[SERVER_ID])
    @application_checks.has_role(MAINTAINER_ROLE_ID)
    async def deny_suggestion_msg(
        self, interaction: nextcord.Interaction, message: nextcord.Message
    ) -> None:
        if interaction.channel.id != self.suggestion_channel:
            embed = nextcord.Embed(
                description="You must be in the suggestions channel to use this command.",
                color=ERROR_COLOR,
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        await interaction.response.send_modal(ApproveOrDeny(False, message))

    @nextcord.slash_command(name="suggestion", guild_ids=[SERVER_ID])
    async def _suggestion(self, interaction: nextcord.Interaction):
        pass

    @_suggestion.subcommand(
        name="suggest",
        description="We'd love to hear your suggestions!",
    )
    async def _suggest(
        self,
        interaction: nextcord.Interaction,
        suggestion: str = nextcord.SlashOption(
            name="suggestion", description="Write your suggestion here.", required=True
        ),
    ):
        embed = nextcord.Embed(
            title="Suggestion", description=suggestion, color=EMBED_COLOR
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar, url=f"https://discord.com/users/{interaction.user.id}")

        channel = interaction.guild.get_channel(self.suggestion_channel)
        channel = cast(nextcord.TextChannel, channel)
        message = await channel.send(embed=embed)
        success_react = await interaction.guild.fetch_emoji(1249728142084673690)
        skullsob_react = await interaction.guild.fetch_emoji(1229339480884908085)
        await message.add_reaction(success_react)
        await message.add_reaction(skullsob_react)

        log_channel = self.bot.get_channel(955105139461607444)
        log_channel = cast(nextcord.TextChannel, log_channel)
        await log_channel.send(
            embed=nextcord.Embed(
                description=f"{str(interaction.user)} has suggested: {suggestion}.",
                color=EMBED_COLOR,
            )
        )

        embed = nextcord.Embed(
            description=f"You can now see your suggestion in {channel.mention}.",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=True)

    @_suggestion.subcommand(name="deny", description="Deny suggestion")
    @application_checks.has_permissions(administrator=True)
    async def _deny(
        self,
        interaction: nextcord.Interaction,
        messageId: str = nextcord.SlashOption(
            name="message_id", description="Message to deny", required=True
        ),
        why: str = nextcord.SlashOption(
            name="why", description="Why did you deny this suggestion?", required=True
        ),
    ):
        channel = interaction.guild.get_channel(self.suggestion_channel)
        channel = cast(nextcord.TextChannel, channel)
        message = await channel.fetch_message(int(messageId))
        embed = message.embeds[0]
        embed.add_field(name=f"Denied by {str(interaction.user)}", value=why)
        await message.edit(embed=embed)

        embed = nextcord.Embed(
            description=f"Denied suggestion [here](https://discord.com/channels/{interaction.guild.id}/{self.suggestion_channel}/{messageId}).",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=True)

    @_suggestion.subcommand(name="approve", description="Approve suggestion")
    @application_checks.has_permissions(administrator=True)
    async def _approve(
        self,
        interaction: nextcord.Interaction,
        messageId: str = nextcord.SlashOption(
            name="message_id", description="Message to approve", required=True
        ),
        why: str = nextcord.SlashOption(
            name="why", description="Why did you approve this request?", required=False
        ),
    ):
        why = why or "No reason provided"
        channel = self.bot.get_channel(self.suggestion_channel)
        channel = cast(nextcord.TextChannel, channel)
        message = await channel.fetch_message(int(messageId))
        embed = message.embeds[0]
        embed.add_field(name=f"Approved by {str(interaction.user)}", value=why)
        await message.edit(embed=embed)

        embed = nextcord.Embed(
            description=f"Approved suggestion [here](https://discord.com/channels/{interaction.guild.id}/{self.suggestion_channel}/{messageId}).",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Suggestion(bot))
