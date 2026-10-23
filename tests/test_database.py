# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from sqlalchemy.exc import IntegrityError, MultipleResultsFound
from datetime import datetime, timedelta, UTC
from takina import database, models
from sqlalchemy import text
from sqlmodel import col
from typing import Any
import asyncio
import pytest

pytestmark = pytest.mark.usefixtures("db")


def giveaway(**overrides: Any) -> models.GiveawayModel:
    fields: dict = {
        "guild_id": 1,
        "id": 1,
        "channel_id": 2,
        "message_id": 3,
        "title": "Touhou Fumo",
        "description": "",
        "ends_at": datetime.now(UTC) + timedelta(hours=1),
    }
    return models.GiveawayModel(**(fields | overrides))


def case(case_id: int, **overrides: Any) -> models.ModLogCaseModel:
    fields: dict = {
        "guild_id": 1,
        "case_id": case_id,
        "action": "warn",
        "member_ids": [10],
        "member_names": ["cirno"],
        "moderator_id": 20,
        "reason": "Freezing frogs",
        "timestamp": datetime.now(UTC),
    }
    return models.ModLogCaseModel(**(fields | overrides))


async def raw(statement: str, **params: object) -> None:
    # straight to postgres, as an admin in psql would, so the cache never hears of it
    async with database.engine.begin() as connection:
        await connection.execute(text(statement), params)


class TestGet:
    async def test_missing(self) -> None:
        assert await database.get(models.PrefixModel, guild_id=1) is None

    async def test_round_trip(self) -> None:
        await database.save(models.PrefixModel(guild_id=1, prefix="!"))
        prefix = await database.get(models.PrefixModel, guild_id=1)
        assert prefix is not None and prefix.prefix == "!"

    async def test_several_matches_raise(self) -> None:
        await database.save(
            models.ReminderModel(user_id=1, reminder="a", remind_at=datetime.now(UTC))
        )
        await database.save(
            models.ReminderModel(user_id=1, reminder="b", remind_at=datetime.now(UTC))
        )
        with pytest.raises(MultipleResultsFound):
            await database.get(models.ReminderModel, user_id=1)

    async def test_composite_key(self) -> None:
        await database.save(giveaway(guild_id=1, id=1, title="One"))
        await database.save(giveaway(guild_id=2, id=1, title="Two"))
        found = await database.get(models.GiveawayModel, guild_id=2, id=1)
        assert found is not None and found.title == "Two"

    async def test_arrays_and_json_survive(self) -> None:
        await database.save(
            models.TriggerResponsesModel(
                guild_id=1, triggers={"r1999": {"trigger": "vertin", "response": "Timekeeper!"}}
            )
        )
        await database.save(giveaway(participants=[2**62, 5]))

        triggers = await database.get(models.TriggerResponsesModel, guild_id=1)
        assert triggers is not None
        assert triggers.triggers == {"r1999": {"trigger": "vertin", "response": "Timekeeper!"}}

        found = await database.get(models.GiveawayModel, guild_id=1, id=1)
        # snowflakes need BIGINT, which a plain integer column would overflow
        assert found is not None and found.participants == [2**62, 5]


class TestGetAll:
    async def test_filters(self) -> None:
        for number in range(3):
            await database.save(case(number, guild_id=1))
        await database.save(case(0, guild_id=2))

        assert len(await database.get_all(models.ModLogCaseModel, guild_id=1)) == 3
        assert await database.get_all(models.ModLogCaseModel, guild_id=3) == []

    async def test_where_order_and_limit(self) -> None:
        for number in range(5):
            await database.save(case(number))

        cases = await database.get_all(
            models.ModLogCaseModel,
            where=[col(models.ModLogCaseModel.case_id) >= 1],
            order_by=col(models.ModLogCaseModel.case_id).desc(),
            limit=2,
        )
        assert [found.case_id for found in cases] == [4, 3]

    async def test_array_contains(self) -> None:
        await database.save(case(0, member_ids=[10, 11]))
        await database.save(case(1, member_ids=[12]))
        cases = await database.get_all(
            models.ModLogCaseModel, where=[col(models.ModLogCaseModel.member_ids).contains([11])]
        )
        assert [found.case_id for found in cases] == [0]


class TestGetOrCreate:
    async def test_new_is_unsaved(self) -> None:
        created = await database.get_or_create(
            models.StarboardSettingsModel, defaults={"minimum_reaction_count": 7}, guild_id=1
        )
        assert created.guild_id == 1
        assert created.minimum_reaction_count == 7
        assert await database.get(models.StarboardSettingsModel, guild_id=1) is None

    async def test_existing_is_returned(self) -> None:
        await database.save(models.StarboardSettingsModel(guild_id=1, minimum_reaction_count=2))
        found = await database.get_or_create(
            models.StarboardSettingsModel, defaults={"minimum_reaction_count": 7}, guild_id=1
        )
        assert found.minimum_reaction_count == 2


