# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.weebism.character import Characters
from takina.libs import lyerrors, lymal, lyviews
from takina.cogs.weebism.manga import Manga
from takina.cogs.weebism.anime import Anime
from typing import Any, ClassVar
from tests import fakes
import pytest

LYCORIS: dict[str, Any] = {
    "mal_id": 50709,
    "url": "https://myanimelist.net/anime/50709/Lycoris_Recoil",
    "title": "Lycoris Recoil",
    "title_english": "Lycoris Recoil",
    "images": {"jpg": {"image_url": "https://cdn.myanimelist.net/lycoris.jpg"}},
    "type": "TV",
    "episodes": 13,
    "score": 8.2,
    "source": "Original",
    "aired": {"string": "Jul 2, 2022 to Sep 24, 2022"},
    "genres": [{"name": "Action"}, {"name": "Award Winning"}],
    "studios": [{"name": "A-1 Pictures"}],
    "rating": "PG-13 - Teens 13 or older",
    "synopsis": "Takina Inoue is reassigned to LycoReco.",
}


def found(entry: dict) -> dict:
    return {"data": [entry]}


class TestSearch:
    @pytest.mark.parametrize("kind", ["anime", "manga", "characters"])
    async def test_query(self, api: fakes.FakeAPI, kind: lymal.Kind) -> None:
        api.add(rf"tenrai\.org/v1/{kind}$", found({"mal_id": 1}))
        assert await lymal.search(kind, "lycoris") == {"mal_id": 1}

        url, kwargs = api.calls[0]
        assert url == f"{lymal.API_URL}/{kind}"
        # sfw always, and one result is all a command shows
        assert kwargs["params"] == {"q": "lycoris", "limit": 1, "sfw": "true"}
        assert kwargs["not_found"] == lymal.NOT_FOUND[kind]

    @pytest.mark.parametrize("data", [None, {}, {"data": []}, {"data": None}])
    async def test_empty(self, api: fakes.FakeAPI, data: Any) -> None:
        api.add(r"tenrai", data)
        with pytest.raises(lyerrors.TakinaNotFoundError, match="Manga not found"):
            await lymal.search("manga", "the empty box")

    async def test_first_result(self, api: fakes.FakeAPI) -> None:
        api.add(r"tenrai", {"data": [{"mal_id": 1}, {"mal_id": 2}]})
        assert (await lymal.search("anime", "x"))["mal_id"] == 1


class TestShown:
    @pytest.mark.parametrize(("value", "expected"), [(None, "Unknown"), ("", "Unknown")])
    def test_unknown(self, value: Any, expected: str) -> None:
        assert lymal.shown(value) == expected

    @pytest.mark.parametrize(("value", "expected"), [(0, "0"), (13, "13"), (8.2, "8.2")])
    def test_falsy_numbers_shown(self, value: Any, expected: str) -> None:
        # zero chapters is a number, not an unknown
        assert lymal.shown(value) == expected


class TestNames:
    def test_joins(self) -> None:
        assert lymal.names([{"name": "Action"}, {"name": "Drama"}]) == "Action, Drama"

    @pytest.mark.parametrize("entries", [None, [], [{"name": ""}], [{"id": 1}]])
    def test_unknown(self, entries: Any) -> None:
        assert lymal.names(entries) == "Unknown"

    def test_skips_nameless(self) -> None:
        assert lymal.names([{"name": "Action"}, {"id": 2}, {"name": None}]) == "Action"


class TestEntryEmbed:
    def test_full(self) -> None:
        embed = lymal.entry_embed(LYCORIS, "Lycoris Recoil")
        assert embed.title == "Lycoris Recoil"
        assert embed.url == LYCORIS["url"]
        assert embed.thumbnail.url == "https://cdn.myanimelist.net/lycoris.jpg"
        assert embed.footer.text == "MAL ID: 50709"

    @pytest.mark.parametrize("images", [None, {}, {"jpg": None}, {"jpg": {}}])
    def test_no_cover(self, images: Any) -> None:
        embed = lymal.entry_embed({"images": images}, "Marisa")
        assert embed.thumbnail.url is None
        assert embed.footer.text is None

    def test_long_title(self) -> None:
        embed = lymal.entry_embed({}, "Lord of the Mysteries " * 30)
        assert len(embed.title or "") == 256


