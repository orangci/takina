# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors, lyhelpers, lychecks
from datetime import datetime, timedelta, UTC
from takina import config, database, models
from sqlalchemy.exc import IntegrityError
from discord.ext import commands, tasks
from collections.abc import Iterable
from sqlmodel import col
import logging
import discord
import asyncio
import weakref
import random


MAXIMUM_GUILD_GIVEAWAYS = 25
MAX_WINNERS = 50
MAX_DURATION = lyhelpers.DURATION_UNITS["y"]
MAX_DESCRIPTION_LENGTH = 2000
MAX_ID_ATTEMPTS = 5
# a burst of entries becomes one message edit
EDIT_DELAY = 5

Title = commands.Range[str, 1, 256]

type GiveawayKey = tuple[int, int]
# everywhere a giveaway can be started; voice and stage channels have a text chat too
type GiveawayChannel = (
    discord.TextChannel | discord.Thread | discord.VoiceChannel | discord.StageChannel
)

logger = logging.getLogger("takina.giveaways")


def mentions(user_ids: Iterable[int]) -> str:
    return ", ".join(f"<@{user_id}>" for user_id in user_ids)


def giveaway_embed(giveaway: models.GiveawayModel) -> discord.Embed:
    timestamp = int(giveaway.ends_at.timestamp())

    embed = discord.Embed(colour=config.EMBED_COLOUR)
    embed.title = giveaway.title
    embed.description = f"{giveaway.description}\n" if giveaway.description else ""
    embed.description += (
        f"\n> **{'Ended' if giveaway.ended else 'Ends'}**: <t:{timestamp}> (<t:{timestamp}:R>)"
    )
    embed.description += f"\n> **Giveaway ID**: `#{giveaway.id}`"
    embed.description += f"\n> **Participants**: {len(giveaway.participants):,}"

    if giveaway.ended and giveaway.winner_ids:
        embed.description += f"\n> **Winners**: {mentions(giveaway.winner_ids)}"
    else:
        embed.description += f"\n> **Winners**: {giveaway.winners:,}"

    if giveaway.ended and not giveaway.participants:
        embed.description += "\n\n**Giveaway ended with no participants.**"

    return embed


class GiveawayView(discord.ui.View):
    def __init__(self, cog: "Giveaways", guild_id: int, giveaway_id: int, *, ended: bool = False):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
        self.giveaway_id = giveaway_id
        self.join_button.custom_id = f"giveaway:{guild_id}:{giveaway_id}:join"
        self.join_button.disabled = ended

    @discord.ui.button(label="🎉", style=discord.ButtonStyle.primary)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        # ended=False makes a click on a stale button change nothing
        giveaway = await database.toggle_in_array(
            models.GiveawayModel,
            "participants",
            user_id,
            guild_id=self.guild_id,
            id=self.giveaway_id,
            ended=False,
        )

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        if giveaway is None:
            embed.description = f"{config.emojis.ERROR} This giveaway has already ended."
        elif user_id in giveaway.participants:
            embed.description = (
                f"{config.emojis.SUCCESS} You have entered giveaway `#{self.giveaway_id}`."
            )
        else:
            embed.description = (
                f"{config.emojis.SUCCESS} You have withdrawn from giveaway `#{self.giveaway_id}`."
            )

        # answer first: the edit below can easily outlast the three seconds discord allows
        await interaction.response.send_message(embed=embed, ephemeral=True)

        if giveaway is not None:
            self.cog.schedule_update((self.guild_id, self.giveaway_id))


