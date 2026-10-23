# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.listeners.github import GitHub, PR_ISSUE_PATTERN, REPO_PATTERN
from takina.cogs.listeners import github as github_module
from takina import config, database, models
from types import SimpleNamespace
from takina.libs import lyerrors
from tests import fakes
from typing import Any
import pytest

REPO: dict[str, Any] = {
    "full_name": "orangci/takina",
    "description": "A multipurpose Discord bot.",
    "html_url": "https://github.com/orangci/takina",
    "stargazers_count": 42,
    "forks_count": 7,
    "open_issues_count": 1234,
    "owner": {"avatar_url": "https://avatars.githubusercontent.com/u/1"},
}


def issue(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "number": 138,
        "title": "default prefix not detected",
        "state": "open",
        "body": "Takina ignores `takina serverinfo`.",
        "html_url": "https://github.com/orangci/takina/issues/138",
        "repository_url": "https://api.github.com/repos/orangci/takina",
        "comments": 1500,
        "user": {"login": "dragsbruh", "avatar_url": "https://avatars.githubusercontent.com/u/2"},
        "updated_at": "2026-10-23T14:00:00Z",
    }
    return data | overrides


class TestPatterns:
    @pytest.mark.parametrize(
        ("text", "groups"),
        [
            ("see orangci/takina#138", ("orangci", "takina", "138")),
            ("Rapptz/discord.py#2000 broke", ("Rapptz", "discord.py", "2000")),
            ("(a-b/c_d.e#1)", ("a-b", "c_d.e", "1")),
        ],
    )
    def test_issue_matches(self, text: str, groups: tuple[str, ...]) -> None:
        match = PR_ISSUE_PATTERN.search(text)
        assert match is not None and match.groups() == groups

    @pytest.mark.parametrize(
        "text",
        [
            "https://example.com/path#1",
            "example.com/path#1",
            "/usr/share#1",
            "orangci/takina#",
            "orangci/takina #1",
            "a" * 40 + "/repo#1",
        ],
    )
    def test_issue_ignores(self, text: str) -> None:
        assert PR_ISSUE_PATTERN.search(text) is None

    @pytest.mark.parametrize(
        "text", ["repo:orangci/takina", "gh:orangci/takina", "GitHub:orangci/takina please"]
    )
    def test_repo_matches(self, text: str) -> None:
        match = REPO_PATTERN.search(text)
        assert match is not None and match.groups() == ("orangci", "takina")

    def test_repo_needs_keyword(self) -> None:
        assert REPO_PATTERN.search("orangci/takina") is None


@pytest.fixture
def world(api: fakes.FakeAPI) -> SimpleNamespace:
    guild = fakes.make_guild()
    cog = fakes.make_cog(GitHub)
    return SimpleNamespace(api=api, guild=guild, cog=cog)


def message(world: SimpleNamespace, content: str) -> Any:
    return fakes.make_message(
        author=fakes.make_member(world.guild),
        channel=fakes.make_channel(world.guild),
        guild=world.guild,
        content=content,
    )


