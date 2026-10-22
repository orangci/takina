# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina import config, database, models
from sqlalchemy.exc import IntegrityError
from collections.abc import Sequence
from datetime import datetime, UTC
from takina.libs import lyerrors
import discord

MAX_CASE_ATTEMPTS = 5


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
