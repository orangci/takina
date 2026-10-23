# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.util.utils import Utils, is_public, resolve_address
from takina.cogs.util.books import Books, format_published
from takina.cogs.util import weather as weather_module
from takina.cogs.util.dictionary import Dictionary
from takina.cogs.util import utils as utils_module
from unittest.mock import AsyncMock, MagicMock
from takina.cogs.util.socials import Socials
from takina.cogs.util.weather import Weather
from takina.cogs.util.avatar import Avatars
from takina.cogs.islam.salah import Salawat
from takina.libs import lyerrors, lyhelpers
from takina.cogs.util.steam import Steam
from takina.cogs.util.time import Time
from takina.cogs.util.info import Info
from typing import Any, ClassVar, Self
from types import SimpleNamespace
from takina import config
from tests import fakes
import datetime
import discord
import pytest
import socket


class TestPublicAddresses:
    @pytest.mark.parametrize("address", ["1.1.1.1", "9.9.9.9", "2606:4700:4700::1111"])
    def test_public(self, address: str) -> None:
        assert is_public(address)

    @pytest.mark.parametrize(
        "address",
        [
            "127.0.0.1",
            "10.0.0.1",
            "172.16.0.1",
            "192.168.1.1",
            "169.254.169.254",
            "100.64.0.1",
            "0.0.0.0",
            "::1",
            "fe80::1%eth0",
            "fd00::1",
            "224.0.0.1",
            "ff02::1",
            "::ffff:127.0.0.1",
        ],
    )
    def test_private(self, address: str) -> None:
        # the bot's own network, its cloud metadata service and friends
        assert not is_public(address)

    async def test_unknown_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fail(*args: Any) -> Any:
            raise socket.gaierror("nope")

        loop = MagicMock()
        loop.getaddrinfo = fail
        monkeypatch.setattr(utils_module.asyncio, "get_running_loop", lambda: loop)
        with pytest.raises(lyerrors.TakinaNotFoundError, match="could not be resolved"):
            await resolve_address("does-not-exist.invalid")


class TestPing:
    @pytest.fixture
    def setup(self, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
        state = SimpleNamespace(address="1.1.1.1", latency=12.7, pinged=[])

        async def resolve(host: str) -> str:
            return state.address

        def ping(address: str, unit: str) -> Any:
            state.pinged.append(address)
            return state.latency

        monkeypatch.setattr(utils_module, "resolve_address", resolve)
        monkeypatch.setattr(utils_module, "dns_ping", ping)
        return state

    async def test_bot_latency(self, setup: SimpleNamespace) -> None:
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Utils, context.bot).ping, context)
        assert "Ping: 42ms" in (fakes.sent_embed(context.reply).description or "")

    async def test_host(self, setup: SimpleNamespace) -> None:
        context = fakes.make_ctx()
        cog = fakes.make_cog(Utils, context.bot)
        await fakes.call(cog.ping, context, "one.one.one.one")
        assert setup.pinged == ["1.1.1.1"]
        assert "one.one.one.one responded with a latency of 12ms" in (
            fakes.sent_embed(context.reply).description or ""
        )

    async def test_private_refused(self, setup: SimpleNamespace) -> None:
        setup.address = "192.168.0.1"
        context = fakes.make_ctx()
        with pytest.raises(lyerrors.TakinaPermissionError, match="public addresses"):
            await fakes.call(fakes.make_cog(Utils, context.bot).ping, context, "router.lan")
        assert setup.pinged == []

    async def test_owner_may_ping_private(self, setup: SimpleNamespace) -> None:
        setup.address = "192.168.0.1"
        owner = fakes.make_user(user_id=961063229168164864)
        bot = fakes.make_bot(owners={owner.id})
        context = fakes.make_ctx(bot=bot, author=owner)
        await fakes.call(fakes.make_cog(Utils, bot).ping, context, "router.lan")
        assert setup.pinged == ["192.168.0.1"]

    @pytest.mark.parametrize("latency", [None, False, 0])
    async def test_timeout(self, setup: SimpleNamespace, latency: Any) -> None:
        setup.latency = latency
        context = fakes.make_ctx()
        with pytest.raises(lyerrors.TakinaError, match="timed out"):
            await fakes.call(fakes.make_cog(Utils, context.bot).ping, context, "slow.example")