@pytest.mark.usefixtures("db")
class TestPreviews:
    async def test_repository(self, world: SimpleNamespace) -> None:
        world.api.add(r"/repos/orangci/takina$", REPO)
        msg = message(world, "check out repo:orangci/takina")
        await world.cog.on_message(msg)

        embed = fakes.sent_embed(msg.reply)
        assert embed.title == "orangci/takina"
        assert embed.url == "https://github.com/orangci/takina"
        values = {field.name: field.value for field in embed.fields}
        assert values["Stars"] == "[42](https://github.com/orangci/takina/stargazers)"
        assert (values["Open issues"] or "").startswith("[1,234]")
        assert fakes.sent(msg.reply)["mention_author"] is False

    async def test_repository_without_description(self, world: SimpleNamespace) -> None:
        world.api.add(r"/repos/orangci/takina$", REPO | {"description": None})
        msg = message(world, "gh:orangci/takina")
        await world.cog.on_message(msg)
        assert fakes.sent_embed(msg.reply).description == "No description provided."

    async def test_issue(self, world: SimpleNamespace) -> None:
        world.api.add(r"/issues/138$", issue())
        msg = message(world, "orangci/takina#138")
        await world.cog.on_message(msg)

        embed = fakes.sent_embed(msg.reply)
        assert embed.title == "Issue #138: default prefix not detected"
        values = {field.name: field.value for field in embed.fields}
        # #48: the api's repository url is json, so the link goes to the page instead
        assert values["Repository"] == "[orangci/takina](https://github.com/orangci/takina)"
        assert values["Status"] == "Open"
        assert values["Comments"] == "1,500"
        assert embed.author.name == "dragsbruh"
        assert embed.footer.text == "Last updated October 23rd, 2026 at 14:00 UTC"

    @pytest.mark.parametrize(
        ("pull_request", "state", "status"),
        [
            ({"merged_at": None}, "open", "Open"),
            ({"merged_at": None}, "closed", "Closed"),
            ({"merged_at": "2026-10-22T10:00:00Z"}, "closed", "Merged"),
        ],
    )
    async def test_pull_request(
        self, world: SimpleNamespace, pull_request: dict, state: str, status: str
    ) -> None:
        world.api.add(r"/issues/131$", issue(number=131, pull_request=pull_request, state=state))
        msg = message(world, "orangci/takina#131")
        await world.cog.on_message(msg)

        embed = fakes.sent_embed(msg.reply)
        assert embed.title is not None and embed.title.startswith("Pull Request #131")
        assert {field.name: field.value for field in embed.fields}["Status"] == status

    async def test_long_body_and_title_cut(self, world: SimpleNamespace) -> None:
        world.api.add(r"/issues/1$", issue(number=1, title="t" * 300, body="b" * 5000))
        msg = message(world, "orangci/takina#1")
        await world.cog.on_message(msg)

        embed = fakes.sent_embed(msg.reply)
        assert len(embed.description or "") <= github_module.MAX_BODY_LENGTH + 1
        assert (embed.description or "").endswith("…")

    async def test_empty_body_and_ghost_user(self, world: SimpleNamespace) -> None:
        world.api.add(r"/issues/1$", issue(number=1, body=None, user=None))
        msg = message(world, "orangci/takina#1")
        await world.cog.on_message(msg)

        embed = fakes.sent_embed(msg.reply)
        assert embed.description == "No description provided."
        assert embed.author.name is None

    async def test_not_a_repository(self, world: SimpleNamespace) -> None:
        world.api.add(r"github", lyerrors.TakinaNotFoundError("Not found."))
        msg = message(world, "and/or#2")
        await world.cog.on_message(msg)
        msg.reply.assert_not_awaited()

    async def test_rate_limit_is_quiet(
        self, world: SimpleNamespace, caplog: pytest.LogCaptureFixture
    ) -> None:
        world.api.add(r"github", lyerrors.TakinaError("Error [403]"))
        msg = message(world, "orangci/takina#1")
        await world.cog.on_message(msg)
        msg.reply.assert_not_awaited()
        assert any("failed" in record.message for record in caplog.records)

    async def test_timeout_is_quiet(self, world: SimpleNamespace) -> None:
        world.api.add(r"github", TimeoutError())
        msg = message(world, "orangci/takina#1")
        await world.cog.on_message(msg)
        msg.reply.assert_not_awaited()

    @pytest.mark.parametrize("content", ["./..#1", "owner/.#1", "owner/..#1"])
    async def test_dot_repositories_skipped(self, world: SimpleNamespace, content: str) -> None:
        msg = message(world, content)
        await world.cog.on_message(msg)
        assert world.api.calls == []

    async def test_ordinary_messages_cost_nothing(self, world: SimpleNamespace) -> None:
        await world.cog.on_message(message(world, "good morning gensokyo"))
        assert world.api.calls == []

    async def test_bots_ignored(self, world: SimpleNamespace) -> None:
        msg = message(world, "orangci/takina#1")
        msg.author.bot = True
        await world.cog.on_message(msg)
        assert world.api.calls == []

    async def test_repo_wins_over_issue(self, world: SimpleNamespace) -> None:
        world.api.add(r"/repos/orangci/takina$", REPO)
        await world.cog.on_message(message(world, "repo:orangci/takina and orangci/takina#1"))
        assert world.api.urls() == ["https://api.github.com/repos/orangci/takina"]

    async def test_turned_off(self, world: SimpleNamespace) -> None:
        await database.save(
            models.GuildSettingsModel(guild_id=world.guild.id, github_previews=False)
        )
        await world.cog.on_message(message(world, "orangci/takina#1"))
        assert world.api.calls == []

    async def test_on_by_default(self, world: SimpleNamespace) -> None:
        world.api.add(r"/issues/1$", issue(number=1))
        await world.cog.on_message(message(world, "orangci/takina#1"))
        assert len(world.api.calls) == 1

    async def test_dms_always_on(self, world: SimpleNamespace) -> None:
        world.api.add(r"/issues/1$", issue(number=1))
        dm = fakes.make_message(
            author=fakes.make_user(), channel=fakes.make_channel(), content="orangci/takina#1"
        )
        await world.cog.on_message(dm)
        dm.reply.assert_awaited_once()


