# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import case, func, inspect, update
from sqlalchemy.engine import Connection
from sqlmodel import SQLModel, select
from collections.abc import Iterable
from alembic.config import Config
from typing import Any, cast
from alembic import command
from takina import config
from pathlib import Path
import time
import copy

if not config.POSTGRESQL_URI:
    raise OSError(
        "You must set the POSTGRESQL_URI environment variable in order for the database (and by extension, the bot itself) to function."
    )

# pre_ping replaces connections that went stale, e.g. after postgres restarted
engine = create_async_engine(config.POSTGRESQL_URI, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


MIGRATIONS = Path(__file__).parent / "migrations"


def _upgrade(connection: Connection) -> None:
    alembic_config = Config()
    alembic_config.set_main_option("script_location", str(MIGRATIONS))
    alembic_config.attributes["connection"] = connection
    command.upgrade(alembic_config, "head")


async def initiate_database() -> None:
    # migrations, not create_all, so existing databases pick up schema changes too
    async with engine.begin() as connection:
        await connection.run_sync(_upgrade)


# rows read on every message or reaction, cached by primary key so the hot path skips postgres.
# save(), delete() and toggle_in_array() keep it current; the expiry only covers changes made
# outside the bot, such as by hand in psql
CACHED_TABLES = {
    "prefixes",
    "guild_settings",
    "trigger_responses",
    "starboard_settings",
    "afk_statuses",
}
CACHE_SECONDS = 5 * 60
MAX_CACHE_ENTRIES = 10_000

type CacheKey = tuple[str, tuple[Any, ...]]

# a miss is cached as None, since most servers have no settings row at all
_cache: dict[CacheKey, tuple[float, SQLModel | None]] = {}
# bumped by every write, so a read that raced a write does not cache what it saw
_generations: dict[CacheKey, int] = {}


def _cache_key(model: type[SQLModel], filters: dict[str, Any]) -> CacheKey | None:
    table = getattr(model, "__tablename__", None)
    if table not in CACHED_TABLES:
        return None

    primary_key = [column.key for column in inspect(model).primary_key]
    if sorted(filters) != sorted(primary_key):
        return None

    return str(table), tuple(filters[key] for key in primary_key)


def _forget(instance: SQLModel) -> None:
    model = type(instance)
    primary_key = {
        column.key: getattr(instance, column.key) for column in inspect(model).primary_key
    }
    if (key := _cache_key(model, primary_key)) is not None:
        _cache.pop(key, None)
        _generations[key] = _generations.get(key, 0) + 1


def _forget_table(model: type[SQLModel]) -> None:
    table = getattr(model, "__tablename__", None)
    for key in [key for key in _cache if key[0] == table]:
        _cache.pop(key, None)
        _generations[key] = _generations.get(key, 0) + 1


def _copy[T: SQLModel](instance: T | None) -> T | None:
    # callers change the rows they get back, so the cache only ever hands out copies
    if instance is None:
        return None

    fields = type(instance).model_fields
    return type(instance)(**{name: copy.deepcopy(getattr(instance, name)) for name in fields})


def _remember(key: CacheKey, generation: int, instance: SQLModel | None) -> None:
    if _generations.get(key, 0) != generation:
        return

    now = time.monotonic()
    if len(_cache) >= MAX_CACHE_ENTRIES:
        for stale_key in [k for k, (at, _) in _cache.items() if now - at >= CACHE_SECONDS]:
            del _cache[stale_key]

        if len(_cache) >= MAX_CACHE_ENTRIES:
            _cache.clear()

    _cache[key] = (now, _copy(instance))


def _has_primary_key(instance: SQLModel) -> bool:
    mapper = inspect(type(instance))
    return all(getattr(instance, column.key) is not None for column in mapper.primary_key)


async def get[T: SQLModel](model: type[T], **filters) -> T | None:
    cache_key = _cache_key(model, filters)
    if cache_key is not None:
        cached = _cache.get(cache_key)
        if cached is not None and time.monotonic() - cached[0] < CACHE_SECONDS:
            return cast("T | None", _copy(cached[1]))

        generation = _generations.get(cache_key, 0)

    async with SessionLocal() as session:
        statement = select(model)

        for key, value in filters.items():
            statement = statement.where(getattr(model, key) == value)

        result = await session.execute(statement)
        instance = result.scalar_one_or_none()

    if cache_key is not None:
        _remember(cache_key, generation, instance)

    return instance


async def get_all[T: SQLModel](
    model: type[T],
    *,
    where: Iterable[Any] = (),
    order_by: Any = None,
    limit: int | None = None,
    **filters,
) -> list[T]:
    async with SessionLocal() as session:
        statement = select(model)

        for key, value in filters.items():
            statement = statement.where(getattr(model, key) == value)

        # sqlalchemy expressions, e.g. models.ReminderModel.remind_at <= now
        for clause in where:
            statement = statement.where(clause)

        if order_by is not None:
            statement = statement.order_by(order_by)

        if limit is not None:
            statement = statement.limit(limit)

        result = await session.execute(statement)
        return list(result.scalars().all())


async def get_or_create[T: SQLModel](
    model: type[T], defaults: dict[str, Any] | None = None, **filters
) -> T:
    # a new instance is not saved yet; callers fill it in and call save()
    instance = await get(model, **filters)
    if instance is None:
        instance = model(**filters, **(defaults or {}))

    return instance


async def save[T: SQLModel](instance: T) -> T:
    async with SessionLocal() as session:
        if _has_primary_key(instance):
            # merge updates the row with this primary key, or inserts it if there is none
            instance = await session.merge(instance)
        else:
            # add lets autoincrement ids flow back into the caller's instance
            session.add(instance)

        await session.commit()
        await session.refresh(instance)

    _forget(instance)
    return instance


async def toggle_in_array[T: SQLModel](
    model: type[T], column: str, value: Any, **filters
) -> T | None:
    # one atomic update, so concurrent toggles cannot overwrite each other
    array = getattr(model, column)
    statement = (
        update(model)
        .where(*(getattr(model, key) == filter_value for key, filter_value in filters.items()))
        .values(
            {
                column: case(
                    (array.any(value), func.array_remove(array, value)),
                    else_=func.array_append(array, value),
                )
            }
        )
        .returning(model)
    )

    async with SessionLocal() as session:
        result = await session.execute(statement)
        instance = result.scalar_one_or_none()
        await session.commit()

    _forget_table(model)
    return instance


async def delete[T: SQLModel](instance: T) -> None:
    async with SessionLocal() as session:
        # merge first: rows from the cache are copies the session has never seen
        await session.delete(await session.merge(instance))
        await session.commit()

    _forget(instance)