class TestSave:
    async def test_updates_by_primary_key(self) -> None:
        await database.save(models.PrefixModel(guild_id=1, prefix="!"))
        await database.save(models.PrefixModel(guild_id=1, prefix="?"))

        rows = await database.get_all(models.PrefixModel)
        assert [(row.guild_id, row.prefix) for row in rows] == [(1, "?")]

    async def test_autoincrement_id_flows_back(self) -> None:
        saved = await database.save(case(0))
        assert saved.id is not None

        again = await database.save(case(1))
        assert again.id == saved.id + 1

    async def test_save_returns_fresh_row(self) -> None:
        # server defaults come back, so callers see what postgres stored
        saved = await database.save(models.GuildSettingsModel(guild_id=1))
        assert saved.github_previews is True

    async def test_mutated_array_is_saved(self) -> None:
        settings = await database.save(models.StarboardSettingsModel(guild_id=1))
        settings.whitelisted_channel_ids.append(5)
        await database.save(settings)

        found = await database.get(models.StarboardSettingsModel, guild_id=1)
        assert found is not None and found.whitelisted_channel_ids == [5]


class TestInsert:
    async def test_inserts(self) -> None:
        await database.insert(giveaway())
        assert await database.get(models.GiveawayModel, guild_id=1, id=1) is not None

    async def test_refuses_to_overwrite(self) -> None:
        await database.insert(giveaway(title="First"))
        with pytest.raises(IntegrityError):
            await database.insert(giveaway(title="Second"))

        found = await database.get(models.GiveawayModel, guild_id=1, id=1)
        assert found is not None and found.title == "First"

    async def test_unique_case_ids(self) -> None:
        await database.insert(case(0))
        with pytest.raises(IntegrityError):
            await database.insert(case(0))


class TestToggleInArray:
    async def test_adds_then_removes(self) -> None:
        await database.save(giveaway())

        added = await database.toggle_in_array(
            models.GiveawayModel, "participants", 42, guild_id=1, id=1
        )
        assert added is not None and added.participants == [42]

        removed = await database.toggle_in_array(
            models.GiveawayModel, "participants", 42, guild_id=1, id=1
        )
        assert removed is not None and removed.participants == []

    async def test_no_match(self) -> None:
        await database.save(giveaway(ended=True))
        assert (
            await database.toggle_in_array(
                models.GiveawayModel, "participants", 42, guild_id=1, id=1, ended=False
            )
            is None
        )

        found = await database.get(models.GiveawayModel, guild_id=1, id=1)
        assert found is not None and found.participants == []

    async def test_concurrent_toggles_all_land(self) -> None:
        # read-modify-write would lose entries here; one update statement each cannot
        await database.save(giveaway())
        await asyncio.gather(
            *(
                database.toggle_in_array(
                    models.GiveawayModel, "participants", user_id, guild_id=1, id=1
                )
                for user_id in range(30)
            )
        )

        found = await database.get(models.GiveawayModel, guild_id=1, id=1)
        assert found is not None and sorted(found.participants) == list(range(30))

    async def test_invalidates_cached_rows(self) -> None:
        await database.save(models.StarboardSettingsModel(guild_id=1))
        await database.get(models.StarboardSettingsModel, guild_id=1)

        await database.toggle_in_array(
            models.StarboardSettingsModel, "whitelisted_channel_ids", 9, guild_id=1
        )

        found = await database.get(models.StarboardSettingsModel, guild_id=1)
        assert found is not None and found.whitelisted_channel_ids == [9]


class TestDelete:
    async def test_deletes(self) -> None:
        prefix = await database.save(models.PrefixModel(guild_id=1, prefix="!"))
        await database.delete(prefix)
        assert await database.get(models.PrefixModel, guild_id=1) is None

    async def test_idempotent(self) -> None:
        # two afk handlers racing to clear one status both delete it
        status = await database.save(models.AFKStatusModel(user_id=1, status="napping"))
        await database.delete(status)
        await database.delete(status)

    async def test_concurrent(self) -> None:
        status = await database.save(models.AFKStatusModel(user_id=1, status="napping"))
        await asyncio.gather(database.delete(status), database.delete(status))
        assert await database.get(models.AFKStatusModel, user_id=1) is None

    async def test_only_that_row(self) -> None:
        await database.save(giveaway(guild_id=1, id=1))
        await database.save(giveaway(guild_id=1, id=2))
        await database.save(giveaway(guild_id=2, id=1))

        await database.delete(giveaway(guild_id=1, id=1))

        remaining = await database.get_all(models.GiveawayModel)
        assert sorted((row.guild_id, row.id) for row in remaining) == [(1, 2), (2, 1)]


