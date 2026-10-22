# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from collections.abc import Awaitable, Callable, Sequence
from takina import config, database, models
from takina.libs import lyerrors, lyviews
from sqlalchemy.exc import IntegrityError
from datetime import datetime, UTC
from discord.ext import commands
from contextlib import suppress
import discord

MAX_CASE_ATTEMPTS = 5
MAX_MASS_TARGETS = 10
# audit log reasons cap at 512, and "Banned by <moderator> for: " needs room too
MAX_REASON_LENGTH = 400

Reason = commands.Range[str, 1, MAX_REASON_LENGTH]

PAST_TENSE = {
    "ban": "banned",
    "hackban": "hackbanned",
    "unban": "unbanned",
    "kick": "kicked",
    "mute": "muted",
    "unmute": "unmuted",
    "warn": "warned",
}


async def next_case_id(guild_id: int) -> int:
    cases = await database.get_all(models.ModLogCaseModel, guild_id=guild_id)
    if not cases:
        # we start the server's cases with case #0, not #1
        # because #0 has more aura
        return 0

    return max(case.case_id for case in cases) + 1


async def log_action(
    guild: discord.Guild,
    action: str,
    targets: Sequence[discord.Member | discord.User],
    reason: str,
    moderator: discord.Member | discord.User | discord.ClientUser,
    duration: str | None = None,
    *,
    mass_action: bool = False,
) -> None:
    settings = await database.get(models.GuildSettingsModel, guild_id=guild.id)
    timestamp = datetime.now(UTC)

    # another action may claim the same case id first, so retry with a fresh one
    for _ in range(MAX_CASE_ATTEMPTS):
        case = models.ModLogCaseModel(
            guild_id=guild.id,
            case_id=await next_case_id(guild.id),
            action=action,
            member_ids=[target.id for target in targets],
            member_names=[str(target) for target in targets],
            moderator_id=moderator.id,
            reason=reason,
            duration=duration,
            timestamp=timestamp,
            mass_action=mass_action,
        )

        try:
            await database.save(case)
            break
        except IntegrityError:
            continue
    else:
        raise lyerrors.TakinaError("Could not allocate a modlog case ID, please try again.")

    if not settings or not settings.modlog_channel_id:
        return

    channel = guild.get_channel(settings.modlog_channel_id)
    if not isinstance(channel, discord.TextChannel):
        return

    action_name = f"{action.title()} ({duration})" if duration else action.title()

    embed = discord.Embed(colour=config.EMBED_COLOUR)
    embed.timestamp = timestamp
    embed.add_field(name="Action", value=action_name, inline=True)
    embed.add_field(name="Case", value=f"#{case.case_id}", inline=True)
    embed.add_field(name="Moderator", value=moderator.mention, inline=True)

    if mass_action:
        embed.add_field(
            name="Targets", value=", ".join(target.mention for target in targets), inline=False
        )
    else:
        embed.add_field(name="Target", value=targets[0].mention, inline=False)

    embed.add_field(name="Reason", value=reason, inline=False)

    if not mass_action and targets[0].avatar:
        embed.set_thumbnail(url=targets[0].avatar.url)

    await channel.send(embed=embed)


def mass_targets[T: (discord.Member, discord.User)](targets: Sequence[T], action: str) -> list[T]:
    # greedy converters happily accept the same member twice
    unique_targets = list(dict.fromkeys(targets))

    if len(unique_targets) < 2:
        raise lyerrors.TakinaUserInputError(f"You must specify at least two members to {action}.")

    if len(unique_targets) > MAX_MASS_TARGETS:
        raise lyerrors.TakinaUserInputError(
            f"You cannot {action} more than {MAX_MASS_TARGETS} members at once."
        )

    return unique_targets


async def _send_dm(
    target: discord.Member | discord.User, text: str, reason: str
) -> discord.Message | None:
    embed = discord.Embed(colour=config.EMBED_COLOUR)
    embed.description = f"{text}\n\n{config.emojis.NOTE} **Reason**: {reason}"

    try:
        return await target.send(embed=embed)
    except discord.HTTPException:
        return None


async def moderate[T: (discord.Member, discord.User)](
    ctx: commands.Context,
    targets: Sequence[T],
    action: str,
    reason: str,
    apply: Callable[[T, str], Awaitable[object]] | None,
    dm: str | None,
    *,
    dm_first: bool = False,
    duration: str | None = None,
) -> None:
    """
    Confirm, act on every target, DM them, report back and log the case.

    Pass `dm_first` when the target cannot be reached afterwards (bans and kicks);
    the DM is then deleted again if the action fails.

    Example:
        await lymodlog.moderate(
            ctx,
            [member],
            "kick",
            reason,
            lambda member, audit_reason: member.kick(reason=audit_reason),
            f"You were kicked from **{ctx.guild}**.",
            dm_first=True,
        )
    """
    assert ctx.guild is not None

    past = PAST_TENSE[action]
    mass_action = len(targets) > 1
    name = f"mass {action}" if mass_action else action
    for_duration = f" for {duration}" if duration else ""
    audit_reason = f"{past.capitalize()} by {ctx.author} for: {reason}"

    confirmation = lyviews.ModerationConfirmationView(
        ctx=ctx, member=", ".join(target.mention for target in targets), action=name, reason=reason
    )
    if not await confirmation.prompt():
        return

    succeeded: list[T] = []
    failed: list[str] = []
    undelivered = 0

    for target in targets:
        dm_message = await _send_dm(target, dm, reason) if dm and dm_first else None

        if apply is not None:
            try:
                await apply(target, audit_reason)
            except discord.HTTPException as error:
                failed.append(f"{target.mention} ({error.text or error.status})")
                if dm_message is not None:
                    with suppress(discord.HTTPException):
                        await dm_message.delete()
                continue

        if dm and not dm_first:
            dm_message = await _send_dm(target, dm, reason)

        if dm and dm_message is None:
            undelivered += 1

        succeeded.append(target)

    if not succeeded:
        raise lyerrors.TakinaError(f"I could not {action} {', '.join(failed)}.")

    mentions = ", ".join(target.mention for target in succeeded)

    embed = discord.Embed(colour=config.EMBED_COLOUR)
    if not mass_action:
        embed.description = f"{config.emojis.SUCCESS} Successfully {past} {mentions}{for_duration}."
    elif failed:
        embed.description = f"{config.emojis.SUCCESS} Successfully {past} {len(succeeded)} of {len(targets)} members{for_duration}: {mentions}."
        embed.description += f"\n\n{config.emojis.ERROR} **Failed**: {', '.join(failed)}"
    else:
        embed.description = f"{config.emojis.SUCCESS} Successfully {past} the following {len(targets)} members{for_duration}: {mentions}."

    embed.description += f"\n\n{config.emojis.NOTE} **Reason**: {reason}"
    embed.description += f"\n{config.emojis.MODERATOR} **Moderator**: {ctx.author}"

    if undelivered:
        embed.set_footer(
            text="I was unable to DM the user."
            if not mass_action
            else f"I was unable to DM {undelivered} user(s)."
        )

    await confirmation.edit_success(embed)
    await log_action(
        ctx.guild, name, succeeded, reason, ctx.author, duration, mass_action=mass_action
    )
