from sqlalchemy.dialects.postgresql import ARRAY as PGArray
from sqlmodel import Field, SQLModel, Column, DateTime
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import BigInteger
from datetime import datetime


class PrefixModel(SQLModel, table=True):
    __tablename__: str = "prefixes"

    guild_id: int = Field(sa_type=BigInteger, primary_key=True)
    prefix: str


class UserSettingsModel(SQLModel, table=True):
    __tablename__ = "user_settings"
    user_id: int = Field(sa_type=BigInteger, primary_key=True)


class GuildSettingsModel(SQLModel, table=True):
    __tablename__ = "guild_settings"
    guild_id: int = Field(sa_type=BigInteger, primary_key=True)


class AFKStatusModel(SQLModel, table=True):
    __tablename__: str = "afk_statuses"

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

    ends_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))

    ended: bool = False
    winner_ids: list[int] = Field(
        default_factory=list, sa_column=Column(MutableList.as_mutable(PGArray(BigInteger)))
    )
    winners: int = 1
