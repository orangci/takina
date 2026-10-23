# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
"""
Every revision against a database of its own: up to head, down to nothing and back, and head
compared with the models, so a model change without its migration fails here, not on prod.
"""

from takina import database, models  # noqa: F401  (models registers the tables)
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from alembic.runtime.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from alembic.script import ScriptDirectory
from collections.abc import AsyncIterator
from sqlalchemy.engine import Connection
from sqlalchemy.pool import NullPool
from sqlalchemy import inspect, text
from alembic.config import Config
from sqlmodel import SQLModel
from alembic import command
from typing import Any
import secrets
import pytest


def alembic_config(connection: Connection | None = None) -> Config:
    alembic = Config()
    alembic.set_main_option("script_location", str(database.MIGRATIONS))
    alembic.attributes["connection"] = connection
    return alembic


@pytest.fixture
async def connection(postgres_uri: str) -> AsyncIterator[AsyncConnection]:
    """A connection to a brand new, empty database."""
    name = f"migrations_{secrets.token_hex(4)}"
    server = create_async_engine(postgres_uri, poolclass=NullPool, isolation_level="AUTOCOMMIT")
    async with server.connect() as admin:
        await admin.execute(text(f'CREATE DATABASE "{name}"'))

    engine = create_async_engine(
        postgres_uri.replace("/postgres?", f"/{name}?"), poolclass=NullPool
    )
    async with engine.connect() as connection:
        yield connection
    await engine.dispose()

    async with server.connect() as admin:
        await admin.execute(text(f'DROP DATABASE "{name}"'))
    await server.dispose()


def upgrade(connection: Connection, revision: str = "head") -> None:
    command.upgrade(alembic_config(connection), revision)
    connection.commit()


def downgrade(connection: Connection, revision: str) -> None:
    command.downgrade(alembic_config(connection), revision)
    connection.commit()


def tables(connection: Connection) -> set[str]:
    return set(inspect(connection).get_table_names()) - {"alembic_version"}


def differences(connection: Connection) -> list[Any]:
    return compare_metadata(MigrationContext.configure(connection), SQLModel.metadata)


def revisions() -> list[str]:
    script = ScriptDirectory.from_config(alembic_config())
    return [revision.revision for revision in reversed(list(script.walk_revisions()))]


async def test_head_matches_models(connection: AsyncConnection) -> None:
    await connection.run_sync(upgrade)
    assert await connection.run_sync(differences) == []
    assert await connection.run_sync(tables) == set(SQLModel.metadata.tables)


async def test_down_to_nothing_and_back(connection: AsyncConnection) -> None:
    await connection.run_sync(upgrade)
    await connection.run_sync(downgrade, "base")
    assert await connection.run_sync(tables) == set()

    await connection.run_sync(upgrade)
    assert await connection.run_sync(differences) == []


async def test_each_step_reverses(connection: AsyncConnection) -> None:
    # one revision at a time, so a downgrade that only works from head is caught too
    for revision in revisions():
        await connection.run_sync(upgrade, revision)
        await connection.run_sync(downgrade, "-1")
        await connection.run_sync(upgrade, revision)


def test_history_is_linear() -> None:
    script = ScriptDirectory.from_config(alembic_config())
    assert len(script.get_heads()) == 1, "several heads; merge them or rebase the revision"
    assert revisions()[0] == "b26edad3bb48", "the baseline must stay the first revision"


async def test_past_winners_backfilled(connection: AsyncConnection) -> None:
    # giveaways from before 8f67688cc8db must come out with an empty array, not null
    previous = revisions()[revisions().index("8f67688cc8db") - 1]
    await connection.run_sync(upgrade, previous)
    await connection.execute(
        text(
            "INSERT INTO giveaways (guild_id, id, channel_id, message_id, title, description,"
            " participants, ends_at, ended, winner_ids, winners)"
            " VALUES (1, 1, 2, 3, 'Fumo', '', '{}', now(), true, '{4}', 1)"
        )
    )
    await connection.commit()

    await connection.run_sync(upgrade)
    result = await connection.execute(text("SELECT past_winner_ids FROM giveaways"))
    assert result.scalar_one() == []


async def test_github_previews_default_on(connection: AsyncConnection) -> None:
    previous = revisions()[revisions().index("ad30e71b3d8a") - 1]
    await connection.run_sync(upgrade, previous)
    await connection.execute(text("INSERT INTO guild_settings (guild_id) VALUES (1)"))
    await connection.commit()

    await connection.run_sync(upgrade)
    result = await connection.execute(text("SELECT github_previews FROM guild_settings"))
    assert result.scalar_one() is True
