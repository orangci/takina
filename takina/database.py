from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from collections.abc import AsyncGenerator
from sqlmodel import SQLModel, select
from takina import config

engine = create_async_engine(config.POSTGRESQL_URI, echo=False)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def initiate_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def get(model: type[SQLModel], **filters):
    async with SessionLocal() as session:
        statement = select(model)

        for key, value in filters.items():
            statement = statement.where(getattr(model, key) == value)

        result = await session.execute(statement)
        return result.scalar_one_or_none()


async def save(instance: SQLModel) -> None:
    async with SessionLocal() as session:
        session.add(instance)
        await session.commit()
        await session.refresh(instance)


async def delete(instance: SQLModel) -> None:
    async with SessionLocal() as session:
        await session.delete(instance)
        await session.commit()