class TestWordPages:
    def test_short(self) -> None:
        assert lymal.word_pages("Klein Moretti") == ["Klein Moretti"]

    def test_empty(self) -> None:
        assert lymal.word_pages("") == []

    def test_splits_between_words(self) -> None:
        text = " ".join(["fool"] * 300)
        pages = lymal.word_pages(text, limit=50)

        assert all(len(page) <= 50 for page in pages)
        assert all(not page.startswith(" ") and not page.endswith(" ") for page in pages)
        assert " ".join(pages) == text

    def test_exact_fit(self) -> None:
        # "aaaa bbbb" is nine characters, so it fits a nine character page
        assert lymal.word_pages("aaaa bbbb", limit=9) == ["aaaa bbbb"]
        assert lymal.word_pages("aaaa bbbbb", limit=9) == ["aaaa", "bbbbb"]

    def test_giant_word(self) -> None:
        # a word longer than any page still gets one, cut to what an embed holds
        pages = lymal.word_pages("x" * 5000, limit=500)
        assert len(pages) == 1
        assert len(pages[0]) == 4096

    def test_keeps_newlines(self) -> None:
        assert lymal.word_pages("line one\n\nline two") == ["line one\n\nline two"]


class TestSendSynopsis:
    async def test_one_page(self) -> None:
        ctx = fakes.make_ctx()
        await lymal.send_synopsis(ctx, {**LYCORIS, "title_english": "Lycoris Recoil"})

        embed = fakes.sent_embed(ctx.reply)
        # the english title is the same, so it isn't repeated
        assert embed.description == LYCORIS["synopsis"]
        assert fakes.sent(ctx.reply).get("view") is None

    async def test_english_title(self) -> None:
        ctx = fakes.make_ctx()
        entry = {
            "title": "Kimetsu no Yaiba",
            "title_english": "Demon Slayer",
            "synopsis": "Swords.",
        }
        await lymal.send_synopsis(ctx, entry)
        assert fakes.sent_embed(ctx.reply).description == "-# Demon Slayer\n\nSwords."

    async def test_missing(self) -> None:
        ctx = fakes.make_ctx()
        await lymal.send_synopsis(ctx, {})

        embed = fakes.sent_embed(ctx.reply)
        assert embed.title == "Unknown"
        assert embed.description == "No synopsis available."

    async def test_paginates(self) -> None:
        ctx = fakes.make_ctx()
        entry = {**LYCORIS, "synopsis": " ".join(["Chisato"] * 400)}
        await lymal.send_synopsis(ctx, entry)

        reply = fakes.sent(ctx.reply)
        view = reply["view"]
        assert isinstance(view, lyviews.PaginatorView)
        assert len(view.embeds) > 1
        for embed in view.embeds:
            fakes.assert_embed_fits(embed)
            assert embed.title == "Lycoris Recoil"
            assert embed.footer.text == "MAL ID: 50709"
        assert reply["embed"] is view.embeds[0]


class TestAnime:
    async def test_details(self, api: fakes.FakeAPI) -> None:
        api.add(r"tenrai\.org/v1/anime", found(LYCORIS))
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Anime).anime, ctx, anime_name="lycoris")

        ctx.defer.assert_awaited_once()
        description = fakes.sent_embed(ctx.reply).description or ""
        assert "-# " not in description
        for line in [
            "> **Type**: TV",
            "> **Episodes**: 13",
            "> **Score**: 8.2",
            "> **Source**: Original",
            "> **Aired**: Jul 2, 2022 to Sep 24, 2022",
            "> **Genres**: Action, Award Winning",
            "> **Studios**: A-1 Pictures",
            "> **Rating**: PG-13 - Teens 13 or older",
        ]:
            assert line in description

    async def test_airing(self, api: fakes.FakeAPI) -> None:
        # a show still airing has no episode count, and tenrai sends nulls everywhere
        api.add(
            r"tenrai",
            found({"title": "Reverse: 1999", "title_english": "Reverse 1999", "aired": None}),
        )
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Anime).anime, ctx, anime_name="reverse")

        description = fakes.sent_embed(ctx.reply).description or ""
        assert description.startswith("-# Reverse 1999\n")
        assert "> **Episodes**: Unknown" in description
        assert "> **Aired**: Unknown" in description
        assert "> **Studios**: Unknown" in description

    async def test_not_found(self, api: fakes.FakeAPI) -> None:
        api.add(r"tenrai", {"data": []})
        ctx = fakes.make_ctx()
        with pytest.raises(lyerrors.TakinaNotFoundError, match="Anime not found"):
            await fakes.call(fakes.make_cog(Anime).anime, ctx, anime_name="nothing")
        ctx.reply.assert_not_awaited()

    async def test_synopsis(self, api: fakes.FakeAPI) -> None:
        api.add(r"tenrai\.org/v1/anime", found(LYCORIS))
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Anime).anime_synopsis, ctx, anime_name="lycoris")
        assert fakes.sent_embed(ctx.reply).description == LYCORIS["synopsis"]