class Giveaways(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._locks: weakref.WeakValueDictionary[GiveawayKey, asyncio.Lock] = (
            weakref.WeakValueDictionary()
        )
        self._pending_updates: dict[GiveawayKey, asyncio.Task] = {}

    # when the bot restarts, it will, on load, activate all views for
    # any currently active giveaways
    async def cog_load(self):
        giveaways = await database.get_all(models.GiveawayModel, ended=False)

        for giveaway in giveaways:
            # a start that crashed before sending leaves a row with no message
            if giveaway.message_id:
                self._bot.add_view(
                    GiveawayView(self, giveaway.guild_id, giveaway.id),
                    message_id=giveaway.message_id,
                )

        self._expiry_loop.start()

    def cog_unload(self):
        self._expiry_loop.cancel()

        for task in self._pending_updates.values():
            task.cancel()

    def lock(self, key: GiveawayKey) -> asyncio.Lock:
        # one lock per giveaway, so ending, rerolling and edits never interleave
        lock = self._locks.get(key)
        if lock is None:
            lock = self._locks[key] = asyncio.Lock()

        return lock

    async def get_giveaway(self, key: GiveawayKey) -> models.GiveawayModel:
        giveaway = await database.get(models.GiveawayModel, guild_id=key[0], id=key[1])

        if giveaway is None:
            raise lyerrors.TakinaNotFoundError(f"Giveaway `#{key[1]}` does not exist.")

        return giveaway

    async def next_id(self, guild_id: int) -> int:
        latest = await database.get_all(
            models.GiveawayModel,
            guild_id=guild_id,
            order_by=col(models.GiveawayModel.id).desc(),
            limit=1,
        )
        return latest[0].id + 1 if latest else 1

    async def _get_channel(self, channel_id: int) -> GiveawayChannel | None:
        channel = self._bot.get_channel(channel_id)

        if channel is None:
            try:
                channel = await self._bot.fetch_channel(channel_id)
            except discord.NotFound:
                return None

        if isinstance(
            channel,
            discord.TextChannel | discord.Thread | discord.VoiceChannel | discord.StageChannel,
        ):
            return channel

        return None

    async def _get_message(self, giveaway: models.GiveawayModel) -> discord.Message | None:
        channel = await self._get_channel(giveaway.channel_id)
        if channel is None:
            return None

        try:
            return await channel.fetch_message(giveaway.message_id)
        except discord.NotFound:
            return None

    async def _edit_message(self, giveaway: models.GiveawayModel) -> None:
        if message := await self._get_message(giveaway):
            view = GiveawayView(self, giveaway.guild_id, giveaway.id, ended=giveaway.ended)
            await message.edit(embed=giveaway_embed(giveaway), view=view)

    def schedule_update(self, key: GiveawayKey) -> None:
        if key not in self._pending_updates:
            self._pending_updates[key] = asyncio.create_task(self._delayed_update(key))

    async def _delayed_update(self, key: GiveawayKey) -> None:
        await asyncio.sleep(EDIT_DELAY)
        # entries from here on schedule a fresh edit
        del self._pending_updates[key]

        try:
            async with self.lock(key):
                giveaway = await database.get(models.GiveawayModel, guild_id=key[0], id=key[1])
                if giveaway and not giveaway.ended:
                    await self._edit_message(giveaway)
        except discord.HTTPException as error:
            logger.warning(f"could not update giveaway {key}: {error}")

    async def _end(self, giveaway: models.GiveawayModel) -> list[int] | None:
        """
        Draw and announce the winners. Hold the giveaway's lock while calling this.
        Returns None when the message is gone, which ends the giveaway without a draw.
        """
        giveaway.ended = True
        message = await self._get_message(giveaway)

        if message is None:
            await database.save(giveaway)
            return None

        participants = list(giveaway.participants)
        giveaway.winner_ids = random.sample(participants, min(giveaway.winners, len(participants)))
        await database.save(giveaway)

        await self._edit_message(giveaway)

        if giveaway.winner_ids:
            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.description = f"Congratulations! You have won giveaway `#{giveaway.id}`!"
            await message.channel.send(mentions(giveaway.winner_ids), embed=embed)

        return giveaway.winner_ids

    @tasks.loop(seconds=30)
    async def _expiry_loop(self):
        try:
            giveaways = await database.get_all(
                models.GiveawayModel,
                where=[models.GiveawayModel.ends_at <= datetime.now(UTC)],
                ended=False,
            )
        except Exception:
            # an unhandled error stops tasks.loop for good, so wait for the next tick instead
            logger.exception("failed to fetch giveaways")
            return

        for giveaway in giveaways:
            key = (giveaway.guild_id, giveaway.id)
            try:
                async with self.lock(key):
                    # read again under the lock, in case stop got there first
                    giveaway = await database.get(models.GiveawayModel, guild_id=key[0], id=key[1])
                    if giveaway and not giveaway.ended:
                        await self._end(giveaway)
            except Exception:
                # one broken giveaway must not stop the others from ending
                logger.exception(f"failed to end giveaway {key}")

    @_expiry_loop.before_loop
    async def _before_expiry_loop(self):
        await self._bot.wait_until_ready()

    async def confirm(self, ctx: commands.Context, description: str) -> None:
        if ctx.interaction:
            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.description = f"{config.emojis.SUCCESS} {description}"
            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.message.add_reaction(config.emojis.SUCCESS)

    @commands.hybrid_group(
        name="giveaway", description="Giveaway management commands.", invoke_without_command=True
    )
    @lychecks.guild_only()
    async def giveaway(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @giveaway.command(
        name="start", description="Start a giveaway.", usage='5h "title" "description" 2'
    )
    @lychecks.has_permissions(manage_events=True)
    @lychecks.guild_only()
    async def start(
        self,
        ctx: commands.Context,
        duration: str,
        title: Title,
        description: str | None = None,
        winners: commands.Range[int, 1, MAX_WINNERS] = 1,
    ):
        assert ctx.guild is not None

        # a Range inside an optional loses its limit on slash, so this one is checked by hand
        if description and len(description) > MAX_DESCRIPTION_LENGTH:
            raise lyerrors.TakinaUserInputError(
                f"The description can be at most {MAX_DESCRIPTION_LENGTH:,} characters long."
            )

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
        elif duration_parsed >= MAX_DURATION:
            raise lyerrors.TakinaUserInputError(
                "The duration of the giveaway must be less than one year."
            )

        ends_at = datetime.now(UTC).replace(microsecond=0) + timedelta(seconds=duration_parsed)

        # the row comes first, so a failed send never leaves a live message without one
        for _ in range(MAX_ID_ATTEMPTS):
            try:
                giveaway = await database.insert(
                    models.GiveawayModel(
                        guild_id=ctx.guild.id,
                        id=await self.next_id(ctx.guild.id),
                        channel_id=ctx.channel.id,
                        message_id=0,
                        title=title,
                        description=description or "",
                        ends_at=ends_at,
                        winners=winners,
                    )
                )
                break
            except IntegrityError:
                # another giveaway took this id first
                continue
        else:
            raise lyerrors.TakinaError("Could not allocate a giveaway ID, please try again.")

        view = GiveawayView(self, ctx.guild.id, giveaway.id)
        try:
            message = await ctx.channel.send(embed=giveaway_embed(giveaway), view=view)
        except discord.HTTPException:
            await database.delete(giveaway)
            raise

        giveaway.message_id = message.id
        await database.save(giveaway)

        self._bot.add_view(view, message_id=message.id)

        if ctx.interaction:
            await self.confirm(ctx, f"Giveaway `#{giveaway.id}` has been started.")

    @giveaway.command(name="stop", aliases=["end"], description="End a giveaway.", usage="1")
    @lychecks.has_permissions(manage_events=True)
    @lychecks.guild_only()
    async def stop(self, ctx: commands.Context, giveaway_id: int):
        assert ctx.guild is not None
        key = (ctx.guild.id, giveaway_id)

        async with self.lock(key):
            giveaway = await self.get_giveaway(key)

            if giveaway.ended:
                raise lyerrors.TakinaError(f"Giveaway `#{giveaway_id}` has already ended.")

            winners = await self._end(giveaway)

        if winners is None:
            raise lyerrors.TakinaNotFoundError(
                f"Giveaway `#{giveaway_id}` has ended, but its message was gone, so no winners were drawn."
            )

        await self.confirm(ctx, f"Successfully ended giveaway `#{giveaway_id}`.")

    @giveaway.command(
        description="Redraw a giveaway's winners from everyone who has not won it yet.", usage="1"
    )
    @lychecks.has_permissions(manage_events=True)
    @lychecks.guild_only()
    async def reroll(self, ctx: commands.Context, giveaway_id: int):
        assert ctx.guild is not None
        key = (ctx.guild.id, giveaway_id)

        async with self.lock(key):
            giveaway = await self.get_giveaway(key)

            if not giveaway.ended:
                raise lyerrors.TakinaError(f"Giveaway `#{giveaway_id}` has not ended yet.")

            # winner_ids too, since giveaways from before past_winner_ids existed lack them
            previous_winners = list(dict.fromkeys(giveaway.past_winner_ids + giveaway.winner_ids))
            eligible = [
                user_id for user_id in giveaway.participants if user_id not in previous_winners
            ]

            if not eligible:
                raise lyerrors.TakinaError("Everyone who entered this giveaway has already won it.")

            giveaway.past_winner_ids = previous_winners
            giveaway.winner_ids = random.sample(eligible, min(giveaway.winners, len(eligible)))
            await database.save(giveaway)

            message = await self._get_message(giveaway)
            if message:
                await self._edit_message(giveaway)

                embed = discord.Embed(colour=config.EMBED_COLOUR)
                embed.description = (
                    f"Congratulations! Due to a reroll, you have won giveaway `#{giveaway.id}`!"
                )
                await message.channel.send(mentions(giveaway.winner_ids), embed=embed)

        await self.confirm(ctx, f"Giveaway `#{giveaway_id}` has been rerolled.")

    @giveaway.command(description="View the details of a past giveaway.", usage="1")
    @lychecks.has_permissions(manage_events=True)
    @lychecks.guild_only()
    async def view(self, ctx: commands.Context, giveaway_id: int):
        assert ctx.guild is not None
        giveaway = await self.get_giveaway((ctx.guild.id, giveaway_id))

        if not giveaway.ended:
            raise lyerrors.TakinaError(f"Giveaway `#{giveaway_id}` has not ended yet.")

        await ctx.reply(
            embed=giveaway_embed(giveaway),
            mention_author=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaways(bot))
