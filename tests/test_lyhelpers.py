# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from unittest.mock import AsyncMock, MagicMock
from takina.libs import lyerrors, lyhelpers
from aiohttp.test_utils import TestServer
from collections.abc import AsyncIterator
from typing import Any, ClassVar, Self
from types import SimpleNamespace
from geopy.exc import GeopyError
from discord.ext import commands
from datetime import timedelta
from takina import config
from aiohttp import web
from tests import fakes
import discord
import aiohttp
import pytest
import time


class TestDurationCalculator:
    @pytest.mark.parametrize(
        ("duration", "seconds"),
        [
            ("1s", 1),
            ("90m", 5400),
            ("1h30m", 5400),
            ("1h 30m", 5400),
            ("1H 30M", 5400),
            ("2d", 172_800),
            ("1w", 604_800),
            ("1y", 31_557_600),
            ("1y 2w 3d 4h 5m 6s", 31_557_600 + 2 * 604_800 + 3 * 86_400 + 4 * 3600 + 5 * 60 + 6),
            ("0s", 0),
            ("  5m  ", 300),
            # repeated units add up rather than being refused
            ("1h1h", 7200),
        ],
    )
    def test_parses(self, duration: str, seconds: int) -> None:
        assert lyhelpers.duration_calculator(duration) == seconds

    @pytest.mark.parametrize(
        "duration",
        [
            "",
            " ",
            "5",
            "m",
            "5x",
            "five minutes",
            "1h30",
            "1.5h",
            "-5m",
            "5m!",
            "h5",
            "1h-30m",
            "🍵",
        ],
    )
    def test_refuses(self, duration: str) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError, match="Invalid duration format"):
            lyhelpers.duration_calculator(duration)


class TestReverseDurationCalculator:
    @pytest.mark.parametrize(
        ("seconds", "duration"),
        [
            (0, "0s"),
            (1, "1s"),
            (59, "59s"),
            (60, "1m"),
            (5400, "1h 30m"),
            (86_400, "1d"),
            (90_061, "1d 1h 1m 1s"),
            (604_800, "1w"),
            (31_557_600, "1y"),
        ],
    )
    def test_formats(self, seconds: int, duration: str) -> None:
        assert lyhelpers.reverse_duration_calculator(seconds) == duration

    def test_refuses_negative(self) -> None:
        with pytest.raises(ValueError):
            lyhelpers.reverse_duration_calculator(-1)

    @pytest.mark.parametrize("seconds", [1, 61, 3599, 3601, 86_399, 1_000_000, 99_999_999])
    def test_round_trips(self, seconds: int) -> None:
        # what reminders print must be something the parser accepts back
        text = lyhelpers.reverse_duration_calculator(seconds)
        assert lyhelpers.duration_calculator(text) == seconds


@pytest.mark.parametrize(
    ("number", "suffix"),
    [
        (0, "th"),
        (1, "st"),
        (2, "nd"),
        (3, "rd"),
        (4, "th"),
        (11, "th"),
        (12, "th"),
        (13, "th"),
        (21, "st"),
        (22, "nd"),
        (23, "rd"),
        (31, "st"),
        (101, "st"),
        (111, "th"),
        (112, "th"),
        (113, "th"),
        (1001, "st"),
    ],
)
def test_get_ordinal(number: int, suffix: str) -> None:
    assert lyhelpers.get_ordinal(number) == suffix


class TestRandintFromSeed:
    def test_same_seed_same_answer(self) -> None:
        answers = {lyhelpers.randint_from_seed("will it rain in gensokyo") for _ in range(20)}
        assert len(answers) == 1

    def test_stays_in_range(self) -> None:
        for seed in range(500):
            assert 3 <= lyhelpers.randint_from_seed(seed, minimum=3, maximum=7) <= 7

    def test_picks_from_array(self) -> None:
        array = ["Reimu", "Marisa", "Sakuya"]
        picks = {lyhelpers.randint_from_seed(seed, array) for seed in range(200)}
        assert picks == set(array)

    def test_empty_array_falls_back_to_range(self) -> None:
        assert 1 <= lyhelpers.randint_from_seed("cirno", []) <= 10


