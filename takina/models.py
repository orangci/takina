from sqlmodel import Field, SQLModel
from sqlalchemy import BigInteger


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
