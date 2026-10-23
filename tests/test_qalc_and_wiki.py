# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.util.wiki import DISAMBIGUATION_CATEGORY, MAX_RANDOM_ATTEMPTS, WIKIPEDIA_ICON
from takina.cogs.util.qalc import BLOCKED_FUNCTIONS, QALC_ENVIRONMENT, Qalc, blocked_function
from takina.cogs.util.wiki import Wikipedia, paginate
from collections.abc import AsyncIterator, Awaitable
from takina.cogs.util import qalc as qalc_module
from unittest.mock import AsyncMock, MagicMock
from takina.libs import lyerrors, lyviews
from typing import Any, cast
from takina import config
from pathlib import Path
from tests import fakes
import asyncio
import pytest
import shutil

needs_qalc = pytest.mark.skipif(qalc_module.QALC_PACKAGE is None, reason="qalc is not installed")


class TestBlockedFunction:
    @pytest.mark.parametrize("name", BLOCKED_FUNCTIONS)
    def test_plain(self, name: str) -> None:
        assert blocked_function(f'{name}("x")') == name

    @pytest.mark.parametrize(
        ("expression", "name"),
        [
            ('COMMAND("id")', "command"),
            ('CoMmAnD("id")', "command"),
            # qalc reads through spaces, underscores and the like inside a name
            ('com mand("id")', "command"),
            ('com_mand("id")', "command"),
            ('c-o-m-m-a-n-d("id")', "command"),
            # fullwidth letters fold to ascii under nfkc
            ('ｃｏｍｍａｎｄ("id")', "command"),
            ('1 + load("/etc/passwd")', "load"),
            ('export(1, "/tmp/x")', "export"),
            ('function("command(\\"id\\")")', "command"),
            ("concatenate(99, 111)", "concatenate"),
            ("char(99)", "char"),
        ],
    )
    def test_evasions(self, expression: str, name: str) -> None:
        assert blocked_function(expression) == name

    @pytest.mark.parametrize(
        "expression",
        ["6 * 7", "sqrt(2)", "10 km to mi", "2^1000", "sin(pi / 2)", "100 USD to EUR", "5!"],
    )
    def test_harmless(self, expression: str) -> None:
        assert blocked_function(expression) is None

    def test_conservative(self) -> None:
        # a name hidden in a longer word is refused as well, since qalc would find it there too
        assert blocked_function("elementary charge") == "char"


