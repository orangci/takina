# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyhelpers, lyerrors
from discord.ext import commands
from takina import config
import discord


class Channels(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @lychecks.has_permissions(manage_channels=True)
    @commands.hybrid_command(
        name="slowmode",
        description="Sets slowmode in the current or specified channel.",
        usage="2h #channel",
    )
    async def slowmode(
        self,
        ctx: commands.Context,
        duration: str | None = None,
        channel: discord.TextChannel | None = None,
    ):
        assert ctx.guild is not None
        assert isinstance(ctx.channel, discord.TextChannel)
        channel = channel or ctx.channel
        assert channel is not None
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        if duration:
            duration = "0s" if duration.lower() in ["off", "disable"] else duration
            duration_parsed = lyhelpers.duration_calculator(duration, slowmode=True)
            if duration_parsed > 21600:
                raise lyerrors.TakinaUserInputError(
                    "The duration you've specified is too long. The maximum slowmode you may set is six hours."
                )

            await channel.edit(slowmode_delay=duration_parsed)
            embed.description = (
                f":timer: Slowmode has been disabled for {channel.mention}."
                if duration == "0s"
                else f":timer: Slowmode set to {duration} in {channel.mention}."
            )
        elif channel.slowmode_delay != 0:
            embed.description = f":timer: The slowmode of {channel.mention} is set to {lyhelpers.reverse_duration_calculator(channel.slowmode_delay)}."
        else:
            embed.description = f":timer: Slowmode is not enabled for {channel.mention}."

        await ctx.reply(embed=embed, mention_author=False)

    @lychecks.has_permissions(manage_channels=True)
    @commands.hybrid_command(
        name="lock", description="Locks the current or specified channel.", usage="#channel"
    )
    async def lock(self, ctx: commands.Context, channel: discord.TextChannel | None = None):
        assert ctx.guild is not None
        assert isinstance(ctx.channel, discord.TextChannel)
        channel = channel or ctx.channel
        assert channel is not None
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False

        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(
            description=f":lock: Channel {channel.mention} has been locked.",
            colour=config.EMBED_COLOUR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @lychecks.has_permissions(manage_channels=True)
    @commands.hybrid_command(
        name="unlock", description="Unlocks the current or specified channel.", usage="#channel"
    )
    async def unlock(self, ctx: commands.Context, channel: discord.TextChannel | None = None):
        assert ctx.guild is not None
        assert isinstance(ctx.channel, discord.TextChannel)
        channel = channel or ctx.channel
        assert channel is not None
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True

        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(
            description=f":unlock: Channel {channel.mention} has been unlocked.",
            colour=config.EMBED_COLOUR,
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Channels(bot))
