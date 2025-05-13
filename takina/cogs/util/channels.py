# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import nextcord
import config
from nextcord import SlashOption
from nextcord.ext import application_checks, commands

from ..libs import oclib


class ChannelManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="slowmode", help="Sets slowmode in the current or specified channel.", usage="2h #channel")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, duration: str = None, channel: nextcord.TextChannel = None):
        channel = channel or ctx.channel
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        if duration:
            duration = "0s" if duration.lower() in ["off", "disable"] else duration
            duration_parsed = oclib.duration_calculator(duration, slowmode=True)
            if isinstance(duration_parsed, nextcord.Embed):
                await ctx.reply(embed=duration_parsed, mention_author=False)
                return

            await channel.edit(slowmode_delay=duration_parsed)
            embed.description = (
                f":timer: Slowmode has been disabled for {channel.mention}."
                if duration == "0s"
                else f":timer: Slowmode set to {duration} in {channel.mention}."
            )
        elif channel.slowmode_delay != 0:
            embed.description = f":timer: The slowmode of {channel.mention} is set to {oclib.reverse_duration_calculator(channel.slowmode_delay)}."
        else:
            embed.description = f":timer: Slowmode is not enabled for {channel.mention}."

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="lock", help="Locks the current or specified channel.", usage="#channel")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context, channel: nextcord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False

        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = nextcord.Embed(description=f"🔒 Channel {channel.mention} has been locked.", color=config.EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="unlock", help="Locks the current or specified channel.", usage="#channel")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context, channel: nextcord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True

        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = nextcord.Embed(description=f"🔓 Channel {channel.mention} has been unlocked.", color=config.EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)


class SlashChannelManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="channel", description="Channel management commands.")
    async def channel_group(self, interaction: nextcord.Interaction):
        pass

    @channel_group.subcommand(name="slowmode", description="Sets slowmode in the current or specified channel.")
    @application_checks.has_permissions(manage_channels=True)
    async def slowmode(
        self,
        interaction: nextcord.Interaction,
        duration: str = SlashOption(description="The amount of time to set the slowmode to", required=False),
        channel: nextcord.TextChannel = SlashOption(description="Channel to set slowmode", required=False),
    ):
        await interaction.response.defer()
        channel = channel or interaction.channel
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        if duration:
            duration = "0s" if duration.lower() in ["off", "disable"] else duration
            duration_parsed = oclib.duration_calculator(duration, slowmode=True)
            if isinstance(duration_parsed, nextcord.Embed):
                await interaction.send(embed=duration_parsed, ephemeral=True)
                return

            await channel.edit(slowmode_delay=duration_parsed)
            embed.description = (
                f":timer: Slowmode has been disabled for {channel.mention}."
                if duration == "0s"
                else f":timer: Slowmode set to {duration} in {channel.mention}."
            )
        elif channel.slowmode_delay != 0:
            embed.description = f":timer: The slowmode of {channel.mention} is set to {oclib.reverse_duration_calculator(channel.slowmode_delay)}."
        else:
            embed.description = f":timer: Slowmode is not enabled for {channel.mention}."

        await interaction.send(embed=embed)

    @channel_group.subcommand(name="lock", description="Locks the current or specified channel.")
    @application_checks.has_permissions(manage_channels=True)
    async def lock(
        self, interaction: nextcord.Interaction, channel: nextcord.TextChannel = SlashOption(description="Channel to lock", required=False)
    ):
        await interaction.response.defer()
        channel = channel or interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False

        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        embed = nextcord.Embed(description=f"🔒 Channel {channel.mention} has been locked.", color=config.EMBED_COLOR)
        await interaction.send(embed=embed)

    @channel_group.subcommand(name="unlock", description="Unlocks the current or specified channel.")
    @application_checks.has_permissions(manage_channels=True)
    async def unlock(
        self, interaction: nextcord.Interaction, channel: nextcord.TextChannel = SlashOption(description="Channel to unlock", required=False)
    ):
        await interaction.response.defer()
        channel = channel or interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True

        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        embed = nextcord.Embed(description=f"🔓 Channel {channel.mention} has been unlocked.", color=config.EMBED_COLOR)
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(ChannelManagement(bot))
    bot.add_cog(SlashChannelManagement(bot))
