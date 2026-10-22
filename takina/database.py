# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from collections.abc import Iterable
from sqlmodel import SQLModel, select
from sqlalchemy import inspect
from typing import Any
from takina import config

if not config.POSTGRESQL_URI:
    raise OSError(
        "You must set the POSTGRESQL_URI environment variable in order for the database (and by extension, the bot itself) to function."
    )

# pre_ping replaces connections that went stale, e.g. after postgres restarted
engine = create_async_engine(config.POSTGRESQL_URI, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def initiate_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


def _has_primary_key(instance: SQLModel) -> bool:
    mapper = inspect(type(instance))
    return all(getattr(instance, column.key) is not None for column in mapper.primary_key)


async def get[T: SQLModel](model: type[T], **filters) -> T | None:
    async with SessionLocal() as session:
        statement = select(model)

        for key, value in filters.items():
            statement = statement.where(getattr(model, key) == value)

        result = await session.execute(statement)
        return result.scalar_one_or_none()


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
        return instance


async def delete[T: SQLModel](instance: T) -> None:
    async with SessionLocal() as session:
        await session.delete(instance)
        await session.commit()
