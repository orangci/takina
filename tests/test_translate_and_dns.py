# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.util import translate as translate_module
from takina.cogs.util.dns import DNS, MAX_LOOKUPS
from takina.cogs.util.translate import Translate
from unittest.mock import AsyncMock, MagicMock
from dns import name, resolver, exception
from takina.libs import lyerrors, lyviews
from whodap.errors import WhodapError
from typing import Any, Self, cast
from types import SimpleNamespace
from takina import config
from tests import fakes
import datetime
import whodap
import pytest

LANGUAGES = [
    {"code": "en"},
    {"code": "ar"},
    {"code": "zh-Hans"},
    {"code": "zh-Hant"},
    {"code": "pt-BR"},
    {"code": "pt"},
]


@pytest.fixture
def translate(api: fakes.FakeAPI) -> SimpleNamespace:
    api.add(r"/languages$", LANGUAGES)
    api.add(r"/translate$", {"translatedText": "السلام عليكم"})
    return SimpleNamespace(api=api, cog=fakes.make_cog(Translate))


class TestTranslateLanguages:
    @pytest.mark.parametrize(
        ("lang", "pair"),
        [
            ("ar", ("auto", "ar")),
            ("AR", ("auto", "ar")),
            ("en-ar", ("en", "ar")),
            ("EN-AR", ("en", "ar")),
            ("zh-hans", ("auto", "zh-Hans")),
            ("en-zh-Hans", ("en", "zh-Hans")),
            ("zh-Hant-en", ("zh-Hant", "en")),
            ("pt-br", ("auto", "pt-BR")),
            ("pt-BR-zh-Hans", ("pt-BR", "zh-Hans")),
            ("pt-en", ("pt", "en")),
        ],
    )
    async def test_parses(
        self, translate: SimpleNamespace, lang: str, pair: tuple[str, str]
    ) -> None:
        assert await translate.cog.parse_languages(lang) == pair

    @pytest.mark.parametrize("lang", ["xx", "en-xx", "-en", "en-", "english", "`" * 80])
    async def test_unknown(self, translate: SimpleNamespace, lang: str) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError, match="Unknown language") as error:
            await translate.cog.parse_languages(lang)
        # backticks are dropped and the echo is cut, so the code span cannot break
        echoed = error.value.message.removeprefix("Unknown language: `").split("`. Use")[0]
        assert "`" not in echoed
        assert len(error.value.message) < 300

    async def test_languages_fetched_once(self, translate: SimpleNamespace) -> None:
        await translate.cog.parse_languages("ar")
        await translate.cog.parse_languages("en-ar")
        assert translate.api.urls().count(f"{config.LIBRETRANSLATE_API_URL}/languages") == 1


class TestTranslateCommand:
    async def test_translates(self, translate: SimpleNamespace) -> None:
        context = fakes.make_ctx()
        await fakes.call(translate.cog.translate, context, "en-ar", text="peace be upon you")

        context.defer.assert_awaited_once()
        url, kwargs = translate.api.calls[-1]
        assert url == f"{config.LIBRETRANSLATE_API_URL}/translate"
        assert kwargs["method"] == "POST"
        assert kwargs["json"]["q"] == "peace be upon you"
        assert (kwargs["json"]["source"], kwargs["json"]["target"]) == ("en", "ar")
        description = fakes.sent_embed(context.reply).description or ""
        assert "> **Original**: peace be upon you" in description
        assert "> **Translation**: السلام عليكم" in description

    async def test_service_error(self, translate: SimpleNamespace) -> None:
        translate.api.add(r"/translate$", {"error": "Rate limited"})
        with pytest.raises(lyerrors.TakinaError, match="Translation failed: Rate limited."):
            await fakes.call(translate.cog.translate, fakes.make_ctx(), "ar", text="hello")

    async def test_empty_answer(self, translate: SimpleNamespace) -> None:
        translate.api.add(r"/translate$", {})
        with pytest.raises(lyerrors.TakinaError, match="Translation failed."):
            await fakes.call(translate.cog.translate, fakes.make_ctx(), "ar", text="hello")

    async def test_long_translation_fits(self, translate: SimpleNamespace) -> None:
        translate.api.add(r"/translate$", {"translatedText": "ل" * 5000})
        context = fakes.make_ctx()
        await fakes.call(translate.cog.translate, context, "ar", text="x" * 2000)
        fakes.sent_embed(context.reply)

    async def test_setup_needs_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(config, "LIBRETRANSLATE_API_URL", None)
        with pytest.raises(lyerrors.TakinaMissingEnvironmentVariableError):
            await translate_module.setup(fakes.make_bot())


