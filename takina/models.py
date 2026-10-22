# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from sqlmodel import Field, SQLModel, Column, DateTime, String, JSON
from sqlalchemy.dialects.postgresql import ARRAY as PGArray
from sqlalchemy.ext.mutable import MutableList, MutableDict
from sqlalchemy import BigInteger, UniqueConstraint
from datetime import datetime
from secrets import token_hex
from typing import TypedDict


class PrefixModel(SQLModel, table=True):
    __tablename__ = "prefixes"

    guild_id: int = Field(sa_type=BigInteger, primary_key=True)
    prefix: str


class UserSettingsModel(SQLModel, table=True):
    __tablename__ = "user_settings"
    user_id: int = Field(sa_type=BigInteger, primary_key=True)


class GuildSettingsModel(SQLModel, table=True):
    __tablename__ = "guild_settings"
    guild_id: int = Field(sa_type=BigInteger, primary_key=True)

    modlog_channel_id: int | None = Field(default=None, sa_type=BigInteger)
    honeypot_channel_id: int | None = Field(default=None, sa_type=BigInteger)
    reports_channel_id: int | None = Field(default=None, sa_type=BigInteger)
    reports_notification_role_id: int | None = Field(default=None, sa_type=BigInteger)


class AFKStatusModel(SQLModel, table=True):
    __tablename__ = "afk_statuses"

    user_id: int = Field(sa_type=BigInteger, primary_key=True)
    status: str


class GiveawayModel(SQLModel, table=True):
    __tablename__ = "giveaways"

    guild_id: int = Field(sa_type=BigInteger, primary_key=True)
    id: int = Field(primary_key=True)

    channel_id: int = Field(sa_type=BigInteger)
    message_id: int = Field(sa_type=BigInteger)

    title: str
    description: str
    button_emoji: str | None = None

    participants: list[int] = Field(
        default_factory=list, sa_column=Column(MutableList.as_mutable(PGArray(BigInteger)))
    )

    ends_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    ended: bool = False
    winner_ids: list[int] = Field(
        default_factory=list, sa_column=Column(MutableList.as_mutable(PGArray(BigInteger)))
    )
    winners: int = 1


class ReminderModel(SQLModel, table=True):
    __tablename__ = "reminders"

    id: str = Field(default_factory=lambda: token_hex(12), primary_key=True)
    user_id: int = Field(sa_type=BigInteger, index=True)
    reminder: str
    remind_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )


class ModLogCaseModel(SQLModel, table=True):
    __tablename__ = "modlog_cases"
    __table_args__ = (UniqueConstraint("guild_id", "case_id", name="uq_modlog_guild_case"),)

    id: int | None = Field(default=None, primary_key=True)
    guild_id: int = Field(sa_type=BigInteger, index=True)
    case_id: int
    action: str
    member_ids: list[int] = Field(
        default_factory=list, sa_column=Column(MutableList.as_mutable(PGArray(BigInteger)))
    )
    member_names: list[str] = Field(
        default_factory=list, sa_column=Column(MutableList.as_mutable(PGArray(String)))
    )
    moderator_id: int = Field(sa_type=BigInteger)
    reason: str
    duration: str | None = None
    timestamp: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    mass_action: bool = False
    # where the case was posted, so edits can update that message
    log_channel_id: int | None = Field(default=None, sa_type=BigInteger)
    log_message_id: int | None = Field(default=None, sa_type=BigInteger)


class StarboardSettingsModel(SQLModel, table=True):
    __tablename__ = "starboard_settings"

    guild_id: int = Field(sa_type=BigInteger, primary_key=True)
    starboard_channel_id: int | None = Field(default=None, sa_type=BigInteger)
    minimum_reaction_count: int = 4
    whitelisted_channel_ids: list[int] = Field(
        default_factory=list, sa_column=Column(MutableList.as_mutable(PGArray(BigInteger)))
    )


class StarboardMessageModel(SQLModel, table=True):
    __tablename__ = "starboard_messages"

    message_id: int = Field(sa_type=BigInteger, primary_key=True)
    starboard_message_id: int = Field(sa_type=BigInteger)


class TriggerData(TypedDict):
    trigger: str
    response: str


class TriggerResponsesModel(SQLModel, table=True):
    __tablename__ = "trigger_responses"

    guild_id: int = Field(sa_type=BigInteger, primary_key=True)
    # entries are replaced whole; MutableDict does not see nested edits
    triggers: dict[str, TriggerData] = Field(
        default_factory=dict, sa_column=Column(MutableDict.as_mutable(JSON))
    )
