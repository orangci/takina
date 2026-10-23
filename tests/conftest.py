# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from collections.abc import AsyncIterator, Iterator
from sqlalchemy.pool import NullPool
from takina.libs import lyhelpers
from sqlmodel import SQLModel
from takina import database
from sqlalchemy import text
from pathlib import Path
from tests import fakes
import subprocess
import asyncio
import shutil
import pytest
import os


@pytest.fixture(autouse=True)
def no_application_emojis(monkeypatch: pytest.MonkeyPatch) -> None:
    # fetch_random_emoji would otherwise ask discord; with none it answers ""
    monkeypatch.setattr(lyhelpers, "_application_emojis", [])


@pytest.fixture(autouse=True)
def empty_cache() -> Iterator[None]:
    database._cache.clear()
    database._generations.clear()
    yield
    database._cache.clear()
    database._generations.clear()


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> fakes.FakeAPI:
    """Answers lyhelpers.request from canned responses, so no test touches the network."""
    fake = fakes.FakeAPI()
    monkeypatch.setattr(lyhelpers, "request", fake.request)
    return fake


def start_postgres(directory: Path) -> str:
    initdb = shutil.which("initdb")
    pg_ctl = shutil.which("pg_ctl")
    if initdb is None or pg_ctl is None:
        pytest.skip(
            "database tests need postgres: set TAKINA_TEST_POSTGRESQL_URI, or put initdb and pg_ctl on PATH"
        )

    data = directory / "data"
    subprocess.run(
        [initdb, "-D", str(data), "-U", "takina", "--auth=trust", "--no-sync"],
        check=True,
        capture_output=True,
    )
    # a socket in the temporary directory and no tcp, so it never clashes with a real server
    subprocess.run(
        [
            pg_ctl,
            "-D",
            str(data),
            "-l",
            str(directory / "log"),
            "-o",
            f"-k {directory} -c listen_addresses='' -c fsync=off",
            "-w",
            "start",
        ],
        check=True,
        capture_output=True,
    )
    return f"postgresql+asyncpg://takina@/postgres?host={directory}"


def stop_postgres(directory: Path) -> None:
    if pg_ctl := shutil.which("pg_ctl"):
        subprocess.run(
            [pg_ctl, "-D", str(directory / "data"), "-m", "immediate", "stop"],
            capture_output=True,
            check=False,
        )


async def migrate(uri: str) -> None:
    engine = create_async_engine(uri, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(database._upgrade)
    await engine.dispose()


@pytest.fixture(scope="session")
def postgres_uri(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """A migrated, empty database, shared by the whole session."""
    if uri := os.getenv("TAKINA_TEST_POSTGRESQL_URI"):
        uri = uri.replace("postgresql://", "postgresql+asyncpg://")
        asyncio.run(migrate(uri))
        yield uri
        return

    # unix sockets have a short path limit, so not the deeply nested pytest default
    directory = Path(tmp_path_factory.mktemp("pg", numbered=True))
    try:
        uri = start_postgres(directory)
        asyncio.run(migrate(uri))
        yield uri
    finally:
        stop_postgres(directory)


@pytest.fixture
async def db(postgres_uri: str, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[None]:
    """Points takina.database at the test database, and empties every table afterwards."""
    # an engine per test, as pooled connections belong to the event loop that opened them
    engine = create_async_engine(postgres_uri)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(
        database,
        "SessionLocal",
        async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False),
    )

    yield

    tables = ", ".join(f'"{table}"' for table in SQLModel.metadata.tables)
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY"))
    await engine.dispose()