class TestChunked:
    def test_even_split(self) -> None:
        assert list(lyhelpers.chunked([1, 2, 3, 4], 2)) == [[1, 2], [3, 4]]

    def test_remainder(self) -> None:
        assert list(lyhelpers.chunked([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]

    def test_empty(self) -> None:
        assert list(lyhelpers.chunked([], 3)) == []

    def test_size_larger_than_list(self) -> None:
        assert list(lyhelpers.chunked([1, 2], 10)) == [[1, 2]]


class TestTruncate:
    def test_short_text_untouched(self) -> None:
        assert lyhelpers.truncate("Marisa", 10) == "Marisa"

    def test_exact_limit_untouched(self) -> None:
        assert lyhelpers.truncate("a" * 10, 10) == "a" * 10

    def test_cut_to_limit_with_ellipsis(self) -> None:
        result = lyhelpers.truncate("a" * 11, 10)
        assert result == "a" * 9 + "…"
        assert len(result) == 10

    def test_trailing_space_dropped_before_ellipsis(self) -> None:
        assert lyhelpers.truncate("Love sign Master Spark", 11) == "Love sign…"

    @pytest.mark.parametrize("limit", [1, 2, 50, 256, 4096])
    def test_never_exceeds_limit(self, limit: int) -> None:
        assert len(lyhelpers.truncate("x" * 5000, limit)) <= limit


class TestStripHtml:
    def test_tags_removed(self) -> None:
        assert lyhelpers.strip_html("<b>Bold</b> and <i>italic</i>") == "Bold and italic"

    def test_breaks_and_paragraphs_become_newlines(self) -> None:
        assert lyhelpers.strip_html("<p>One</p><p>Two</p>") == "One\nTwo"
        assert lyhelpers.strip_html("a<br>b<BR/>c<br />d") == "a\nb\nc\nd"

    def test_entities_unescaped(self) -> None:
        assert lyhelpers.strip_html("Tom &amp; Jerry &lt;3") == "Tom & Jerry <3"

    def test_escaped_tags_survive_as_text(self) -> None:
        # unescaping comes after stripping, so &lt;b&gt; is shown rather than eaten
        assert lyhelpers.strip_html("&lt;b&gt;") == "<b>"

    def test_whitespace_trimmed(self) -> None:
        assert lyhelpers.strip_html("  <p>text</p>  ") == "text"


class TestPermissionsCheck:
    @pytest.fixture
    def setup(self) -> SimpleNamespace:
        guild = fakes.make_guild()
        low = fakes.make_role(guild, position=1, name="Fairy")
        mid = fakes.make_role(guild, position=5, name="Moderator")
        high = fakes.make_role(guild, position=10, name="Admin")
        bot_role = fakes.make_role(guild, position=8, name="Takina")

        guild.me = fakes.make_member(guild, name="takina", top_role=bot_role, bot=True)
        owner = fakes.make_member(guild, name="yukari", top_role=low)
        guild.owner = owner
        moderator = fakes.make_member(guild, name="reimu", top_role=mid)
        fairy = fakes.make_member(guild, name="cirno", top_role=low)
        admin = fakes.make_member(guild, name="kanako", top_role=high)
        return SimpleNamespace(
            guild=guild, owner=owner, moderator=moderator, fairy=fairy, admin=admin, mid=mid
        )

    async def test_allows_lower_member(self, setup: SimpleNamespace) -> None:
        ctx = fakes.make_ctx(guild=setup.guild, author=setup.moderator)
        await lyhelpers.permissions_check(ctx, setup.fairy, True, True, True)

    async def test_refuses_self(self, setup: SimpleNamespace) -> None:
        ctx = fakes.make_ctx(guild=setup.guild, author=setup.moderator)
        with pytest.raises(lyerrors.TakinaPermissionError, match="yourself"):
            await lyhelpers.permissions_check(ctx, setup.moderator)

    async def test_self_allowed_without_author_check(self, setup: SimpleNamespace) -> None:
        ctx = fakes.make_ctx(guild=setup.guild, author=setup.moderator)
        await lyhelpers.permissions_check(
            ctx, setup.moderator, author_check=False, role_check=False
        )

    async def test_refuses_owner(self, setup: SimpleNamespace) -> None:
        ctx = fakes.make_ctx(guild=setup.guild, author=setup.moderator)
        with pytest.raises(lyerrors.TakinaPermissionError, match="server owner"):
            await lyhelpers.permissions_check(ctx, setup.owner, owner_check=True)

    async def test_owner_allowed_without_owner_check(self, setup: SimpleNamespace) -> None:
        ctx = fakes.make_ctx(guild=setup.guild, author=setup.moderator)
        await lyhelpers.permissions_check(ctx, setup.owner, owner_check=False)

    async def test_refuses_equal_role(self, setup: SimpleNamespace) -> None:
        peer = fakes.make_member(setup.guild, name="sanae", top_role=setup.mid)
        ctx = fakes.make_ctx(guild=setup.guild, author=setup.moderator)
        with pytest.raises(
            lyerrors.TakinaPermissionError, match="higher than or equal to your own"
        ):
            await lyhelpers.permissions_check(ctx, peer)

    async def test_refuses_higher_role(self, setup: SimpleNamespace) -> None:
        ctx = fakes.make_ctx(guild=setup.guild, author=setup.moderator)
        with pytest.raises(lyerrors.TakinaPermissionError):
            await lyhelpers.permissions_check(ctx, setup.admin)

    async def test_owner_outranks_everyone(self, setup: SimpleNamespace) -> None:
        # the owner's top role is the lowest, yet they may act on the moderator
        ctx = fakes.make_ctx(guild=setup.guild, author=setup.owner)
        await lyhelpers.permissions_check(ctx, setup.moderator)

    async def test_refuses_member_above_bot(self, setup: SimpleNamespace) -> None:
        # the owner passes the author check, so only the bot's own rank is left to fail
        ctx = fakes.make_ctx(guild=setup.guild, author=setup.owner)
        with pytest.raises(lyerrors.TakinaBotPermissionError, match="my own"):
            await lyhelpers.permissions_check(ctx, setup.admin)

    async def test_role_check_off_skips_both(self, setup: SimpleNamespace) -> None:
        ctx = fakes.make_ctx(guild=setup.guild, author=setup.moderator)
        await lyhelpers.permissions_check(ctx, setup.admin, role_check=False)

    async def test_refuses_outside_guild(self) -> None:
        ctx = fakes.make_ctx()
        with pytest.raises(lyerrors.TakinaError, match="only be used in a server"):
            await lyhelpers.permissions_check(ctx, MagicMock(spec=discord.Member))


class TestInvokeMoved:
    async def test_invokes_new_home(self) -> None:
        ctx = fakes.make_ctx(guild=fakes.make_guild())
        command = MagicMock(spec=commands.Command)
        ctx.bot.get_command.return_value = command

        await lyhelpers.invoke_moved(ctx, "settings guild honeypot", channel="channel")

        ctx.bot.get_command.assert_called_once_with("settings guild honeypot")
        ctx.invoke.assert_awaited_once_with(command, channel="channel")

    async def test_missing_command_is_disabled(self) -> None:
        ctx = fakes.make_ctx(guild=fakes.make_guild())
        with pytest.raises(lyerrors.TakinaDisabledError, match="settings guild honeypot"):
            await lyhelpers.invoke_moved(ctx, "settings guild honeypot")
        ctx.invoke.assert_not_awaited()


class TestBotAccess:
    def test_get_bot_before_setup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(lyhelpers, "_bot", None)
        with pytest.raises(RuntimeError, match="setup"):
            lyhelpers.get_bot()

    def test_setup_sets_bot(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(lyhelpers, "_bot", None)
        bot = fakes.make_bot()
        lyhelpers.setup(bot)
        assert lyhelpers.get_bot() is bot

    def test_uptime(self, monkeypatch: pytest.MonkeyPatch) -> None:
        bot = fakes.make_bot()
        bot.start_time = discord.utils.utcnow() - timedelta(days=2, hours=3, minutes=4, seconds=5)
        monkeypatch.setattr(lyhelpers, "_bot", bot)
        # a second may tick between the two clocks
        assert lyhelpers.uptime_fetcher() in ("2d 3h 4m 5s", "2d 3h 4m 6s")

    async def test_member_count_prefers_approximate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        bot = fakes.make_bot()
        bot.fetch_guild.return_value = SimpleNamespace(approximate_member_count=1234)
        monkeypatch.setattr(lyhelpers, "_bot", bot)
        guild = fakes.make_guild()
        guild.member_count = 10

        assert await lyhelpers.fetch_member_count(guild) == 1234
        bot.fetch_guild.assert_awaited_once_with(guild.id, with_counts=True)

    async def test_member_count_falls_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        bot = fakes.make_bot()
        bot.fetch_guild.return_value = SimpleNamespace(approximate_member_count=None)
        monkeypatch.setattr(lyhelpers, "_bot", bot)
        guild = fakes.make_guild()
        guild.member_count = None

        assert await lyhelpers.fetch_member_count(guild) == 0


class TestFetchRandomEmoji:
    async def test_none_gives_empty(self) -> None:
        assert await lyhelpers.fetch_random_emoji() == ""

    async def test_fetched_once(self, monkeypatch: pytest.MonkeyPatch) -> None:
        bot = fakes.make_bot()
        bot.fetch_application_emojis.return_value = ["<:yukkuri:1>"]
        monkeypatch.setattr(lyhelpers, "_bot", bot)
        monkeypatch.setattr(lyhelpers, "_application_emojis", None)

        assert await lyhelpers.fetch_random_emoji() == "<:yukkuri:1> "
        assert await lyhelpers.fetch_random_emoji() == "<:yukkuri:1> "
        bot.fetch_application_emojis.assert_awaited_once()


class RecordingServer(TestServer):
    """A local server that remembers the last request to /json."""

    seen: dict[str, Any]


@pytest.fixture
async def server(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[RecordingServer]:
    """A real http server on localhost, so request() is tested against aiohttp itself."""
    seen: dict[str, Any] = {}

    async def json_ok(request: web.Request) -> web.Response:
        seen["headers"] = dict(request.headers)
        seen["method"] = request.method
        seen["query"] = dict(request.query)
        return web.json_response({"name": "Reimu"}, headers={"X-Total-Count": "42"})

    async def text_ok(request: web.Request) -> web.Response:
        return web.Response(text="just text")

    async def missing(request: web.Request) -> web.Response:
        return web.Response(status=404)

    async def broken(request: web.Request) -> web.Response:
        return web.Response(status=503, reason="Service Unavailable")

    app = web.Application()
    app.router.add_route("*", "/json", json_ok)
    app.router.add_get("/text", text_ok)
    app.router.add_get("/missing", missing)
    app.router.add_get("/broken", broken)

    test_server = RecordingServer(app)
    await test_server.start_server()

    bot = fakes.make_bot()
    bot.http_session = aiohttp.ClientSession()
    monkeypatch.setattr(lyhelpers, "_bot", bot)
    test_server.seen = seen

    yield test_server

    await bot.http_session.close()
    await test_server.close()


class TestRequest:
    async def test_json(self, server: RecordingServer) -> None:
        assert await lyhelpers.request(str(server.make_url("/json"))) == {"name": "Reimu"}

    async def test_sends_user_agent(self, server: RecordingServer) -> None:
        await lyhelpers.request(str(server.make_url("/json")))
        assert server.seen["headers"]["User-Agent"] == config.USER_AGENT

    async def test_merges_headers(self, server: RecordingServer) -> None:
        await lyhelpers.request(str(server.make_url("/json")), headers={"Accept": "marisa/json"})
        headers = server.seen["headers"]
        assert headers["Accept"] == "marisa/json"
        assert headers["User-Agent"] == config.USER_AGENT

    async def test_method_and_params(self, server: RecordingServer) -> None:
        await lyhelpers.request(
            str(server.make_url("/json")), method="POST", params={"q": "sakuya"}
        )
        assert server.seen["method"] == "POST"
        assert server.seen["query"] == {"q": "sakuya"}

    async def test_text(self, server: RecordingServer) -> None:
        assert await lyhelpers.request(str(server.make_url("/text")), disable_json=True) == (
            "just text"
        )

    async def test_with_headers(self, server: RecordingServer) -> None:
        body, headers = await lyhelpers.request(str(server.make_url("/json")), with_headers=True)
        assert body == {"name": "Reimu"}
        assert headers["X-Total-Count"] == "42"

    async def test_not_json_is_an_error(self, server: RecordingServer) -> None:
        with pytest.raises(lyerrors.TakinaError, match="other than JSON"):
            await lyhelpers.request(str(server.make_url("/text")))

    async def test_404_is_not_found(self, server: RecordingServer) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError, match="That could not be found."):
            await lyhelpers.request(str(server.make_url("/missing")))

    async def test_404_custom_message(self, server: RecordingServer) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError, match="No such youkai."):
            await lyhelpers.request(str(server.make_url("/missing")), not_found="No such youkai.")

    async def test_other_errors_name_the_status(self, server: RecordingServer) -> None:
        with pytest.raises(lyerrors.TakinaError, match=r"Error \[503\].*Service Unavailable"):
            await lyhelpers.request(str(server.make_url("/broken")))

    async def test_without_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        bot = fakes.make_bot()
        bot.http_session = None
        monkeypatch.setattr(lyhelpers, "_bot", bot)
        with pytest.raises(RuntimeError, match="HTTP session"):
            await lyhelpers.request("http://localhost/json")

    async def test_default_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        bot = fakes.make_bot()
        bot.http_session = MagicMock()
        monkeypatch.setattr(lyhelpers, "_bot", bot)
        bot.http_session.request.side_effect = RuntimeError("stop here")

        with pytest.raises(RuntimeError):
            await lyhelpers.request("http://localhost/json")

        timeout = bot.http_session.request.call_args.kwargs["timeout"]
        assert timeout.total == 10


class FakeNominatim:
    calls: ClassVar[list[str]] = []
    result: Any = None
    error: Exception | None = None

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def geocode(self, query: str, language: str) -> Any:
        FakeNominatim.calls.append(query)
        if FakeNominatim.error is not None:
            raise FakeNominatim.error
        return FakeNominatim.result


class TestGeocode:
    @pytest.fixture(autouse=True)
    def nominatim(self, monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
        FakeNominatim.calls = []
        FakeNominatim.result = SimpleNamespace(latitude=35.0, longitude=139.0, address="Gensokyo")
        FakeNominatim.error = None
        monkeypatch.setattr(lyhelpers, "Nominatim", FakeNominatim)
        sleep = AsyncMock()
        monkeypatch.setattr(lyhelpers, "asyncio", SimpleNamespace(sleep=sleep))
        monkeypatch.setattr(lyhelpers, "_last_geocode", 0.0)
        return sleep

    async def test_returns_location(self) -> None:
        location = await lyhelpers.geocode("Hakurei Shrine")
        assert location is not None
        assert location.address == "Gensokyo"
        assert FakeNominatim.calls == ["Hakurei Shrine"]

    async def test_waits_between_requests(self, nominatim: AsyncMock) -> None:
        await lyhelpers.geocode("Human Village")
        nominatim.assert_not_awaited()

        await lyhelpers.geocode("Misty Lake")
        # nominatim allows one request a second, so the second call sleeps for most of one
        nominatim.assert_awaited_once()
        assert 0 < nominatim.await_args_list[-1].args[0] <= 1

    async def test_no_wait_after_a_second(self, nominatim: AsyncMock) -> None:
        lyhelpers._last_geocode = time.monotonic() - 2
        await lyhelpers.geocode("Youkai Mountain")
        nominatim.assert_not_awaited()

    async def test_service_error(self) -> None:
        FakeNominatim.error = GeopyError("down")
        with pytest.raises(lyerrors.TakinaError, match="could not be reached"):
            await lyhelpers.geocode("Former Hell")

    async def test_error_still_counts_for_rate_limit(self) -> None:
        FakeNominatim.error = GeopyError("down")
        with pytest.raises(lyerrors.TakinaError):
            await lyhelpers.geocode("Former Hell")
        assert lyhelpers._last_geocode > 0
