# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyhelpers, lyerrors
from discord.ext import commands
from takina import config
import discord

MAX_SLOWMODE = 6 * 60 * 60

# plain assignment, as discord.py cannot read a type statement as a converter
Channel = discord.TextChannel | discord.VoiceChannel | discord.Thread


def target_channel(ctx: commands.Context, channel: Channel | None) -> Channel:
    if channel is not None:
        return channel

    if not isinstance(ctx.channel, discord.TextChannel | discord.VoiceChannel | discord.Thread):
        raise lyerrors.TakinaUserInputError(
            "This only works in text channels, voice channels and threads."
        )

    return ctx.channel


class Channels(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def set_locked(self, ctx: commands.Context, channel: Channel, locked: bool) -> None:
        assert ctx.guild is not None
        reason = f"{'Locked' if locked else 'Unlocked'} by {ctx.author}."

        if isinstance(channel, discord.Thread):
            await channel.edit(locked=locked, reason=reason)
            return

        # None hands both back to the role's defaults on unlock
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        value = False if locked else None
        overwrite.update(send_messages=value, send_messages_in_threads=value)
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=reason)

    @commands.hybrid_command(
        name="slowmode",
        description="Sets slowmode in the current or specified channel.",
        usage="2h #channel",
    )
    @lychecks.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def slowmode(
        self, ctx: commands.Context, duration: str | None = None, channel: Channel | None = None
    ):
        channel = target_channel(ctx, channel)
        embed = discord.Embed(colour=config.EMBED_COLOUR)

        if duration:
            seconds = (
                0
                if duration.lower() in ("off", "disable")
                else lyhelpers.duration_calculator(duration)
            )
            if seconds > MAX_SLOWMODE:
                raise lyerrors.TakinaUserInputError(
                    "The duration you've specified is too long. The maximum slowmode you may set is six hours."
                )

            await channel.edit(slowmode_delay=seconds)
            if seconds:
                embed.description = f"{config.emojis.SUCCESS} Slowmode set to {lyhelpers.reverse_duration_calculator(seconds)} in {channel.mention}."
            else:
                embed.description = (
                    f"{config.emojis.SUCCESS} Slowmode has been disabled for {channel.mention}."
                )
        elif channel.slowmode_delay:
            embed.description = f"{config.emojis.NOTE} The slowmode of {channel.mention} is set to {lyhelpers.reverse_duration_calculator(channel.slowmode_delay)}."
        else:
            embed.description = (
                f"{config.emojis.NOTE} Slowmode is not enabled for {channel.mention}."
            )

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="lock",
        description="Locks the current or specified channel, along with its threads.",
        usage="#channel",
    )
    @lychecks.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def lock(self, ctx: commands.Context, channel: Channel | None = None):
        channel = target_channel(ctx, channel)
        await self.set_locked(ctx, channel, True)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} {channel.mention} has been locked."
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="unlock", description="Unlocks the current or specified channel.", usage="#channel"
    )
    @lychecks.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def unlock(self, ctx: commands.Context, channel: Channel | None = None):
        channel = target_channel(ctx, channel)
        await self.set_locked(ctx, channel, False)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} {channel.mention} has been unlocked."
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Channels(bot))
