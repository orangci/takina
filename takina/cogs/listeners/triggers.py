# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors, lychecks, lyhelpers, lyviews
from takina import config, database, models
from discord.ext import commands
import discord
import time
import re

MAX_TRIGGERS = 30
MIN_TRIGGER_LEN = 2
MAX_TRIGGER_NAME_LEN = 20
MAX_TRIGGER_LEN = 75
MAX_RESPONSE_LEN = 500
# seconds before the same trigger may fire again in a channel
TRIGGER_COOLDOWN = 10
TRIGGERS_PER_PAGE = 5


def trigger_pattern(trigger: str) -> re.Pattern[str]:
    # lookarounds rather than \b, so triggers that start or end with punctuation still match
    return re.compile(rf"(?<!\w){re.escape(trigger)}(?!\w)", re.IGNORECASE)


class TriggerResponses(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        # (channel id, trigger name) to when it last fired, on the monotonic clock
        self._last_fired: dict[tuple[int, str], float] = {}

    async def get_guild_triggers(self, guild_id: int) -> models.TriggerResponsesModel:
        # unsaved for a new guild; the commands that change triggers save it themselves
        return await database.get_or_create(models.TriggerResponsesModel, guild_id=guild_id)

    @commands.hybrid_group(
        name="trigger", description="Manage trigger responses.", invoke_without_command=True
    )
    @lychecks.guild_only()
    async def trigger(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @trigger.command(
        name="add",
        description="Add a new trigger response.",
        usage='r1999 "reverse: 1999" "Reverse: 1999 is PEAK"',
    )
    @lychecks.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def add_trigger(
        self, ctx: commands.Context, name: str, trigger: str, response: str
    ) -> None:
        assert ctx.guild is not None
        trigger = trigger.strip()

        if len(trigger) < MIN_TRIGGER_LEN:
            raise lyerrors.TakinaUserInputError(
                f"Trigger text must be at least {MIN_TRIGGER_LEN} characters long."
            )

        if len(name) > MAX_TRIGGER_NAME_LEN:
            raise lyerrors.TakinaUserInputError(
                f"Trigger name cannot exceed {MAX_TRIGGER_NAME_LEN} characters."
            )

        if len(trigger) > MAX_TRIGGER_LEN:
            raise lyerrors.TakinaUserInputError(
                f"Trigger text cannot exceed {MAX_TRIGGER_LEN} characters."
            )

        if len(response) > MAX_RESPONSE_LEN:
            raise lyerrors.TakinaUserInputError(
                f"Trigger response text cannot exceed {MAX_RESPONSE_LEN} characters."
            )

        settings = await self.get_guild_triggers(ctx.guild.id)

        for trigger_data in settings.triggers.values():
            if trigger_data["trigger"].casefold() == trigger.casefold():
                raise lyerrors.TakinaError(f"A trigger with the text `{trigger}` already exists.")

        if len(settings.triggers) >= MAX_TRIGGERS:
            raise lyerrors.TakinaError(f"Maximum of {MAX_TRIGGERS} triggers reached.")

        if name in settings.triggers:
            raise lyerrors.TakinaError(f"A trigger with the name `{name}` already exists.")

        settings.triggers[name] = {"trigger": trigger, "response": response}
        await database.save(settings)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Trigger `{name}` added."
        await ctx.reply(embed=embed, mention_author=False)

    @trigger.command(
        name="remove",
        aliases=["delete", "rm"],
        description="Remove an existing trigger.",
        usage="r1999",
    )
    @lychecks.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def remove_trigger(self, ctx: commands.Context, name: str) -> None:
        assert ctx.guild is not None

        settings = await self.get_guild_triggers(ctx.guild.id)
        if name not in settings.triggers:
            raise lyerrors.TakinaError(f"No trigger with the name `{name}` exists.")

        del settings.triggers[name]
        await database.save(settings)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Trigger `{name}` removed."
        await ctx.reply(embed=embed, mention_author=False)

    @trigger.command(name="list", description="List all triggers for the server.")
    @lychecks.guild_only()
    async def list_triggers(self, ctx: commands.Context) -> None:
        assert ctx.guild is not None

        settings = await self.get_guild_triggers(ctx.guild.id)
        if not settings.triggers:
            raise lyerrors.TakinaError("No triggers are set for this server.")

        title = f"{await lyhelpers.fetch_random_emoji()}Trigger List"
        entries = [
            f"- `{name}`:\nTrigger — {data['trigger']}\nResponse — {data['response']}"
            for name, data in settings.triggers.items()
        ]

        # whole entries per page, so a trigger never ends up apart from its response
        embeds: list[discord.Embed] = []
        for chunk in lyhelpers.chunked(entries, TRIGGERS_PER_PAGE):
            embed = discord.Embed(title=title, colour=config.EMBED_COLOUR)
            embed.description = "\n".join(chunk)
            embeds.append(embed)

        if len(embeds) == 1:
            await ctx.reply(embed=embeds[0], mention_author=False)
            return

        await lyviews.PaginatorView.send(ctx, embeds)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        prefixes = await self._bot.get_prefix(message)
        if isinstance(prefixes, str):
            prefixes = [prefixes]

        if any(message.content.startswith(prefix) for prefix in prefixes):
            return

        settings = await database.get(models.TriggerResponsesModel, guild_id=message.guild.id)
        if not settings:
            return

        for name, data in settings.triggers.items():
            if not trigger_pattern(data["trigger"]).search(message.content):
                continue

            key = (message.channel.id, name)
            now = time.monotonic()
            if now - self._last_fired.get(key, -TRIGGER_COOLDOWN) < TRIGGER_COOLDOWN:
                return

            self._last_fired[key] = now
            await message.channel.send(
                data["response"], allowed_mentions=discord.AllowedMentions.none()
            )
            return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TriggerResponses(bot))