class TestUtils:
    async def test_member_count(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(lyhelpers, "fetch_member_count", AsyncMock(return_value=12345))
        guild = fakes.make_guild()
        guild.icon = None
        context = fakes.make_ctx(guild=guild)
        await fakes.call(fakes.make_cog(Utils).member_count, context)
        assert "**12,345** members" in (fakes.sent_embed(context.reply).description or "")

    async def test_version(self) -> None:
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Utils).version, context)
        description = fakes.sent_embed(context.reply).description or ""
        assert f"[**{config.BOT_VERSION}**]({config.CHANGELOG_URL})" in description

    async def test_uptime(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(lyhelpers, "uptime_fetcher", lambda: "1d 2h 3m 4s")
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Utils).uptime, context)
        assert "has been up for 1d 2h 3m 4s" in (fakes.sent_embed(context.reply).description or "")


class TestInfo:
    @pytest.fixture
    def guild(self) -> Any:
        guild = fakes.make_guild(name="Gensokyo")
        guild.owner_id = 961063229168164864
        guild.created_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC)
        guild.verification_level = discord.VerificationLevel.high
        guild.emojis, guild.stickers = [1, 2], [3]
        guild.premium_tier, guild.premium_subscription_count = 2, 14
        guild.description = None
        guild.banner = guild.icon = None
        return guild

    async def test_serverinfo(self, guild: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(lyhelpers, "fetch_member_count", AsyncMock(return_value=1500))
        context = fakes.make_ctx(guild=guild)
        await fakes.call(fakes.make_cog(Info).serverinfo, context)

        description = fakes.sent_embed(context.reply).description or ""
        # owner_id, as the owner is rarely cached without the members intent
        assert "> **Owner**: <@961063229168164864>" in description
        assert "> **Members**: 1,500" in description
        assert "> **Boosts**: Tier 2 — 14 boosts" in description
        assert "> **Emojis**: 2 emojis and 1 stickers" in description

    async def test_serverinfo_description_first(
        self, guild: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(lyhelpers, "fetch_member_count", AsyncMock(return_value=1))
        guild.description = "Where forgotten things go."
        context = fakes.make_ctx(guild=guild)
        await fakes.call(fakes.make_cog(Info).serverinfo, context)
        assert (fakes.sent_embed(context.reply).description or "").startswith(
            "Where forgotten things go.\n\n"
        )

    async def test_userinfo(self, guild: Any) -> None:
        role = fakes.make_role(guild, position=3, name="Shrine Maiden")
        member = fakes.make_member(
            guild,
            name="reimu",
            top_role=role,
            permissions=discord.Permissions(ban_members=True, send_messages=True),
        )
        member.joined_at = datetime.datetime(2021, 5, 5, tzinfo=datetime.UTC)
        bot = fakes.make_bot()
        bot.fetch_user.return_value = SimpleNamespace(banner=None)
        context = fakes.make_ctx(bot=bot, guild=guild, author=member)

        await fakes.call(fakes.make_cog(Info, bot).userinfo, context)

        description = fakes.sent_embed(context.reply).description or ""
        assert "> **Username**: reimu" in description
        assert f"> **Roles (1)**: {role.mention}" in description
        assert "> **Dangerous Permissions**: Ban Members" in description
        assert "Send Messages" not in description
        assert "> **Joined on**: <t:1620172800:D>" in description

    async def test_userinfo_many_roles_fit(self, guild: Any) -> None:
        member = fakes.make_member(guild, permissions=discord.Permissions.all())
        member.roles = [guild.default_role] + [
            fakes.make_role(guild, position=n) for n in range(1, 250)
        ]
        member.timed_out_until = discord.utils.utcnow()
        member.bot = True
        bot = fakes.make_bot()
        bot.fetch_user.return_value = SimpleNamespace(banner=None)
        context = fakes.make_ctx(bot=bot, guild=guild, author=member)
        await fakes.call(fakes.make_cog(Info, bot).userinfo, context)
        embed = fakes.sent_embed(context.reply)
        assert "> **Roles (249)**" in (embed.description or "")
        assert embed.footer.text == "This user is a bot account."

    async def test_roleinfo(self, guild: Any) -> None:
        role = fakes.make_role(
            guild,
            position=3,
            name="Moderator",
            permissions=discord.Permissions(kick_members=True).value,
        )
        guild.roles = [guild.default_role, role, fakes.make_role(guild, position=5)]
        context = fakes.make_ctx(guild=guild)
        await fakes.call(fakes.make_cog(Info).roleinfo, context, role=role)
        description = fakes.sent_embed(context.reply).description or ""
        assert f"> **Role ID**: {role.id}" in description
        assert "> **Permissions**: Kick Members" in description
        assert "> **Position**: 0" in description


class TestAvatars:
    @pytest.fixture
    def setup(self) -> SimpleNamespace:
        guild = fakes.make_guild()
        member = fakes.make_member(guild, name="marisa")
        bot = fakes.make_bot()
        return SimpleNamespace(
            guild=guild, member=member, bot=bot, cog=fakes.make_cog(Avatars, bot)
        )

    async def test_avatar_of_author(self, setup: SimpleNamespace) -> None:
        context = fakes.make_ctx(bot=setup.bot, guild=setup.guild, author=setup.member)
        await fakes.call(setup.cog.avatar, context)
        embed = fakes.sent_embed(context.reply)
        assert embed.title == "marisa's Avatar"
        assert embed.image.url == setup.member.display_avatar.url

    async def test_no_server_avatar(self, setup: SimpleNamespace) -> None:
        context = fakes.make_ctx(bot=setup.bot, guild=setup.guild, author=setup.member)
        with pytest.raises(lyerrors.TakinaError, match="does not have a server avatar set"):
            await fakes.call(setup.cog.server_avatar, context)

    async def test_server_avatar_of_user_object(self, setup: SimpleNamespace) -> None:
        with pytest.raises(lyerrors.TakinaError, match="server avatar"):
            await setup.cog.fetch_user_image(
                fakes.make_ctx(bot=setup.bot), fakes.make_user(), "guild_avatar"
            )

    async def test_banner_is_fetched(self, setup: SimpleNamespace) -> None:
        setup.bot.fetch_user.return_value = SimpleNamespace(
            banner=SimpleNamespace(url="https://cdn/banner.png")
        )
        context = fakes.make_ctx(bot=setup.bot, guild=setup.guild, author=setup.member)
        await fakes.call(setup.cog.banner, context)
        setup.bot.fetch_user.assert_awaited_once_with(setup.member.id)
        assert fakes.sent_embed(context.reply).image.url == "https://cdn/banner.png"

    async def test_server_banner_left_server(self, setup: SimpleNamespace) -> None:
        setup.guild.fetch_member.side_effect = discord.NotFound(MagicMock(status=404), "gone")
        context = fakes.make_ctx(bot=setup.bot, guild=setup.guild, author=setup.member)
        with pytest.raises(lyerrors.TakinaNotFoundError, match="not in this server"):
            await fakes.call(setup.cog.server_banner, context)


class TestSocials:
    GITHUB_USER: ClassVar[dict[str, Any]] = {
        "login": "orangci",
        "html_url": "https://github.com/orangci",
        "bio": "Writes Takina.",
        "blog": "orangc.net",
        "email": None,
        "location": "Gensokyo",
        "hireable": None,
        "company": None,
        "followers": 50,
        "following": 0,
        "created_at": "2020-01-01T00:00:00Z",
        "public_repos": 30,
        "public_gists": 0,
        "type": "User",
        "site_admin": False,
        "avatar_url": "https://avatars.githubusercontent.com/u/1",
        "id": 1,
    }

    async def test_github(self, api: fakes.FakeAPI) -> None:
        api.add(r"api\.github\.com/users/orangci$", self.GITHUB_USER)
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Socials).github, context, username="@orangci")

        description = fakes.sent_embed(context.reply).description or ""
        # a bare domain would not render as a link
        assert "> **Website**: [orangc.net](https://orangc.net)" in description
        assert "> **Followers**: 50" in description
        assert "Following" not in description
        assert "not a regular GitHub user" not in description
        assert api.calls[0][1]["not_found"] == "That GitHub account does not exist."

    async def test_github_quotes_username(self, api: fakes.FakeAPI) -> None:
        api.add(r"github", lyerrors.TakinaNotFoundError("That GitHub account does not exist."))
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(fakes.make_cog(Socials).github, fakes.make_ctx(), username="../orgs/x")
        assert api.urls() == ["https://api.github.com/users/..%2Forgs%2Fx"]

    async def test_github_organisation(self, api: fakes.FakeAPI) -> None:
        api.add(
            r"github",
            self.GITHUB_USER
            | {"type": "Organization", "blog": "https://takina.is-a.bot", "site_admin": True},
        )
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Socials).github, context, username="takina")
        description = fakes.sent_embed(context.reply).description or ""
        assert "[takina.is-a.bot](https://takina.is-a.bot)" in description
        assert "not a regular GitHub user" in description
        assert "site administrator" in description

    async def test_codeberg(self, api: fakes.FakeAPI) -> None:
        api.add(
            r"codeberg\.org/api/v1/users/orangc$",
            {
                "username": "orangc",
                "html_url": "https://codeberg.org/orangc",
                "id": 7,
                "followers_count": 3,
                "created": "2023-02-03T00:00:00Z",
            },
        )
        api.add(r"/repos$", ([], {"X-Total-Count": "1234"}))
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Socials).codeberg, context, username="orangc")

        context.defer.assert_awaited_once()
        description = fakes.sent_embed(context.reply).description or ""
        assert "> **Public Repositories**: 1,234" in description
        assert api.calls[1][1]["params"] == {"limit": 1}

    async def test_codeberg_error_body(self, api: fakes.FakeAPI) -> None:
        api.add(r"codeberg", {"message": "user does not exist"})
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(fakes.make_cog(Socials).codeberg, fakes.make_ctx(), username="ghost")