class FakeRDAP:
    """whodap's client, answering only for the names in `known`."""

    def __init__(self, known: dict[tuple[str, str], Any]) -> None:
        self.known = known
        self.lookups: list[tuple[str, str]] = []

    def __call__(self) -> "FakeRDAP":
        return self

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def aio_lookup(self, domain: str, tld: str) -> Any:
        self.lookups.append((domain, tld))
        if (domain, tld) in self.known:
            return self.known[(domain, tld)]
        raise WhodapError("no such domain")


def domain_response(data: dict[str, Any]) -> Any:
    response = MagicMock(spec=whodap.DomainResponse)
    response.to_whois_dict.return_value = data
    return response


@pytest.fixture
def rdap(monkeypatch: pytest.MonkeyPatch) -> FakeRDAP:
    fake = FakeRDAP({})
    monkeypatch.setattr(whodap.DNSClient, "new_aio_client_context", fake)
    return fake


class TestWhois:
    async def test_registered_name(self, rdap: FakeRDAP) -> None:
        rdap.known[("orangc", "net")] = domain_response(
            {
                "domain_name": "orangc.net",
                "created_date": datetime.datetime(2020, 1, 2, tzinfo=datetime.UTC),
                "nameservers": ["a.ns", "b.ns"],
                "registrant_name": None,
            }
        )
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(DNS).whois, context, "OrangC.net")

        embed = fakes.sent_embed(context.reply)
        description = embed.description or ""
        assert embed.title == "WHOIS Information for OrangC.net"
        assert "> **Domain Name**: orangc.net" in description
        assert "> **Created Date**: <t:1577923200:D>" in description
        assert "> **Nameservers**: a.ns, b.ns" in description
        assert "Registrant" not in description
        assert "icann.org/wicf" in description

    async def test_subdomain_falls_back(self, rdap: FakeRDAP) -> None:
        rdap.known[("example", "com")] = domain_response({"domain_name": "example.com"})
        cog = fakes.make_cog(DNS)
        assert await cog.resolve_domain("www.shop.example.com") is rdap.known[("example", "com")]
        assert rdap.lookups[-3:] == [
            ("www.shop.example", "com"),
            ("shop.example", "com"),
            ("example", "com"),
        ]

    async def test_second_level_registries(self, rdap: FakeRDAP) -> None:
        rdap.known[("example.co", "uk")] = domain_response({})
        cog = fakes.make_cog(DNS)
        assert await cog.resolve_domain("example.co.uk") is rdap.known[("example.co", "uk")]
        assert rdap.lookups[0] == ("example.co", "uk")

    async def test_lookups_bounded(self, rdap: FakeRDAP) -> None:
        cog = fakes.make_cog(DNS)
        assert await cog.resolve_domain(".".join(["a"] * 120) + ".com") is None
        assert len(rdap.lookups) == MAX_LOOKUPS

    async def test_bare_word(self, rdap: FakeRDAP) -> None:
        assert await fakes.make_cog(DNS).resolve_domain("localhost") is None
        assert rdap.lookups == []

    async def test_unknown(self, rdap: FakeRDAP) -> None:
        with pytest.raises(lyerrors.TakinaNotFoundError, match="doesn't appear to exist"):
            await fakes.call(fakes.make_cog(DNS).whois, fakes.make_ctx(), "nothing.example")

    async def test_unsupported_tld(self, rdap: FakeRDAP, monkeypatch: pytest.MonkeyPatch) -> None:
        async def unsupported(domain: str, tld: str) -> Any:
            raise NotImplementedError

        monkeypatch.setattr(rdap, "aio_lookup", unsupported)
        with pytest.raises(lyerrors.TakinaNotFoundError, match="not supported"):
            await fakes.call(fakes.make_cog(DNS).whois, fakes.make_ctx(), "reimu.hakurei")

    async def test_long_name_and_data_fit(self, rdap: FakeRDAP) -> None:
        long_domain = ("a" * 60 + ".") * 4 + "com"
        rdap.known[("a" * 60, "com")] = domain_response(
            {f"field_{n}": "x" * 200 for n in range(40)}
        )
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(DNS).whois, context, long_domain)
        fakes.sent_embed(context.reply)

    def test_input_capped(self) -> None:
        assert DNS.whois.clean_params["domain"].annotation.max == 253