class TestManga:
    MARIA: ClassVar[dict[str, Any]] = {
        "mal_id": 17074,
        "title": "Utsuro no Hako to Zero no Maria",
        "title_english": "The Empty Box and Zeroth Maria",
        "status": "Finished",
        "chapters": 0,
        "volumes": 7,
        "score": 8.1,
        "genres": [{"name": "Mystery"}],
        "published": {"string": "Jan 2009 to Oct 2011"},
        "authors": [{"name": "Mikage, Eiji"}, {"name": "Tetsuo"}, {"id": 3}],
    }

    async def test_finished(self, api: fakes.FakeAPI) -> None:
        api.add(r"tenrai\.org/v1/manga", found(self.MARIA))
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Manga).manga, ctx, manga_name="maria")

        description = fakes.sent_embed(ctx.reply).description or ""
        assert description.startswith("-# The Empty Box and Zeroth Maria\n")
        assert "> **Chapters**: 0" in description
        assert "> **Volumes**: 7" in description
        assert "> **Status**: Finished" in description
        assert "> **Authors**: Mikage, Eiji & Tetsuo" in description
        assert "> **Published**: Jan 2009 to Oct 2011" in description

    async def test_publishing_hides_counts(self, api: fakes.FakeAPI) -> None:
        api.add(r"tenrai", found({**self.MARIA, "status": "Publishing"}))
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Manga).manga, ctx, manga_name="maria")

        description = fakes.sent_embed(ctx.reply).description or ""
        assert "Chapters" not in description
        assert "Volumes" not in description

    async def test_sparse(self, api: fakes.FakeAPI) -> None:
        api.add(r"tenrai", found({}))
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Manga).manga, ctx, manga_name="?")

        embed = fakes.sent_embed(ctx.reply)
        assert embed.title == "Unknown"
        assert "> **Authors**: Unknown" in (embed.description or "")
        assert "> **Status**: Unknown" in (embed.description or "")

    async def test_synopsis(self, api: fakes.FakeAPI) -> None:
        api.add(r"tenrai\.org/v1/manga", found({**self.MARIA, "synopsis": "A box."}))
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Manga).manga_synopsis, ctx, manga_name="maria")
        assert fakes.sent_embed(ctx.reply).description == (
            "-# The Empty Box and Zeroth Maria\n\nA box."
        )


class TestCharacter:
    async def test_names(self, api: fakes.FakeAPI) -> None:
        api.add(
            r"tenrai\.org/v1/characters",
            found(
                {
                    "name": "Takina Inoue",
                    "name_english": "Inoue Takina",
                    "name_kanji": "井ノ上たきな",
                    "nicknames": ["Takina-chan"],
                    "about": "A Lycoris.",
                }
            ),
        )
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Characters).character, ctx, character="takina")

        embed = fakes.sent_embed(ctx.reply)
        assert embed.title == "Takina Inoue"
        assert embed.description == "-# Inoue Takina • 井ノ上たきな • Takina-chan\nA Lycoris."

    async def test_bare(self, api: fakes.FakeAPI) -> None:
        api.add(r"tenrai", found({"name": "Cirno", "name_english": "Cirno"}))
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Characters).character, ctx, character="cirno")
        assert fakes.sent_embed(ctx.reply).description == "\nNo information available."

    async def test_long_about(self, api: fakes.FakeAPI) -> None:
        api.add(r"tenrai", found({"name": "Klein", "about": "The Fool. " * 200}))
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Characters).character, ctx, character="klein")

        description = fakes.sent_embed(ctx.reply).description or ""
        assert len(description) <= 401
        assert description.endswith("…")

    async def test_not_found(self, api: fakes.FakeAPI) -> None:
        api.add(r"tenrai", {"data": []})
        with pytest.raises(lyerrors.TakinaNotFoundError, match="Character not found"):
            await fakes.call(fakes.make_cog(Characters).character, fakes.make_ctx(), character="x")
