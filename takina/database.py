from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from collections.abc import AsyncGenerator
from sqlmodel import SQLModel, select
from typing import TypeVar
from takina import config


T = TypeVar("T", bound=SQLModel)

engine = create_async_engine(config.POSTGRESQL_URI, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def initiate_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def get(model: type[T], **filters) -> T | None:
    async with SessionLocal() as session:
        statement = select(model)

        for key, value in filters.items():
            statement = statement.where(getattr(model, key) == value)

        result = await session.execute(statement)
        return result.scalar_one_or_none()


async def get_all(model: type[T], **filters) -> list[T]:
    async with SessionLocal() as session:
        statement = select(model)

        for key, value in filters.items():
            statement = statement.where(getattr(model, key) == value)

        result = await session.execute(statement)
        return list(result.scalars().all())


async def save(instance: T) -> None:
    async with SessionLocal() as session:
        session.add(instance)
        await session.commit()
        await session.refresh(instance)


async def delete(instance: T) -> None:
    async with SessionLocal() as session:
        await session.delete(instance)
        await session.commit()
