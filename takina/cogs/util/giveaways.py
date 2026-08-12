from takina.libs import lyerrors, lyhelpers, lychecks
from datetime import datetime, timedelta, timezone
from takina import config, database, models
from discord.ext import commands, tasks
import discord
import random


MAXIMUM_GUILD_GIVEAWAYS = 25


class GiveawayView(discord.ui.View):
    def __init__(self, cog: "Giveaways", guild_id: int, giveaway_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
        self.giveaway_id = giveaway_id
        self.join_button.custom_id = f"giveaway:{guild_id}:{giveaway_id}:join"

    @discord.ui.button(label="🎉", style=discord.ButtonStyle.primary)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            return

        giveaway = await database.get(
            models.GiveawayModel, guild_id=interaction.guild.id, id=self.giveaway_id
        )
        if not giveaway:
            return

        user_id = interaction.user.id
        embed = discord.Embed(colour=config.EMBED_COLOUR)

        if user_id in giveaway.participants:
            giveaway.participants.remove(user_id)
            await database.save(giveaway)
            await self.cog.update_giveaway_message(giveaway)
            embed.description = f"{config.emojis.SUCCESS} You have withdrawn from the giveaway."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        giveaway.participants.append(user_id)
        await database.save(giveaway)
        await self.cog.update_giveaway_message(giveaway)

        embed.description = (
            f"{config.emojis.SUCCESS} You have entered giveaway #{self.giveaway_id}."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class Giveaways(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._expiry_loop.start()

    # when the bot restarts, it will, on load, activate all views for
    # any currently active giveaways
    async def cog_load(self):
        giveaways = await database.get_all(models.GiveawayModel, ended=False)

        for giveaway in giveaways:
            self._bot.add_view(
                GiveawayView(self, giveaway.guild_id, giveaway.id), message_id=giveaway.message_id
            )

    def cog_unload(self):
        self._expiry_loop.cancel()

    async def _get_next_id(self, guild_id: int) -> int:
        giveaways = await database.get_all(models.GiveawayModel, guild_id=guild_id)

        if not giveaways:
            return 1

        return max(giveaway.id for giveaway in giveaways) + 1

    async def _get_channel(self, channel_id: int) -> discord.TextChannel | discord.Thread | None:
        channel = self._bot.get_channel(channel_id)

        if channel is None:
            try:
                channel = await self._bot.fetch_channel(channel_id)
            except discord.NotFound:
                return None

        if isinstance(channel, (discord.TextChannel, discord.Thread)):
            return channel

        return None

    async def _get_participants(self, giveaway: models.GiveawayModel) -> list[discord.User]:
        participant_ids = list(giveaway.participants)

        if self._bot.user is not None:
            participant_ids = [
                user_id for user_id in participant_ids if user_id != self._bot.user.id
            ]

        participants = []
        invalid_ids = []

        for user_id in participant_ids:
            try:
                user = await self._bot.fetch_user(user_id)
            except discord.NotFound:
                invalid_ids.append(user_id)
                continue

            if not user.bot:
                participants.append(user)
            else:
                invalid_ids.append(user_id)

        if invalid_ids:
            giveaway.participants = [
                user_id for user_id in giveaway.participants if user_id not in invalid_ids
            ]
            await database.save(giveaway)

        return participants

    async def update_giveaway_message(self, giveaway: models.GiveawayModel):
        channel = await self._get_channel(giveaway.channel_id)

        if channel is None:
            return

        try:
            message = await channel.fetch_message(giveaway.message_id)
        except discord.NotFound:
            return

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = giveaway.title
        embed.description = f"{giveaway.description}\n"
        embed.description += f"\n> **Ends**: <t:{int(giveaway.ends_at.timestamp())}> (<t:{int(giveaway.ends_at.timestamp())}:R>)"
        embed.description += f"\n> **Giveaway ID**: `#{giveaway.id}`"
        embed.description += f"\n> **Participants**: {len(giveaway.participants)}"
        embed.description += f"\n> **Winners**: {giveaway.winners}"

        view = GiveawayView(self, giveaway.guild_id, giveaway.id)
        await message.edit(embed=embed, view=view)

    async def _end_giveaway(
        self, giveaway: models.GiveawayModel, *, reroll: bool = False
    ) -> list[discord.User] | None:
        if giveaway.ended and not reroll:
            return None

        channel = await self._get_channel(giveaway.channel_id)

        # if, say, the channel has been deleted
        # then end the giveaway, yes
        # but then return, since there's no point in trying to
        # edit a non existent message
        if channel is None:
            giveaway.ended = True
            await database.save(giveaway)
            return None

        # read above comment, except it's if the message is gone, not channel
        try:
            message = await channel.fetch_message(giveaway.message_id)
        except discord.NotFound:
            giveaway.ended = True
            await database.save(giveaway)
            return None

        participants = await self._get_participants(giveaway)

        if not participants:
            giveaway.ended = True
            giveaway.winner_ids = []
            await database.save(giveaway)

            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.title = giveaway.title
            embed.description = f"{giveaway.description}\n"
            embed.description += f"\n> **Ended**: <t:{int(giveaway.ends_at.timestamp())}> (<t:{int(giveaway.ends_at.timestamp())}:R>)"
            embed.description += f"\n> **Giveaway ID**: `#{giveaway.id}`"
            embed.description += "\n> **Participants**: 0"
            embed.description += f"\n> **Winners**: {giveaway.winners}"
            embed.description += "\n\n**Giveaway ended with no participants.**"

            view = GiveawayView(self, giveaway.guild_id, giveaway.id)
            for item in view.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True

            await message.edit(embed=embed, view=view)
            return []

        winner_count = min(giveaway.winners, len(participants))
        winners = random.sample(participants, winner_count)

        giveaway.ended = True
        giveaway.winner_ids = [winner.id for winner in winners]
        await database.save(giveaway)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = giveaway.title
        embed.description = f"{giveaway.description}\n"
        embed.description += f"\n> **Ends**: <t:{int(giveaway.ends_at.timestamp())}> (<t:{int(giveaway.ends_at.timestamp())}:R>)"
        embed.description += f"\n> **Giveaway ID**: `#{giveaway.id}`"
        embed.description += f"\n> **Participants**: {len(giveaway.participants)}"
        embed.description += f"\n> **Winners**: {', '.join(winner.mention for winner in winners)}"

        view = GiveawayView(self, giveaway.guild_id, giveaway.id)

        for item in view.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        await message.edit(embed=embed, view=view)

        notification_embed = discord.Embed(colour=config.EMBED_COLOUR)
        notification_embed.description = f"Congratulations! You have won giveaway #{giveaway.id}!"

        await channel.send(
            ", ".join(winner.mention for winner in winners), embed=notification_embed
        )
        return winners

    async def _reroll_giveaway(self, giveaway: models.GiveawayModel) -> list[discord.User] | None:
        if not giveaway.ended:
            return None

        participants = await self._get_participants(giveaway)
        previous_winner_ids = set(giveaway.winner_ids)
        participants = [user for user in participants if user.id not in previous_winner_ids]

        if not participants:
            return None

        winner_count = min(giveaway.winners, len(participants))
        winners = random.sample(participants, winner_count)
        giveaway.winner_ids = [winner.id for winner in winners]

        await database.save(giveaway)

        channel = await self._get_channel(giveaway.channel_id)

        if channel:
            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.description = (
                f"Congratulations! Due to a reroll, you have won giveaway #{giveaway.id}!"
            )
            await channel.send(", ".join(winner.mention for winner in winners), embed=embed)

        return winners

    @tasks.loop(seconds=30)
    async def _expiry_loop(self):
        giveaways = await database.get_all(models.GiveawayModel, ended=False)

        now = datetime.now(timezone.utc)

        for giveaway in giveaways:
            if giveaway.ends_at <= now:
                await self._end_giveaway(giveaway)

    @_expiry_loop.before_loop
    async def _before_expiry_loop(self):
        await self._bot.wait_until_ready()

    @commands.hybrid_group(
        name="giveaway", description="Giveaway management commands.", invoke_without_command=True
    )
    async def giveaway(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @giveaway.command(
        name="start", description="Start a giveaway.", usage='5h "title" "description" 2'
    )
    # @lychecks.has_permissions(manage_events=True)
    @lychecks.guild_only()
    async def start(
        self,
        ctx: commands.Context,
        duration: str,
        title: str,
        description: str | None = None,
        winners: int = 1,
    ):
        assert ctx.guild is not None

        if not description:
            description = ""

        if winners < 1:
            raise lyerrors.TakinaUserInputError("A giveaway must have at least one winner.")
        elif winners > 50:
            raise lyerrors.TakinaUserInputError("A giveaway cannot have more than 50 winners.")

        active_giveaways = await database.get_all(
            models.GiveawayModel, guild_id=ctx.guild.id, ended=False
        )

        if len(active_giveaways) >= MAXIMUM_GUILD_GIVEAWAYS:
            raise lyerrors.TakinaError(
                "This guild has reached the maximum number of active giveaways allowed at once."
            )

        duration_parsed = lyhelpers.duration_calculator(duration)

        if duration_parsed <= 0:
            raise lyerrors.TakinaUserInputError("The giveaway duration must be greater than zero.")
        elif duration_parsed >= 31557600:
            raise lyerrors.TakinaUserInputError(
                "The duration of the giveaway must be less than one year."
            )

        giveaway_id = await self._get_next_id(ctx.guild.id)

        ends_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(
            seconds=duration_parsed
        )

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = title
        embed.description = f"{description}\n"
        embed.description += (
            f"\n> **Ends**: <t:{int(ends_at.timestamp())}> (<t:{int(ends_at.timestamp())}:R>)"
        )
        embed.description += f"\n> **Giveaway ID**: #`{giveaway_id}`"
        embed.description += "\n> **Participants**: 0"
        embed.description += f"\n> **Winners**: {winners}"

        view = GiveawayView(self, ctx.guild.id, giveaway_id)
        message = await ctx.channel.send(embed=embed, view=view)

        giveaway = models.GiveawayModel(
            guild_id=ctx.guild.id,
            id=giveaway_id,
            channel_id=ctx.channel.id,
            message_id=message.id,
            title=title,
            description=description,
            ends_at=ends_at,
            winners=winners,
        )

        await database.save(giveaway)

        self._bot.add_view(view, message_id=message.id)

        if ctx.interaction:
            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.description = (
                f"{config.emojis.SUCCESS} Giveaway #`{giveaway_id}` has been started."
            )
            await ctx.send(embed=embed, ephemeral=True)

    @giveaway.command(name="stop", aliases=["end"], description="End a giveaway.", usage="1")
    # @lychecks.has_permissions(manage_events=True)
    @lychecks.guild_only()
    async def stop(self, ctx: commands.Context, giveaway_id: int):
        assert ctx.guild is not None
        giveaway = await database.get(models.GiveawayModel, guild_id=ctx.guild.id, id=giveaway_id)

        if giveaway is None:
            raise lyerrors.TakinaNotFoundError(f"Giveaway #`{giveaway_id}` does not exist.")

        if giveaway.ended:
            raise lyerrors.TakinaError(f"Giveaway #`{giveaway_id}` has already ended.")

        await self._end_giveaway(giveaway)

        if ctx.interaction:
            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.description = (
                f"{config.emojis.SUCCESS} Successfully ended giveaway #`{giveaway_id}`."
            )
            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.message.add_reaction(config.emojis.SUCCESS)

    @giveaway.command(description="Reroll a giveaway winner.", usage="1")
    # @lychecks.has_permissions(manage_events=True)
    @lychecks.guild_only()
    async def reroll(self, ctx: commands.Context, giveaway_id: int):
        assert ctx.guild is not None
        giveaway = await database.get(models.GiveawayModel, guild_id=ctx.guild.id, id=giveaway_id)

        if giveaway is None:
            raise lyerrors.TakinaNotFoundError(f"Giveaway #`{giveaway_id}` does not exist.")

        if not giveaway.ended:
            raise lyerrors.TakinaError(f"Giveaway #`{giveaway_id}` has not ended yet.")

        winners = await self._reroll_giveaway(giveaway)

        if winners is None:
            raise lyerrors.TakinaError(
                "There are no or not enough eligible participants required to reroll."
            )

        if ctx.interaction:
            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.description = (
                f"{config.emojis.SUCCESS} Giveaway #`{giveaway_id}` has been rerolled."
            )

            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.message.add_reaction(config.emojis.SUCCESS)

    @giveaway.command(description="View the details of a past giveaway.", usage="1")
    # @lychecks.has_permissions(manage_events=True)
    @lychecks.guild_only()
    async def view(self, ctx: commands.Context, giveaway_id: int):
        assert ctx.guild is not None
        giveaway = await database.get(models.GiveawayModel, guild_id=ctx.guild.id, id=giveaway_id)

        if giveaway is None:
            raise lyerrors.TakinaNotFoundError(f"Giveaway #`{giveaway_id}` does not exist.")

        if not giveaway.ended:
            raise lyerrors.TakinaError(f"Giveaway #`{giveaway_id}` has not ended yet.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{giveaway.description}\n"
        embed.description += f"\n> **Ended**: <t:{int(giveaway.ends_at.timestamp())}> (<t:{int(giveaway.ends_at.timestamp())}:R>)"
        embed.description += f"\n> **Giveaway ID**: `#{giveaway.id}`"
        embed.description += f"\n> **Participants**: {len(giveaway.participants)}"

        if giveaway.winner_ids:
            winners = []

            for winner_id in giveaway.winner_ids:
                try:
                    winner = await self._bot.fetch_user(winner_id)
                except discord.NotFound:
                    continue

                winners.append(winner.mention)

            if winners:
                embed.description += f"\n> **Winners**: {', '.join(winner for winner in winners)}"

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaways(bot))