class TestCache:
    async def test_hit_skips_postgres(self) -> None:
        await database.save(models.PrefixModel(guild_id=1, prefix="!"))
        await database.get(models.PrefixModel, guild_id=1)

        await raw("UPDATE prefixes SET prefix = '?' WHERE guild_id = 1")

        cached = await database.get(models.PrefixModel, guild_id=1)
        assert cached is not None and cached.prefix == "!"

    async def test_miss_is_cached_and_save_clears_it(self) -> None:
        assert await database.get(models.GuildSettingsModel, guild_id=1) is None
        await raw("INSERT INTO guild_settings (guild_id) VALUES (1)")
        assert await database.get(models.GuildSettingsModel, guild_id=1) is None

        await database.save(models.GuildSettingsModel(guild_id=1, modlog_channel_id=5))
        found = await database.get(models.GuildSettingsModel, guild_id=1)
        assert found is not None and found.modlog_channel_id == 5

    async def test_delete_clears(self) -> None:
        status = await database.save(models.AFKStatusModel(user_id=1, status="napping"))
        assert await database.get(models.AFKStatusModel, user_id=1) is not None

        await database.delete(status)
        assert await database.get(models.AFKStatusModel, user_id=1) is None

    async def test_hands_out_copies(self) -> None:
        await database.save(models.StarboardSettingsModel(guild_id=1, whitelisted_channel_ids=[1]))

        first = await database.get(models.StarboardSettingsModel, guild_id=1)
        assert first is not None
        first.whitelisted_channel_ids.append(2)
        first.minimum_reaction_count = 99

        second = await database.get(models.StarboardSettingsModel, guild_id=1)
        assert second is not None
        assert second.whitelisted_channel_ids == [1]
        assert second.minimum_reaction_count == 4

    async def test_expires(self, monkeypatch: pytest.MonkeyPatch) -> None:
        await database.save(models.PrefixModel(guild_id=1, prefix="!"))
        await database.get(models.PrefixModel, guild_id=1)
        await raw("UPDATE prefixes SET prefix = '?' WHERE guild_id = 1")

        now = database.time.monotonic()
        monkeypatch.setattr(database.time, "monotonic", lambda: now + database.CACHE_SECONDS + 1)

        found = await database.get(models.PrefixModel, guild_id=1)
        assert found is not None and found.prefix == "?"

    async def test_only_by_primary_key(self) -> None:
        await database.save(models.PrefixModel(guild_id=1, prefix="!"))
        await database.get(models.PrefixModel, guild_id=1, prefix="!")
        assert database._cache == {}

    async def test_only_hot_tables(self) -> None:
        await database.save(giveaway())
        await database.get(models.GiveawayModel, guild_id=1, id=1)
        assert database._cache == {}

    async def test_racing_write_is_not_cached(self) -> None:
        # a read that started before a write must not store what it saw
        key = database._cache_key(models.PrefixModel, {"guild_id": 1})
        assert key is not None
        generation = database._generations.get(key, 0)

        await database.save(models.PrefixModel(guild_id=1, prefix="!"))
        database._remember(key, generation, models.PrefixModel(guild_id=1, prefix="stale"))

        assert key not in database._cache

    async def test_size_is_bounded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(database, "MAX_CACHE_ENTRIES", 3)
        for guild_id in range(10):
            await database.get(models.PrefixModel, guild_id=guild_id)
            assert len(database._cache) <= 3

    async def test_full_cache_drops_stale_first(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(database, "MAX_CACHE_ENTRIES", 2)
        now = database.time.monotonic()

        monkeypatch.setattr(database.time, "monotonic", lambda: now - database.CACHE_SECONDS - 1)
        await database.get(models.PrefixModel, guild_id=1)
        monkeypatch.setattr(database.time, "monotonic", lambda: now)
        await database.get(models.PrefixModel, guild_id=2)
        await database.get(models.PrefixModel, guild_id=3)

        assert set(database._cache) == {("prefixes", (2,)), ("prefixes", (3,))}


async def test_initiate_database_is_idempotent() -> None:
    # every startup runs it against a database that is already at head
    await database.initiate_database()
    await database.initiate_database()