class TestBooks:
    @pytest.mark.parametrize(
        ("published", "shown"),
        [
            ("2008", "2008"),
            ("2008-05", "May 2008"),
            ("2008-05-14", "<t:1210723200:D>"),
            ("2008-13", "2008-13"),
            ("2008-02-30", "2008-02-30"),
            ("someday", "someday"),
        ],
    )
    def test_format_published(self, published: str, shown: str) -> None:
        assert format_published(published) == shown

    async def test_by_title(self, api: fakes.FakeAPI) -> None:
        api.add(
            r"googleapis",
            {
                "items": [
                    {
                        "volumeInfo": {
                            "title": "Yumi and the Nightmare Painter",
                            "authors": ["Brandon Sanderson"],
                            "publishedDate": "2023-07",
                            "description": "<p>A <b>painter</b> &amp; a ghost</p>" + "x" * 1000,
                            "industryIdentifiers": [
                                {"type": "ISBN_10", "identifier": "1"},
                                {"type": "ISBN_13", "identifier": "978"},
                            ],
                        }
                    }
                ]
            },
        )
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Books).book, context, book="Yumi")

        embed = fakes.sent_embed(context.reply)
        description = embed.description or ""
        assert "> **Authors**: Brandon Sanderson" in description
        assert "> **Published**: July 2023" in description
        assert "A painter & a ghost" in description and "<b>" not in description
        assert embed.footer.text == "ISBN: 978"
        assert api.calls[0][1]["params"]["q"] == "intitle:Yumi"
        assert api.calls[0][1]["params"]["key"] == config.GOOGLE_API_KEY

    async def test_falls_back_to_isbn(self, api: fakes.FakeAPI) -> None:
        def answer(url: str, kwargs: dict) -> Any:
            if kwargs["params"]["q"].startswith("isbn:"):
                return {"items": [{"volumeInfo": {"title": "Found by ISBN"}}]}
            return {"totalItems": 0}

        api.add(r"googleapis", answer)
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Books).book, context, book="9780765383181")
        assert fakes.sent_embed(context.reply).title == "Found by ISBN"

    async def test_not_found(self, api: fakes.FakeAPI) -> None:
        api.add(r"googleapis", {"totalItems": 0})
        with pytest.raises(lyerrors.TakinaNotFoundError, match="does not exist in the database"):
            await fakes.call(fakes.make_cog(Books).book, fakes.make_ctx(), book="Necronomicon")


