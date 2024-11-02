import nextcord
from nextcord.ext import application_checks, commands
from nextcord import SlashOption
from __main__ import EMBED_COLOR
from ..libs.oclib import *


class ChannelManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="slowmode",
        description="Sets slowmode in the current or specified channel.",
        help="Usage: `slowmode #channel <duration>`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.has_permissions(manage_channels=True)
    async def slowmode(
        self, ctx: commands.Context, duration: str, channel: nextcord.TextChannel = None
    ):
        channel = channel or ctx.channel
        duration = duration_calculator(duration)
        if duration is None:
            embed = nextcord.Embed(
                description="❌ Invalid duration format. Use `<number>[d|h|m|w|y].`",
                color=EMBED_COLOR,
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        await channel.edit(slowmode_delay=duration)
        embed = nextcord.Embed(
            description=f" :timer: Slowmode set to {duration} seconds in {channel.mention}.",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="lock",
        description="Locks the current or specified channel.",
        help="Usage: `lock #channel`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context, channel: nextcord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False

        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = nextcord.Embed(
            description=f"🔒 Channel {channel.mention} has been locked.",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="unlock",
        description="Unlocks the current or specified channel.",
        help="Usage: `unlock #channel`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context, channel: nextcord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True

        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = nextcord.Embed(
            description=f"🔓 Channel {channel.mention} has been unlocked.",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)


class SlashChannelManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="channel", description="Channel management commands.")
    async def channel_group(self, interaction: nextcord.Interaction):
        pass

    @channel_group.subcommand(
        name="slowmode",
        description="Sets slowmode in the current or specified channel.",
    )
    @application_checks.has_permissions(manage_channels=True)
    async def slowmode(
        self,
        interaction: nextcord.Interaction,
        duration: str = SlashOption(
            description="The amount of time to set the slowmode to", required=True
        ),
        channel: nextcord.TextChannel = SlashOption(
            description="Channel to set slowmode", required=False
        ),
    ):
        channel = channel or interaction.channel
        duration = duration_calculator(duration)
        if duration is None:
            embed = nextcord.Embed(
                description="❌ Invalid duration format. Use `<number>[d|h|m|w|y].`",
                color=EMBED_COLOR,
            )
            await interaction.send(embed=embed, ephemeral=True)
            return

        await channel.edit(slowmode_delay=duration)
        embed = nextcord.Embed(
            description=f":timer: Slowmode set to {duration} seconds in {channel.mention}.",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed)

    @channel_group.subcommand(
        name="lock", description="Locks the current or specified channel."
    )
    @application_checks.has_permissions(manage_channels=True)
    async def lock(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = SlashOption(
            description="Channel to lock", required=False
        ),
    ):
        channel = channel or interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False

        await channel.set_permissions(
            interaction.guild.default_role, overwrite=overwrite
        )
        embed = nextcord.Embed(
            description=f"🔒 Channel {channel.mention} has been locked.",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed)

    @channel_group.subcommand(
        name="unlock", description="Unlocks the current or specified channel."
    )
    @application_checks.has_permissions(manage_channels=True)
    async def unlock(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = SlashOption(
            description="Channel to unlock", required=False
        ),
    ):
        channel = channel or interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True

        await channel.set_permissions(
            interaction.guild.default_role, overwrite=overwrite
        )
        embed = nextcord.Embed(
            description=f"🔓 Channel {channel.mention} has been unlocked.",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(ChannelManagement(bot))
    bot.add_cog(SlashChannelManagement(bot))
