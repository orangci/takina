# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.fun.mysteries import EIGHT_BALL_RESPONSES, ORANGC_ID, TAKINA_ID, ETHAN_ID
from takina.cogs.fun.fun import JOKE_CATEGORIES, Fun, image_url
from takina.cogs.fun.mysteries import Mysteries
from takina.cogs.fun.neko import API_URL, Neko
from takina.cogs.fun import fun as fun_module
from takina.libs.fate_responses import fates
from takina.libs.topics_list import topics
from takina.cogs.fun.ias import Ias
from takina.libs import lyerrors
from typing import Any, cast
from urllib import parse
from tests import fakes
import aiohttp
import pytest


@pytest.fixture
def ctx() -> fakes.MagicMock:
    return fakes.make_ctx()


class TestImageUrl:
    def test_url(self) -> None:
        assert image_url({"url": "https://api.garythe.cat/gary.png"}) == (
            "https://api.garythe.cat/gary.png"
        )

    @pytest.mark.parametrize("data", [{}, {"url": ""}, {"url": None}])
    def test_missing(self, data: dict) -> None:
        with pytest.raises(lyerrors.TakinaError):
            image_url(data)


class TestFact:
    async def test_fact(self, ctx: fakes.MagicMock, api: fakes.FakeAPI) -> None:
        api.add(r"uselessfacts", {"text": "Cirno is the strongest."})
        await fakes.call(fakes.make_cog(Fun).fact, ctx)

        embed = fakes.sent_embed(ctx.reply)
        assert embed.description is not None
        assert embed.description.startswith("Cirno is the strongest.")
        assert fakes.sent(ctx.reply)["mention_author"] is False

    @pytest.mark.parametrize("data", [{}, {"text": ""}])
    async def test_no_fact(self, ctx: fakes.MagicMock, api: fakes.FakeAPI, data: dict) -> None:
        api.add(r"uselessfacts", data)
        with pytest.raises(lyerrors.TakinaError):
            await fakes.call(fakes.make_cog(Fun).fact, ctx)
        ctx.reply.assert_not_awaited()


class TestJoke:
    @pytest.fixture
    def pick(self, monkeypatch: pytest.MonkeyPatch):
        def choose(kind: str) -> None:
            monkeypatch.setattr(fun_module.random, "choice", lambda options: kind)

        return choose

    async def test_dad_joke(self, ctx: fakes.MagicMock, api: fakes.FakeAPI, pick) -> None:
        pick("dadjoke")
        api.add(r"icanhazdadjoke", {"joke": "I'm reading a book on anti-gravity."})
        await fakes.call(fakes.make_cog(Fun).joke, ctx)

        _, kwargs = api.calls[0]
        assert kwargs["headers"] == {"Accept": "application/json"}
        assert (fakes.sent_embed(ctx.reply).description or "").startswith("I'm reading a book")

    async def test_single_part(self, ctx: fakes.MagicMock, api: fakes.FakeAPI, pick) -> None:
        pick("regular")
        api.add(r"jokeapi", {"joke": "A SQL query walks into a bar."})
        await fakes.call(fakes.make_cog(Fun).joke, ctx)

        assert f"/joke/{JOKE_CATEGORIES}?safe-mode" in api.urls()[0]
        assert "Christmas" not in JOKE_CATEGORIES
        assert (fakes.sent_embed(ctx.reply).description or "").startswith("A SQL query")

    async def test_two_part(self, ctx: fakes.MagicMock, api: fakes.FakeAPI, pick) -> None:
        pick("regular")
        api.add(r"jokeapi", {"setup": "Why did Cirno fail maths?", "delivery": "She's a ⑨."})
        await fakes.call(fakes.make_cog(Fun).joke, ctx)

        description = fakes.sent_embed(ctx.reply).description
        assert description is not None
        assert description.startswith("Why did Cirno fail maths?\nShe's a ⑨.")

    @pytest.mark.parametrize(
        "data",
        [
            {"error": True, "message": "No matching joke found"},
            {"setup": "Half a joke"},
            {"delivery": "Only a punchline"},
        ],
    )
    async def test_error_body(
        self, ctx: fakes.MagicMock, api: fakes.FakeAPI, pick, data: dict
    ) -> None:
        pick("regular")
        api.add(r"jokeapi", data)
        with pytest.raises(lyerrors.TakinaError):
            await fakes.call(fakes.make_cog(Fun).joke, ctx)

    async def test_no_dad_joke(self, ctx: fakes.MagicMock, api: fakes.FakeAPI, pick) -> None:
        pick("dadjoke")
        api.add(r"icanhazdadjoke", {})
        with pytest.raises(lyerrors.TakinaError):
            await fakes.call(fakes.make_cog(Fun).joke, ctx)