class TestDictionary:
    async def test_define(self, api: fakes.FakeAPI) -> None:
        api.add(
            r"dictionaryapi",
            [
                {
                    "word": "grass",
                    "phonetic": "/ɡɹɑːs/",
                    "meanings": [
                        {
                            "partOfSpeech": "noun",
                            "definitions": [
                                {"definition": f"sense {n}", "example": "touch grass"}
                                for n in range(1, 6)
                            ],
                        },
                        {"partOfSpeech": "verb", "definitions": []},
                    ],
                }
            ],
        )
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Dictionary).define, context, word="grass")

        embed = fakes.sent_embed(context.reply)
        description = embed.description or ""
        assert description.startswith("*/ɡɹɑːs/*")
        assert "3. sense 3" in description and "4. sense 4" not in description
        assert '"*touch grass*"' in description
        assert "Verb" not in description
        assert api.urls() == ["https://api.dictionaryapi.dev/api/v2/entries/en/grass"]

    async def test_define_huge_entry_fits(self, api: fakes.FakeAPI) -> None:
        meanings = [
            {
                "partOfSpeech": f"pos{n}",
                "definitions": [{"definition": "d" * 500, "example": "e" * 500}] * 3,
            }
            for n in range(10)
        ]
        api.add(r"dictionaryapi", [{"word": "w" * 300, "meanings": meanings}])
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Dictionary).define, context, word="w")
        fakes.sent_embed(context.reply)

    async def test_define_quotes_word(self, api: fakes.FakeAPI) -> None:
        api.add(r"dictionaryapi", lyerrors.TakinaNotFoundError("No definition found."))
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(fakes.make_cog(Dictionary).define, fakes.make_ctx(), word="a/b c")
        assert api.urls()[0].endswith("/a%2Fb%20c")

    async def test_define_no_meanings(self, api: fakes.FakeAPI) -> None:
        api.add(r"dictionaryapi", [{"word": "x", "meanings": []}])
        with pytest.raises(lyerrors.TakinaError, match="No definition"):
            await fakes.call(fakes.make_cog(Dictionary).define, fakes.make_ctx(), word="x")

    async def test_urban(self, api: fakes.FakeAPI) -> None:
        api.add(
            r"urbandictionary",
            {
                "list": [
                    {
                        "word": "anime",
                        "definition": "Japanese [animation]",
                        "example": "I watch [anime]",
                        "permalink": "https://www.urbandictionary.com/define.php?term=anime",
                        "thumbs_up": 1234,
                        "thumbs_down": 5,
                    }
                ]
            },
        )
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Dictionary).ubdict, context, word="anime")
        embed = fakes.sent_embed(context.reply)
        assert (
            embed.description
            == "Japanese [animation](https://www.urbandictionary.com/define.php?term=animation)"
        )
        assert embed.footer.text is not None and embed.footer.text.startswith("👍 1,234 | 👎 5")

    async def test_urban_many_links_fall_back_to_text(self, api: fakes.FakeAPI) -> None:
        brackets = " ".join("[a]" for _ in range(75))
        api.add(
            r"urbandictionary",
            {
                "list": [
                    {
                        "word": "w",
                        "definition": brackets,
                        "example": brackets,
                        "permalink": "https://u",
                        "thumbs_up": 0,
                        "thumbs_down": 0,
                    }
                ]
            },
        )
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Dictionary).ubdict, context, word="w")
        embed = fakes.sent_embed(context.reply)
        # linked, the example would outgrow its field, so it loses the brackets instead
        assert "[" not in (embed.fields[0].value or "")

    async def test_urban_nothing(self, api: fakes.FakeAPI) -> None:
        api.add(r"urbandictionary", {"list": []})
        with pytest.raises(lyerrors.TakinaError, match="No results"):
            await fakes.call(fakes.make_cog(Dictionary).ubdict, fakes.make_ctx(), word="zzz")