def answers(*records: str) -> list[str]:
    return list(records)


def paginated() -> AsyncMock:
    # patched over by the cog fixture below
    return cast(AsyncMock, lyviews.PaginatorView.send)


class TestDig:
    @pytest.fixture
    def cog(self, monkeypatch: pytest.MonkeyPatch) -> DNS:
        cog = fakes.make_cog(DNS)
        monkeypatch.setattr(lyviews.PaginatorView, "send", AsyncMock())
        return cog

    def records(self, cog: DNS, table: dict[str, Any]) -> AsyncMock:
        async def resolve(url: str, record_type: str) -> Any:
            value = table.get(record_type, resolver.NoAnswer())
            if isinstance(value, BaseException):
                raise value
            return value

        mock = AsyncMock(side_effect=resolve)
        cast(Any, cog._resolver).resolve = mock
        return mock

    def test_public_resolvers(self) -> None:
        cog = fakes.make_cog(DNS)
        assert cog._resolver.nameservers == ["1.1.1.1", "9.9.9.9"]

    async def test_records(self, cog: DNS) -> None:
        resolve = self.records(cog, {"A": answers("1.2.3.4"), "TXT": answers('"v=spf1 `rm -rf`"')})
        await fakes.call(cog.dig, fakes.make_ctx(), "https://orangc.net/blog/post")

        assert {call.args[0] for call in resolve.await_args_list} == {"orangc.net"}
        (embeds,) = [call.args[1] for call in paginated().await_args_list]
        description = embeds[0].description or ""
        assert "**A Records**\n```1.2.3.4```" in description
        # a backtick in a record must not close the code block early
        assert "`\u200brm -rf`\u200b" in description

    async def test_pages_of_three(self, cog: DNS) -> None:
        self.records(cog, {kind: answers("x") for kind in ("A", "CNAME", "AAAA", "MX", "TXT")})
        await fakes.call(cog.dig, fakes.make_ctx(), "orangc.net")
        embeds = paginated().await_args_list[-1].args[1]
        assert len(embeds) == 2

    async def test_nothing(self, cog: DNS) -> None:
        self.records(cog, {})
        with pytest.raises(lyerrors.TakinaNotFoundError, match="No DNS records"):
            await fakes.call(cog.dig, fakes.make_ctx(), "orangc.net")

    @pytest.mark.parametrize(
        ("error", "kind", "message"),
        [
            (resolver.NXDOMAIN(), lyerrors.TakinaNotFoundError, "does not exist"),
            (name.LabelTooLong(), lyerrors.TakinaUserInputError, "not a valid domain"),
            (name.EmptyLabel(), lyerrors.TakinaUserInputError, "not a valid domain"),
            (exception.Timeout(), lyerrors.TakinaError, "timed out"),
        ],
    )
    async def test_errors(
        self, cog: DNS, error: Exception, kind: type[Exception], message: str
    ) -> None:
        self.records(cog, {"A": error})
        with pytest.raises(kind, match=message):
            await fakes.call(cog.dig, fakes.make_ctx(), "orangc.net")

    async def test_no_nameservers_skips(self, cog: DNS) -> None:
        self.records(cog, {"A": resolver.NoNameservers(), "MX": answers("10 mail.orangc.net.")})
        await fakes.call(cog.dig, fakes.make_ctx(), "orangc.net")
        assert "MX Records" in (paginated().await_args_list[-1].args[1][0].description or "")

    async def test_huge_records_fit(self, cog: DNS) -> None:
        self.records(cog, {kind: answers(*["x" * 255] * 20) for kind in ("A", "TXT", "MX")})
        await fakes.call(cog.dig, fakes.make_ctx(), "a" * 250 + ".com")
        for embed in paginated().await_args_list[-1].args[1]:
            fakes.assert_embed_fits(embed)