class TestFetch:
    async def test_cached(self, world: SimpleNamespace) -> None:
        world.api.add(r"github", REPO)
        await world.cog.fetch("https://api.github.com/repos/orangci/takina")
        await world.cog.fetch("https://api.github.com/repos/orangci/takina")
        assert len(world.api.calls) == 1

    async def test_misses_cached_too(self, world: SimpleNamespace) -> None:
        world.api.add(r"github", lyerrors.TakinaNotFoundError("Not found."))
        assert await world.cog.fetch("https://api.github.com/repos/a/b") is None
        assert await world.cog.fetch("https://api.github.com/repos/a/b") is None
        assert len(world.api.calls) == 1

    async def test_errors_not_cached(self, world: SimpleNamespace) -> None:
        world.api.add(r"github", lyerrors.TakinaError("Error [403]"))
        await world.cog.fetch("https://api.github.com/repos/a/b")
        await world.cog.fetch("https://api.github.com/repos/a/b")
        assert len(world.api.calls) == 2

    async def test_expires(self, world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
        world.api.add(r"github", REPO)
        await world.cog.fetch("https://api.github.com/repos/orangci/takina")

        now = github_module.time.monotonic()
        later = now + github_module.CACHE_SECONDS + 1
        monkeypatch.setattr(github_module.time, "monotonic", lambda: later)
        await world.cog.fetch("https://api.github.com/repos/orangci/takina")
        assert len(world.api.calls) == 2

    async def test_bounded(self, world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(github_module, "MAX_CACHE_ENTRIES", 3)
        world.api.add(r"github", REPO)
        clock = SimpleNamespace(now=0.0)
        monkeypatch.setattr(github_module.time, "monotonic", lambda: clock.now)

        for number in range(10):
            clock.now += github_module.CACHE_SECONDS
            await world.cog.fetch(f"https://api.github.com/repos/a/{number}")
        assert len(world.cog._cache) <= 3

    async def test_token_sent(
        self, world: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(config, "GITHUB_AUTH_TOKEN", "marisa-token")
        world.api.add(r"github", REPO)
        await world.cog.fetch("https://api.github.com/repos/orangci/takina")

        headers = world.api.calls[0][1]["headers"]
        assert headers["Authorization"] == "Bearer marisa-token"
        assert headers["Accept"] == "application/vnd.github+json"

    async def test_no_token(self, world: SimpleNamespace) -> None:
        world.api.add(r"github", REPO)
        await world.cog.fetch("https://api.github.com/repos/orangci/takina")
        assert "Authorization" not in world.api.calls[0][1]["headers"]
