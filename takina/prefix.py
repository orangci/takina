from sqlmodel import Field, SQLModel
from sqlalchemy import BigInteger
from discord.ext import commands
from takina import database
import discord
import os


async def get_prefix(bot: commands.Bot, message: discord.Message) -> list[str]:
    default_prefixes = [".", "takina ", "Takina "]

    if message.guild is None:
        return default_prefixes

    prefix = await database.get(PrefixModel, guild_id=message.guild.id)

    if prefix is not None:
        return [prefix.prefix, "takina ", "Takina "]

    if env_prefix := os.getenv("PREFIX"):
        return [env_prefix]

    return default_prefixes


class PrefixModel(SQLModel, table=True):
    __tablename__: str = "prefixes"

    guild_id: int = Field(sa_type=BigInteger, primary_key=True)
    prefix: str
