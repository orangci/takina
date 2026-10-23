# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from collections.abc import Callable, Iterator
from types import ModuleType
from takina import config
import importlib
import tomllib
import dotenv
import pytest
import os


@pytest.fixture
def load(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[..., ModuleType]]:
    """Reload config under other environment variables, restoring the real ones afterwards."""
    saved = dict(os.environ)
    # a local .env would otherwise fill in whatever a test unsets
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: False)

    def reload(**env: str | None) -> ModuleType:
        for key, value in env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        return importlib.reload(config)

    yield reload

    os.environ.clear()
    os.environ.update(saved)
    importlib.reload(config)


@pytest.mark.parametrize(
    ("value", "colour"),
    [
        ("#2B2D31", 0x2B2D31),
        ("#ff0037", 0xFF0037),
        ("0xFF0037", 0xFF0037),
        ("16711735", 16711735),
        ('"#2B2D31"', 0x2B2D31),
        ("'#2B2D31'", 0x2B2D31),
        ("  #2B2D31  ", 0x2B2D31),
    ],
)
def test_embed_colour(load: Callable[..., ModuleType], value: str, colour: int) -> None:
    assert load(EMBED_COLOUR=value).EMBED_COLOUR == colour


def test_embed_colour_default(load: Callable[..., ModuleType]) -> None:
    assert load(EMBED_COLOUR=None).EMBED_COLOUR == 0x2B2D31


def test_postgres_uri_gets_the_async_driver(load: Callable[..., ModuleType]) -> None:
    loaded = load(POSTGRESQL_URI="postgresql://takina@localhost/takina")
    assert loaded.POSTGRESQL_URI == "postgresql+asyncpg://takina@localhost/takina"


def test_libretranslate_trailing_slash(load: Callable[..., ModuleType]) -> None:
    loaded = load(LIBRETRANSLATE_API_URL="https://translate.example/")
    assert loaded.LIBRETRANSLATE_API_URL == "https://translate.example"


def test_version_from_pyproject(load: Callable[..., ModuleType]) -> None:
    with open(config.Path(__file__).parent.parent / "pyproject.toml", "rb") as file:
        version = tomllib.load(file)["project"]["version"]

    loaded = load(BOT_VERSION=None)
    assert loaded.BOT_VERSION == version
    assert version in loaded.USER_AGENT


def test_version_from_environment(load: Callable[..., ModuleType]) -> None:
    loaded = load(BOT_VERSION="9.8.7")
    assert loaded.BOT_VERSION == "9.8.7"
    assert loaded.CHANGELOG_URL.endswith("CHANGELOG.md#9-8-7")
    assert loaded.USER_AGENT.startswith("Takina/9.8.7 ")


def test_bot_name_in_user_agent(load: Callable[..., ModuleType]) -> None:
    assert load(BOT_NAME="Chisato").USER_AGENT.startswith("Chisato/")


@pytest.mark.parametrize(("value", "expected"), [(None, 5), ("", 5), ("12", 12)])
def test_commands_cooldown(
    load: Callable[..., ModuleType], value: str | None, expected: int
) -> None:
    assert load(COMMANDS_COOLDOWN=value).COMMANDS_COOLDOWN == expected


class TestEmojis:
    def test_defaults(self, load: Callable[..., ModuleType]) -> None:
        loaded = load(EMOJIS_SUCCESS=None, EMOJIS_ERROR=None, EMOJIS_NOTE=None)
        assert loaded.emojis.SUCCESS == "✅"
        assert loaded.emojis.ERROR == "❌"
        assert loaded.emojis.NOTE == "📝"

    def test_list_picks_one(self, load: Callable[..., ModuleType]) -> None:
        loaded = load(EMOJIS_SUCCESS="<:reimu:1>, <:marisa:2>,,")
        picks = {loaded.emojis.SUCCESS for _ in range(100)}
        assert picks == {"<:reimu:1>", "<:marisa:2>"}

    def test_case_insensitive_names(self) -> None:
        assert config.emojis.success == config.emojis.SUCCESS

    def test_unknown_name(self) -> None:
        with pytest.raises(AttributeError):
            _ = config.emojis.SPELLCARD

    def test_empty_value_is_an_error(self, load: Callable[..., ModuleType]) -> None:
        loaded = load(EMOJIS_NOTE=" , ")
        with pytest.raises(AttributeError):
            _ = loaded.emojis.NOTE
