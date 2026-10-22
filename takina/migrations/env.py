# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from sqlalchemy.ext.asyncio import async_engine_from_config
from takina import config as takina_config, models  # noqa: F401  (models registers the tables)
from logging.config import fileConfig
from sqlalchemy.engine import Connection
from sqlmodel import SQLModel
from sqlalchemy import pool
from alembic import context
import asyncio

config = context.config

# the bot calls migrations with logging already set up; the alembic cli brings alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

if not takina_config.POSTGRESQL_URI:
    raise OSError("You must set the POSTGRESQL_URI environment variable to run migrations.")

# configparser treats % as interpolation, and urls may contain percent-encoding
config.set_main_option("sqlalchemy.url", takina_config.POSTGRESQL_URI.replace("%", "%%"))

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


def run_migrations_online() -> None:
    # the bot passes its own connection, since it is already inside an event loop
    connection = config.attributes.get("connection")
    if connection is not None:
        do_run_migrations(connection)
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