class TestQalcCommand:
    async def test_blocked_before_running(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cog = fakes.make_cog(Qalc)
        qalc_expression = AsyncMock()
        monkeypatch.setattr(cog, "qalc_expression", qalc_expression)
        ctx = fakes.make_ctx()

        with pytest.raises(lyerrors.TakinaUserInputError, match="`command`"):
            await fakes.call(cog.qalc, ctx, calculation='command("id")')
        qalc_expression.assert_not_awaited()
        ctx.defer.assert_not_awaited()

    async def test_result(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cog = fakes.make_cog(Qalc)
        qalc_expression = AsyncMock(return_value="42")
        monkeypatch.setattr(cog, "qalc_expression", qalc_expression)
        ctx = fakes.make_ctx()
        await fakes.call(cog.qalc, ctx, calculation="6 * 7")

        ctx.defer.assert_awaited_once()
        assert fakes.sent_embed(ctx.reply).description == " 42"

    @pytest.mark.parametrize("result", [None, ""])
    async def test_invalid(self, monkeypatch: pytest.MonkeyPatch, result: str | None) -> None:
        cog = fakes.make_cog(Qalc)
        qalc_expression = AsyncMock(return_value=result)
        monkeypatch.setattr(cog, "qalc_expression", qalc_expression)
        with pytest.raises(lyerrors.TakinaUserInputError, match="Invalid expression"):
            await fakes.call(cog.qalc, fakes.make_ctx(), calculation="sqrt(")

    async def test_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(config, "QALC_TIMEOUT", 0.05)
        cog = fakes.make_cog(Qalc)

        async def forever(expression: str) -> str:
            await asyncio.sleep(10)
            return "never"

        qalc_expression = forever
        monkeypatch.setattr(cog, "qalc_expression", qalc_expression)
        with pytest.raises(lyerrors.TakinaError, match="timed out"):
            await fakes.call(cog.qalc, fakes.make_ctx(), calculation="ackermann(4, 4)")

    async def test_long_result(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cog = fakes.make_cog(Qalc)
        qalc_expression = AsyncMock(return_value="9" * 10_000)
        monkeypatch.setattr(cog, "qalc_expression", qalc_expression)
        ctx = fakes.make_ctx()
        await fakes.call(cog.qalc, ctx, calculation="10^10000 - 1")
        assert (fakes.sent_embed(ctx.reply).description or "").endswith("…")

    async def test_setup_needs_qalc(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(qalc_module, "QALC_PACKAGE", None)
        bot = fakes.make_bot()
        with pytest.raises(lyerrors.TakinaMissingEnvironmentVariableError):
            await qalc_module.setup(bot)
        bot.add_cog.assert_not_awaited()


class TestQalcProcess:
    def test_environment(self) -> None:
        # no PATH for command to search, and none of the bot's secrets
        assert QALC_ENVIRONMENT["PATH"] == ""
        assert QALC_ENVIRONMENT["LC_ALL"] == "C"
        assert set(QALC_ENVIRONMENT) == {"LC_ALL", "PATH", "HOME"}
        assert "TOKEN" not in QALC_ENVIRONMENT

    async def test_arguments(self, monkeypatch: pytest.MonkeyPatch) -> None:
        seen: dict[str, Any] = {}

        async def spawn(*args: Any, **kwargs: Any) -> Any:
            seen["args"], seen["kwargs"] = args, kwargs
            process = MagicMock()
            process.communicate = AsyncMock(return_value=(b" 42 \n", b""))
            process.returncode = 0
            return process

        monkeypatch.setattr(qalc_module, "QALC_PACKAGE", "/bin/qalc")
        monkeypatch.setattr(qalc_module.asyncio, "create_subprocess_exec", spawn)
        assert await Qalc(fakes.make_bot()).qalc_expression("--help") == "42"

        # the expression comes after --, so it can never be read as an option
        assert seen["args"] == ("/bin/qalc", "-t", "--", "--help")
        assert seen["kwargs"]["env"] is QALC_ENVIRONMENT

    async def test_failure_exit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def spawn(*args: Any, **kwargs: Any) -> Any:
            process = MagicMock()
            process.communicate = AsyncMock(return_value=(b"error", b""))
            process.returncode = 1
            return process

        monkeypatch.setattr(qalc_module, "QALC_PACKAGE", "/bin/qalc")
        monkeypatch.setattr(qalc_module.asyncio, "create_subprocess_exec", spawn)
        assert await Qalc(fakes.make_bot()).qalc_expression("sqrt(") is None

    async def test_cancel_kills(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        sleep = shutil.which("sleep")
        if sleep is None:
            pytest.skip("no sleep binary")

        # a stand-in qalc that never answers; PATH is empty inside, hence the full path
        script = tmp_path / "qalc"
        script.write_text(f"#!/bin/sh\nexec {sleep} 30\n")
        script.chmod(0o755)
        monkeypatch.setattr(qalc_module, "QALC_PACKAGE", str(script))

        spawned: list[asyncio.subprocess.Process] = []
        real_spawn = asyncio.create_subprocess_exec

        async def spawn(*args: Any, **kwargs: Any) -> asyncio.subprocess.Process:
            process = await real_spawn(*args, **kwargs)
            spawned.append(process)
            return process

        monkeypatch.setattr(qalc_module.asyncio, "create_subprocess_exec", spawn)

        task = asyncio.create_task(Qalc(fakes.make_bot()).qalc_expression("1"))
        while not spawned:
            await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        # killed and reaped, not left running for thirty seconds
        assert spawned[0].returncode is not None

    @needs_qalc
    @pytest.mark.parametrize(
        ("expression", "expected"),
        [("6 * 7", "42"), ("-5 + 2", "−3"), ("2^10", "1024"), ("100 cm to m", "1 m")],
    )
    async def test_real_qalc(self, expression: str, expected: str) -> None:
        assert await Qalc(fakes.make_bot()).qalc_expression(expression) == expected

    @needs_qalc
    async def test_real_qalc_invalid(self) -> None:
        assert await Qalc(fakes.make_bot()).qalc_expression("sqrt(") is None

    @needs_qalc
    async def test_real_qalc_command_finds_nothing(self) -> None:
        # even unblocked, command has no PATH to find a program on
        result = await Qalc(fakes.make_bot()).qalc_expression('command("id")')
        assert result is None or "uid=" not in result


class TestPaginate:
    def test_joins(self) -> None:
        assert paginate(["Reimu", "Marisa"], 100, "\n\n") == ["Reimu\n\nMarisa"]

    def test_splits(self) -> None:
        pages = paginate(["a" * 40, "b" * 40, "c" * 40], 85, "\n")
        assert pages == ["a" * 40 + "\n" + "b" * 40, "c" * 40]
        assert all(len(page) <= 85 for page in pages)

    def test_separator_counts(self) -> None:
        # ten and ten with a two character separator is 22, one past the limit
        assert paginate(["a" * 10, "b" * 10], 21, "\n\n") == ["a" * 10, "b" * 10]
        assert paginate(["a" * 10, "b" * 10], 22, "\n\n") == ["a" * 10 + "\n\n" + "b" * 10]

    def test_empty(self) -> None:
        assert paginate([], 100, "\n") == []

    def test_huge_line(self) -> None:
        pages = paginate(["x" * 9000], 750, "\n")
        assert len(pages) == 1
        assert len(pages[0]) == 4096


def ready[T](value: T) -> Awaitable[T]:
    async def coroutine() -> T:
        return value

    return coroutine()


class FakePage:
    """Just enough of wikipediaapi.AsyncWikipediaPage, whose properties are awaitables."""

    def __init__(
        self,
        title: str = "Hakurei Reimu",
        *,
        exists: bool = True,
        summary: str = "",
        categories: tuple[str, ...] = (),
        links: tuple[str, ...] = (),
        images: tuple[str, ...] = (),
    ) -> None:
        self.title = title
        self._exists = exists
        self._summary = summary
        self._categories = {name: None for name in categories}
        self._links = {name: None for name in links}
        self._images = {name: SimpleImage(name) for name in images}

    async def exists(self) -> bool:
        return self._exists

    @property
    def summary(self) -> Awaitable[str]:
        return ready(self._summary)

    @property
    def categories(self) -> Awaitable[dict]:
        return ready(self._categories)

    @property
    def links(self) -> Awaitable[dict]:
        return ready(self._links)

    @property
    def images(self) -> Awaitable[dict]:
        return ready(self._images)

    @property
    def fullurl(self) -> Awaitable[str]:
        return ready(f"https://en.wikipedia.org/wiki/{self.title.replace(' ', '_')}")


class SimpleImage:
    def __init__(self, name: str) -> None:
        self.name = name

    @property
    def url(self) -> Awaitable[str]:
        return ready(f"https://upload.wikimedia.org/{self.name}")


@pytest.fixture
async def wiki() -> AsyncIterator[Wikipedia]:
    cog = fakes.make_cog(Wikipedia)
    # the real client is closed at once, and a fake answers in its place
    await cog.cog_unload()
    cog._wiki = MagicMock()
    yield cog


@pytest.fixture
def client(wiki: Wikipedia) -> MagicMock:
    return cast(MagicMock, wiki._wiki)


class TestWiki:
    async def test_summary(self, wiki: Wikipedia, client: MagicMock) -> None:
        page = FakePage(summary="The shrine maiden.\n\nShe likes tea.", images=("reimu.png",))
        client.page.return_value = page
        ctx = fakes.make_ctx()
        await fakes.call(wiki.wiki, ctx, page_name="Hakurei Reimu")

        ctx.defer.assert_awaited_once()
        client.page.assert_called_once_with("Hakurei Reimu")
        embed = fakes.sent_embed(ctx.reply)
        assert embed.title == "Hakurei Reimu"
        assert embed.url == "https://en.wikipedia.org/wiki/Hakurei_Reimu"
        assert embed.description == "The shrine maiden.\n\nShe likes tea."
        assert embed.thumbnail.url == "https://upload.wikimedia.org/reimu.png"
        assert embed.footer.text == "Powered by Wikipedia"

    async def test_no_images(self, wiki: Wikipedia, client: MagicMock) -> None:
        client.page.return_value = FakePage(summary="Tea.")
        ctx = fakes.make_ctx()
        await fakes.call(wiki.wiki, ctx, page_name="Tea")
        assert fakes.sent_embed(ctx.reply).thumbnail.url == WIKIPEDIA_ICON

    async def test_empty_summary(self, wiki: Wikipedia, client: MagicMock) -> None:
        client.page.return_value = FakePage()
        ctx = fakes.make_ctx()
        await fakes.call(wiki.wiki, ctx, page_name="Hakurei Reimu")
        assert fakes.sent_embed(ctx.reply).description == "No summary available."

    async def test_long_summary_paginates(self, wiki: Wikipedia, client: MagicMock) -> None:
        summary = "\n".join(f"Paragraph {n}: " + "danmaku " * 40 for n in range(10))
        client.page.return_value = FakePage(summary=summary)
        ctx = fakes.make_ctx()
        await fakes.call(wiki.wiki, ctx, page_name="Danmaku")

        view = fakes.sent(ctx.reply)["view"]
        assert isinstance(view, lyviews.PaginatorView)
        assert len(view.embeds) > 1
        for embed in view.embeds:
            fakes.assert_embed_fits(embed)
        text = "".join(embed.description or "" for embed in view.embeds)
        assert all(f"Paragraph {n}:" in text for n in range(10))

    async def test_missing(self, wiki: Wikipedia, client: MagicMock) -> None:
        client.page.return_value = FakePage(exists=False)
        ctx = fakes.make_ctx()
        with pytest.raises(lyerrors.TakinaNotFoundError, match="does not exist"):
            await fakes.call(wiki.wiki, ctx, page_name="Hakurei reimu")
        ctx.reply.assert_not_awaited()

    async def test_disambiguation(self, wiki: Wikipedia, client: MagicMock) -> None:
        client.page.return_value = FakePage(
            "Mercury",
            categories=(DISAMBIGUATION_CATEGORY,),
            links=("Mercury (planet)", "Mercury (element)", "Mercury (mythology)"),
        )
        ctx = fakes.make_ctx()
        await fakes.call(wiki.wiki, ctx, page_name="mercury")

        embed = fakes.sent_embed(ctx.reply)
        assert embed.title == 'Disambiguations for "mercury"'
        assert embed.description == (
            "- Mercury (planet)\n- Mercury (element)\n- Mercury (mythology)"
        )

    async def test_disambiguation_paginates(self, wiki: Wikipedia, client: MagicMock) -> None:
        links = tuple(f"Lord of the Mysteries (part {n})" for n in range(40))
        client.page.return_value = FakePage(
            "Lord of the Mysteries", categories=(DISAMBIGUATION_CATEGORY,), links=links
        )
        ctx = fakes.make_ctx()
        await fakes.call(wiki.wiki, ctx, page_name="Lord of the Mysteries")

        view = fakes.sent(ctx.reply)["view"]
        assert all(len(embed.description or "") <= 300 for embed in view.embeds)
        lines = [line for embed in view.embeds for line in (embed.description or "").splitlines()]
        assert lines == [f"- {name}" for name in links]

    async def test_disambiguation_without_links(self, wiki: Wikipedia, client: MagicMock) -> None:
        client.page.return_value = FakePage(categories=(DISAMBIGUATION_CATEGORY,))
        with pytest.raises(lyerrors.TakinaNotFoundError, match="links to nothing"):
            await fakes.call(wiki.wiki, fakes.make_ctx(), page_name="Nothing")

    async def test_long_query_title(self, wiki: Wikipedia, client: MagicMock) -> None:
        client.page.return_value = FakePage(categories=(DISAMBIGUATION_CATEGORY,), links=("x",))
        ctx = fakes.make_ctx()
        await fakes.call(wiki.wiki, ctx, page_name="Fumo " * 60)
        assert len(fakes.sent_embed(ctx.reply).title or "") <= 256


class TestRandomWiki:
    async def test_random(self, wiki: Wikipedia, client: MagicMock) -> None:
        page = FakePage("Cirno", summary="The strongest.")
        client.random = AsyncMock(return_value={"Cirno": page})
        ctx = fakes.make_ctx()
        await fakes.call(wiki.randomwiki, ctx)

        assert fakes.sent_embed(ctx.reply).title == "Cirno"

    async def test_skips_disambiguations(self, wiki: Wikipedia, client: MagicMock) -> None:
        pages = [
            FakePage("Mercury", categories=(DISAMBIGUATION_CATEGORY,)),
            FakePage("Mars", categories=(DISAMBIGUATION_CATEGORY,)),
            FakePage("Marisa Kirisame", summary="An ordinary magician."),
        ]
        client.random = AsyncMock(side_effect=[{page.title: page} for page in pages])
        ctx = fakes.make_ctx()
        await fakes.call(wiki.randomwiki, ctx)

        assert client.random.await_count == 3
        assert fakes.sent_embed(ctx.reply).title == "Marisa Kirisame"

    async def test_gives_up(self, wiki: Wikipedia, client: MagicMock) -> None:
        page = FakePage("Mercury", categories=(DISAMBIGUATION_CATEGORY,))
        client.random = AsyncMock(return_value={"Mercury": page})
        ctx = fakes.make_ctx()
        with pytest.raises(lyerrors.TakinaError, match="disambiguation"):
            await fakes.call(wiki.randomwiki, ctx)

        assert client.random.await_count == MAX_RANDOM_ATTEMPTS
        ctx.reply.assert_not_awaited()


async def test_real_client_user_agent() -> None:
    cog = Wikipedia(fakes.make_bot())
    try:
        assert config.USER_AGENT in str(cog._wiki._client.headers.get("user-agent", ""))
    finally:
        await cog.cog_unload()