class TestSteam:
    async def test_game(self, api: fakes.FakeAPI) -> None:
        api.add(r"storesearch", {"items": [{"id": 1332010}]})
        api.add(
            r"appdetails",
            {
                "1332010": {
                    "success": True,
                    "data": {
                        "name": "Stray",
                        "is_free": False,
                        "price_overview": {"final_formatted": "$29.99"},
                        "platforms": {"windows": True, "mac": True, "linux": False},
                        "genres": [{"description": "Adventure"}],
                        "short_description": "Lost, alone &amp; separated<br>from family",
                    },
                }
            },
        )
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Steam).steam, context, game="Stray")

        embed = fakes.sent_embed(context.reply)
        description = embed.description or ""
        assert embed.url == "https://store.steampowered.com/app/1332010"
        assert "> **Price**: $29.99" in description
        assert "> **Platforms**: Windows, Mac" in description
        assert "Lost, alone & separated\nfrom family" in description
        assert api.calls[0][1]["params"]["cc"] == config.STEAM_REGION

    async def test_free(self, api: fakes.FakeAPI) -> None:
        api.add(r"storesearch", {"items": [{"id": 1}]})
        api.add(r"appdetails", {"1": {"success": True, "data": {"name": "Free", "is_free": True}}})
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Steam).steam, context, game="x")
        assert "> **Price**: Free" in (fakes.sent_embed(context.reply).description or "")

    async def test_not_found(self, api: fakes.FakeAPI) -> None:
        api.add(r"storesearch", {"items": []})
        with pytest.raises(lyerrors.TakinaNotFoundError, match="Game not found"):
            await fakes.call(fakes.make_cog(Steam).steam, fakes.make_ctx(), game="x")

    async def test_delisted(self, api: fakes.FakeAPI) -> None:
        api.add(r"storesearch", {"items": [{"id": 1}]})
        api.add(r"appdetails", {"1": {"success": False}})
        with pytest.raises(lyerrors.TakinaNotFoundError, match="store page is not available"):
            await fakes.call(fakes.make_cog(Steam).steam, fakes.make_ctx(), game="x")


