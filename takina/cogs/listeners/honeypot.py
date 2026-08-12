from takina.models import GuildSettingsModel
from takina.cogs.mod.modlog import ModLog
from takina import config, database
from takina.libs import lychecks
from discord.ext import commands
from datetime import timedelta
from typing import cast
import discord


class Honeypot(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    @property
    def modlog(self) -> ModLog:
        modlog = self._bot.get_cog("ModLog")
        return cast(ModLog, modlog)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        settings = await database.get(GuildSettingsModel, guild_id=message.guild.id)
        if not settings or not settings.honeypot_channel_id:
            return

        if message.channel.id != settings.honeypot_channel_id:
            return

        member = message.author
        if not isinstance(member, discord.Member):
            return

        reason = "Muted for triggering the honeypot system."
        await member.timeout(timedelta(weeks=4), reason=reason)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"You were muted in **{message.guild.name}** for 4 weeks."
        embed.description += f"\n\n{config.emojis.NOTE} **Reason**: You have been automatically muted by the honeypot system."

        try:
            await member.send(embed=embed)
        except discord.HTTPException:
            pass

        for channel in message.guild.text_channels:
            try:
                await channel.purge(
                    before=discord.utils.utcnow(),
                    after=discord.utils.utcnow() - timedelta(minutes=10),
                    check=lambda msg: msg.author.id == member.id,
                    oldest_first=False,
                    bulk=True,
                )
            except discord.Forbidden:
                pass

        if moderator := self._bot.user:
            await self.modlog.log_action(message, "mute", member, reason, moderator, "4w")

    @commands.hybrid_command(
        name="honeypot", description="Configure the honeypot channel.", usage="#channel"
    )
    @lychecks.has_permissions(manage_guild=True)
    @lychecks.guild_only()
    async def honeypot(self, ctx: commands.Context, channel: discord.TextChannel) -> None:
        assert ctx.guild is not None

        settings = await database.get(GuildSettingsModel, guild_id=ctx.guild.id)
        if settings is None:
            settings = GuildSettingsModel(guild_id=ctx.guild.id)

        settings.honeypot_channel_id = channel.id
        await database.save(settings)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Honeypot channel has been set to {channel.mention}. Please remember to give me permissions to manage messages and to timeout members.`"

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Honeypot(bot))
