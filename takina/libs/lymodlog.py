# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from collections.abc import Awaitable, Callable, Sequence
from takina import config, database, models
from takina.libs import lyerrors, lyviews
from sqlalchemy.exc import IntegrityError
from datetime import datetime, UTC
from discord.ext import commands
from contextlib import suppress
from sqlmodel import col
import logging
import discord

logger = logging.getLogger("takina.modlog")

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
    latest = await database.get_all(
        models.ModLogCaseModel,
        guild_id=guild_id,
        order_by=col(models.ModLogCaseModel.case_id).desc(),
        limit=1,
    )
    if not latest:
        # we start the server's cases with case #0, not #1
        # because #0 has more aura
        return 0

    return latest[0].case_id + 1


def case_embed(
    case: models.ModLogCaseModel,
    avatar_url: str | None = None,
    edited_by: discord.Member | discord.User | None = None,
) -> discord.Embed:
    action = f"{case.action.title()} ({case.duration})" if case.duration else case.action.title()
    targets = ", ".join(f"<@{member_id}>" for member_id in case.member_ids) or "Unknown"

    embed = discord.Embed(colour=config.EMBED_COLOUR)
    embed.timestamp = case.timestamp
    embed.add_field(name="Action", value=action, inline=True)
    embed.add_field(name="Case", value=f"#{case.case_id}", inline=True)
    embed.add_field(name="Moderator", value=f"<@{case.moderator_id}>", inline=True)
    embed.add_field(name="Targets" if case.mass_action else "Target", value=targets, inline=False)
    embed.add_field(name="Reason", value=case.reason, inline=False)

    if edited_by is not None:
        edited_at = int(datetime.now(UTC).timestamp())
        embed.add_field(
            name="Edited", value=f"By {edited_by.mention} <t:{edited_at}:R>", inline=False
        )

    if avatar_url and not case.mass_action:
        embed.set_thumbnail(url=avatar_url)

    return embed


async def log_action(
    guild: discord.Guild,
    action: str,
    targets: Sequence[discord.Member | discord.User],
    reason: str,
    moderator: discord.Member | discord.User | discord.ClientUser,
    duration: str | None = None,
    *,
    mass_action: bool = False,
) -> discord.Message | None:
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
        return None

    channel = guild.get_channel(settings.modlog_channel_id)
    if not isinstance(channel, discord.TextChannel):
        return None

    avatar = targets[0].avatar
    embed = case_embed(case, avatar.url if avatar else None)

    try:
        message = await channel.send(embed=embed)
    except discord.HTTPException as error:
        # the case is saved and the action done, so a broken log channel must not fail them
        logger.warning(f"could not post case #{case.case_id} in guild {guild.id}: {error}")
        return None

    case.log_channel_id = channel.id
    case.log_message_id = message.id
    await database.save(case)

    return message


async def update_logged_case(
    guild: discord.Guild, case: models.ModLogCaseModel, edited_by: discord.Member | discord.User
) -> None:
    if case.log_channel_id is None or case.log_message_id is None:
        return

    channel = guild.get_channel(case.log_channel_id)
    if not isinstance(channel, discord.TextChannel):
        return

    target = guild.get_member(case.member_ids[0]) if case.member_ids else None
    avatar_url = target.display_avatar.url if target else None

    try:
        await channel.get_partial_message(case.log_message_id).edit(
            embed=case_embed(case, avatar_url, edited_by)
        )
    except discord.HTTPException as error:
        logger.warning(f"could not update case #{case.case_id} in guild {guild.id}: {error}")


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