class TestCommit:
    async def test_same_action_same_answer(self, ctx: fakes.MagicMock) -> None:
        cog = fakes.make_cog(Fun)
        await fakes.call(cog.commit, ctx, action="arson")
        await fakes.call(cog.commit, ctx, action="arson")

        first, second = (fakes.sent_embed(ctx.reply, i).description for i in (0, 1))
        assert first == second

    async def test_varies_by_action(self, ctx: fakes.MagicMock) -> None:
        cog = fakes.make_cog(Fun)
        actions = [f"steal {n} donation boxes" for n in range(20)]
        for action in actions:
            await fakes.call(cog.commit, ctx, action=action)

        answers = {fakes.sent_embed(ctx.reply, i).description for i in range(len(actions))}
        assert len(answers) > 1


class TestGoogle:
    async def test_quotes_query(self, ctx: fakes.MagicMock) -> None:
        query = "shawarma near the human village & co?"
        await fakes.call(fakes.make_cog(Fun).google, ctx, query=query)

        embed = fakes.sent_embed(ctx.reply)
        expected = f"https://letmegooglethat.com/?q={parse.quote_plus(query)}"
        assert embed.url == expected
        assert embed.fields[0].value == expected
        assert f"**{query}**" in (embed.description or "")
        assert " " not in (embed.url or "")