class TestLocations:
    @pytest.fixture
    def located(self, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
        location = SimpleNamespace(latitude=24.71, longitude=46.68, address="Riyadh, Saudi Arabia")
        monkeypatch.setattr(lyhelpers, "geocode", AsyncMock(return_value=location))
        return location

    async def test_time(self, located: SimpleNamespace) -> None:
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Time).time, context, location="Riyadh")
        assert "The current time in Asia/Riyadh is" in (
            fakes.sent_embed(context.reply).description or ""
        )

    async def test_time_unknown_place(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(lyhelpers, "geocode", AsyncMock(return_value=None))
        with pytest.raises(lyerrors.TakinaNotFoundError, match="not recognized"):
            await fakes.call(fakes.make_cog(Time).time, fakes.make_ctx(), location="Gensokyo")

    async def test_weather(self, located: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
        forecast = SimpleNamespace(
            elevation=612.0,
            current_weather=SimpleNamespace(
                temperature=40.0, weather_code=0, wind_speed=12.5, wind_direction=270
            ),
        )

        class FakeOpenMeteo:
            async def __aenter__(self) -> Self:
                return self

            async def __aexit__(self, *args: object) -> None:
                return None

            async def forecast(self, **kwargs: Any) -> Any:
                assert (kwargs["latitude"], kwargs["longitude"]) == (24.71, 46.68)
                return forecast

        monkeypatch.setattr(weather_module, "OpenMeteo", FakeOpenMeteo)
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Weather).weather, context, location="Riyadh")

        description = fakes.sent_embed(context.reply).description or ""
        assert "**Riyadh, Saudi Arabia**" in description
        assert "> **Conditions**: Clear sky" in description
        assert "40.0°C / 104.0°F" in description
        assert "> **Elevation**: 612 metres" in description

        forecast.current_weather.weather_code = 1000
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Weather).weather, context, location="Riyadh")
        assert "Unknown (code 1000)" in (fakes.sent_embed(context.reply).description or "")

    async def test_salawat(self, api: fakes.FakeAPI) -> None:
        api.add(
            r"aladhan",
            {
                "data": {
                    "timings": {
                        "Fajr": "04:30",
                        "Dhuhr": "11:50",
                        "Asr": "15:10",
                        "Maghrib": "17:30",
                        "Isha": "19:00",
                    },
                    "meta": {"timezone": "Asia/Riyadh"},
                }
            },
        )
        context = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Salawat).salawat, context, location_name="riyadh")

        embed = fakes.sent_embed(context.reply)
        assert embed.title == "Islāmic Prayer Times for Riyadh"
        assert "> **Fajr**: 04:30" in (embed.description or "")
        assert embed.footer.text == "Times are in Asia/Riyadh, the timezone of that location."

    async def test_salawat_error(self, api: fakes.FakeAPI) -> None:
        # errors come back with a message where the timings would be
        api.add(r"aladhan", {"code": 400, "data": "Unable to geocode address."})
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(
                fakes.make_cog(Salawat).salawat, fakes.make_ctx(), location_name="nowhere"
            )