class TestRoll:
    async def test_in_range(self, ctx: fakes.MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
        bounds: list[tuple[int, int]] = []

        def randint(low: int, high: int) -> int:
            bounds.append((low, high))
            return 9

        monkeypatch.setattr(fun_module.random, "randint", randint)
        await fakes.call(fakes.make_cog(Fun).roll, ctx)

        assert bounds == [(1, 100)]
        assert "You rolled 9!" in (fakes.sent_embed(ctx.reply).description or "")


class TestImages:
    @pytest.mark.parametrize("name", ["gary", "goober"])
    async def test_image(self, ctx: fakes.MagicMock, api: fakes.FakeAPI, name: str) -> None:
        api.add(rf"garythe\.cat/{name}$", {"url": f"https://cdn.garythe.cat/{name}.jpg"})
        await fakes.call(getattr(fakes.make_cog(Fun), name), ctx)

        embed = fakes.sent_embed(ctx.reply)
        assert embed.image.url == f"https://cdn.garythe.cat/{name}.jpg"
        assert embed.title == name.title()

    @pytest.mark.parametrize("name", ["gary", "goober"])
    async def test_no_image(self, ctx: fakes.MagicMock, api: fakes.FakeAPI, name: str) -> None:
        api.add(r"garythe\.cat", {})
        with pytest.raises(lyerrors.TakinaError):
            await fakes.call(getattr(fakes.make_cog(Fun), name), ctx)

    @pytest.mark.parametrize("name", ["gary", "goober"])
    async def test_needs_embed_links(self, name: str) -> None:
        guild = fakes.make_guild()
        ctx = fakes.make_ctx(guild=guild)
        command = getattr(fakes.make_cog(Fun, ctx.bot), name)
        with pytest.raises(lyerrors.TakinaPermissionError):
            await fakes.run_checks(command, ctx)


class TestRoast:
    async def test_without_target(self, ctx: fakes.MagicMock, api: fakes.FakeAPI) -> None:
        api.add(r"insult\.mattbas", "You are as useful as a screen door on a submarine")
        await fakes.call(fakes.make_cog(Fun).roast, ctx)

        assert api.calls[0][1]["disable_json"] is True
        reply = fakes.sent(ctx.reply)
        assert reply["content"] is None
        assert reply["embed"].description.endswith("submarine.")

    async def test_with_target(self, ctx: fakes.MagicMock, api: fakes.FakeAPI) -> None:
        api.add(r"insult\.mattbas", "You smell of mushrooms")
        marisa = fakes.make_user(name="marisa")
        await fakes.call(fakes.make_cog(Fun).roast, ctx, marisa)

        assert fakes.sent(ctx.reply)["content"] == marisa.mention


class TestTopic:
    async def test_topic(self, ctx: fakes.MagicMock) -> None:
        await fakes.call(fakes.make_cog(Fun).topic, ctx)
        description = fakes.sent_embed(ctx.reply).description or ""
        assert any(description.startswith(topic) for topic in topics)

    def test_topics_fit(self) -> None:
        assert topics
        assert all(len(topic) < 4000 and topic.strip() for topic in topics)


class TestIas:
    @pytest.mark.parametrize("name", ["uma", "touhou"])
    async def test_image(self, ctx: fakes.MagicMock, api: fakes.FakeAPI, name: str) -> None:
        api.add(
            rf"iostpa\.com/{name}$",
            {"image_link": "https://i.iostpa.com/reimu.png", "twitter_link": "https://x.com/zun"},
        )
        await fakes.call(getattr(fakes.make_cog(Ias), name), ctx)

        embed = fakes.sent_embed(ctx.reply)
        assert embed.image.url == "https://i.iostpa.com/reimu.png"
        assert embed.author.name == "Source"
        assert embed.author.url == "https://x.com/zun"

    async def test_no_image(self, ctx: fakes.MagicMock, api: fakes.FakeAPI) -> None:
        api.add(r"iostpa", {"twitter_link": "https://x.com/zun"})
        with pytest.raises(lyerrors.TakinaError):
            await fakes.call(fakes.make_cog(Ias).touhou, ctx)

    def test_aliases(self) -> None:
        cog = fakes.make_cog(Ias)
        assert "2hu" in cog.touhou.aliases
        assert "umamusume" in cog.uma.aliases


class TestEightBall:
    async def test_deterministic(self, ctx: fakes.MagicMock) -> None:
        cog = fakes.make_cog(Mysteries)
        await fakes.call(cog.eight_ball, ctx, question="will it rain in gensokyo")
        await fakes.call(cog.eight_ball, ctx, question="will it rain in gensokyo")

        first, second = (fakes.sent_embed(ctx.reply, i).description for i in (0, 1))
        assert first == second
        assert first is not None
        answer = first.split("**Answer:** ")[1]
        assert answer in EIGHT_BALL_RESPONSES

    def test_balanced(self) -> None:
        # as many yeses as noes, so the ball has no favourite
        assert len(EIGHT_BALL_RESPONSES) == 20
        assert len(set(EIGHT_BALL_RESPONSES)) == 20

    async def test_shows_question(self, ctx: fakes.MagicMock) -> None:
        await fakes.call(fakes.make_cog(Mysteries).eight_ball, ctx, question="am i the strongest")
        assert "**Question:** am i the strongest" in (fakes.sent_embed(ctx.reply).description or "")


class TestFate:
    async def test_symmetric(self) -> None:
        # the seed is the sum of both ids, so it reads the same either way round
        reimu, marisa = fakes.make_user(name="reimu"), fakes.make_user(name="marisa")
        cog = fakes.make_cog(Mysteries)

        forward = fakes.make_ctx(author=reimu)
        backward = fakes.make_ctx(author=marisa)
        await fakes.call(cog.fate, forward, marisa)
        await fakes.call(cog.fate, backward, reimu)

        one = (fakes.sent_embed(forward.reply).description or "").replace(marisa.mention, "X")
        two = (fakes.sent_embed(backward.reply).description or "").replace(reimu.mention, "X")
        assert one == two
        assert fakes.sent_embed(forward.reply).footer.text == "In another universe..."

    async def test_fills_target(self) -> None:
        marisa = fakes.make_user(name="marisa")
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Mysteries).fate, ctx, marisa)

        description = fakes.sent_embed(ctx.reply).description or ""
        assert "{target}" not in description
        templates = [fate.format(target=marisa.mention) for fate in fates]
        assert any(description.endswith(template) for template in templates)

    async def test_self(self) -> None:
        reimu = fakes.make_user(name="reimu")
        ctx = fakes.make_ctx(author=reimu)
        await fakes.call(fakes.make_cog(Mysteries).fate, ctx, reimu)

        embed = fakes.sent_embed(ctx.reply)
        assert "the same person" in (embed.description or "")
        assert embed.footer.text is None

    @pytest.mark.parametrize(
        ("author_id", "expected"),
        [(ORANGC_ID, "daughter"), (ETHAN_ID, "niece"), (None, "mind your own business")],
    )
    async def test_takina(self, author_id: int | None, expected: str) -> None:
        bot = fakes.make_bot()
        ctx = fakes.make_ctx(bot=bot, author=fakes.make_user(user_id=author_id))
        await fakes.call(fakes.make_cog(Mysteries, bot).fate, ctx, bot.user)

        embed = fakes.sent_embed(ctx.reply)
        assert expected in (embed.description or "")
        assert embed.footer.text is None

    async def test_main_instance(self) -> None:
        # another instance answers for the main one too
        ctx = fakes.make_ctx()
        main = fakes.make_user(user_id=TAKINA_ID, bot=True)
        await fakes.call(fakes.make_cog(Mysteries, ctx.bot).fate, ctx, main)
        assert "mind your own business" in (fakes.sent_embed(ctx.reply).description or "")

    def test_fates_have_targets(self) -> None:
        assert all("{target}" in fate for fate in fates)
        for fate in fates:
            fate.format(target="<@1>")


async def autocomplete(cog: Neko, interaction: Any, current: str) -> list[Any]:
    # the decorator hides the plain method from type checkers, though it is one at runtime
    return await cast(Any, cog).category_autocomplete(interaction, current)


ENDPOINTS = {"neko": {"format": "png"}, "kitsune": {"format": "png"}, "hug": {"format": "gif"}}


class TestNeko:
    @pytest.fixture
    def endpoints(self, api: fakes.FakeAPI) -> fakes.FakeAPI:
        api.add(r"nekos\.best/api/v2/endpoints$", ENDPOINTS)
        return api

    def png(self, name: str = "neko") -> dict:
        return {
            "results": [
                {
                    "url": f"https://nekos.best/{name}.png",
                    "artist_name": "ZUN",
                    "artist_href": "https://x.com/zun",
                }
            ]
        }

    async def test_default(self, endpoints: fakes.FakeAPI) -> None:
        endpoints.add(r"/neko$", self.png())
        ctx = fakes.make_ctx(invoked_with="neko")
        await fakes.call(fakes.make_cog(Neko).neko, ctx)

        embed = fakes.sent_embed(ctx.reply)
        assert embed.image.url == "https://nekos.best/neko.png"
        assert embed.author.name == "Artist: ZUN"
        assert embed.author.url == "https://x.com/zun"

    async def test_kitsune_alias(self, endpoints: fakes.FakeAPI) -> None:
        endpoints.add(r"/kitsune$", self.png("kitsune"))
        ctx = fakes.make_ctx(invoked_with="kitsune")
        await fakes.call(fakes.make_cog(Neko).neko, ctx)
        assert f"{API_URL}/kitsune" in endpoints.urls()

    async def test_explicit_category_beats_alias(self, endpoints: fakes.FakeAPI) -> None:
        endpoints.add(r"/neko$", self.png())
        ctx = fakes.make_ctx(invoked_with="kitsune")
        await fakes.call(fakes.make_cog(Neko).neko, ctx, "NEKO")
        assert f"{API_URL}/neko" in endpoints.urls()

    async def test_gif(self, endpoints: fakes.FakeAPI) -> None:
        endpoints.add(
            r"/hug$", {"results": [{"url": "https://nekos.best/hug.gif", "anime_name": "Lycoris"}]}
        )
        ctx = fakes.make_ctx(invoked_with="neko")
        await fakes.call(fakes.make_cog(Neko).neko, ctx, "hug")

        embed = fakes.sent_embed(ctx.reply)
        assert embed.footer.text == "Anime: Lycoris"
        assert embed.author.name is None

    async def test_unknown_category(self, endpoints: fakes.FakeAPI) -> None:
        ctx = fakes.make_ctx(invoked_with="neko")
        with pytest.raises(lyerrors.TakinaNotFoundError) as caught:
            await fakes.call(fakes.make_cog(Neko).neko, ctx, "`" * 3 + "fumo" * 40)

        # no backticks to break out of the code span, and no wall of text
        message = str(caught.value)
        span = message.split("`")[1]
        assert span == ("fumo" * 40)[:50]
        assert len(endpoints.calls) == 1

    @pytest.mark.parametrize("data", [{}, {"results": []}, {"results": [{"url": ""}]}])
    async def test_empty(self, endpoints: fakes.FakeAPI, data: dict) -> None:
        endpoints.add(r"/neko$", data)
        ctx = fakes.make_ctx(invoked_with="neko")
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(fakes.make_cog(Neko).neko, ctx)

    async def test_endpoints_cached(self, endpoints: fakes.FakeAPI) -> None:
        endpoints.add(r"/neko$", self.png())
        cog = fakes.make_cog(Neko)
        for _ in range(3):
            await fakes.call(cog.neko, fakes.make_ctx(invoked_with="neko"))

        assert endpoints.urls().count(f"{API_URL}/endpoints") == 1

    async def test_autocomplete(self, endpoints: fakes.FakeAPI) -> None:
        cog = fakes.make_cog(Neko)
        interaction = fakes.make_interaction(user=fakes.make_user())

        choices = await autocomplete(cog, interaction, "")
        assert [choice.value for choice in choices] == sorted(ENDPOINTS)

        choices = await autocomplete(cog, interaction, "KIT")
        assert [choice.value for choice in choices] == ["kitsune"]

    async def test_autocomplete_caps_at_25(self, api: fakes.FakeAPI) -> None:
        api.add(r"/endpoints$", {f"endpoint{i:02}": {"format": "gif"} for i in range(40)})
        cog = fakes.make_cog(Neko)
        choices = await autocomplete(cog, fakes.make_interaction(user=fakes.make_user()), "")
        assert len(choices) == 25

    @pytest.mark.parametrize(
        "error", [lyerrors.TakinaError("down"), aiohttp.ClientConnectionError(), TimeoutError()]
    )
    async def test_autocomplete_failure(self, api: fakes.FakeAPI, error: Exception) -> None:
        api.add(r"/endpoints$", error)
        cog = fakes.make_cog(Neko)
        choices = await autocomplete(cog, fakes.make_interaction(user=fakes.make_user()), "")
        assert choices == []
        # nothing is cached, so the next try asks again
        assert cog._endpoints is None
