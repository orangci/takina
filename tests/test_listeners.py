# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.listeners.ping_response import ORANGC_ID, PingResponse
from takina.cogs.sesp.awcc.hof import AWCC_HOF
from takina.cogs.listeners.quran import Quran
from takina.libs import lyerrors, lyhelpers
from unittest.mock import AsyncMock
from types import SimpleNamespace
from discord.ext import commands
from typing import Any, ClassVar
from takina import config
from tests import fakes
import datetime
import aiohttp
import pytest

AWCC_GUILD_ID = 275341388554698753


@pytest.fixture
def started_bot(monkeypatch: pytest.MonkeyPatch) -> fakes.MagicMock:
    """A bot that lyhelpers knows about, up for a day and an hour."""
    bot = fakes.make_bot()
    bot.start_time = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1, hours=1)
    bot.get_prefix = AsyncMock(return_value=[".", "takina "])
    monkeypatch.setattr(lyhelpers, "_bot", bot)
    return bot


def mention_message(bot: Any, content: str | None = None, **overrides: Any) -> fakes.MagicMock:
    guild = fakes.make_guild()
    guild.me = fakes.make_member(guild, name="takina", bot=True, user_id=bot.user.id)
    guild.me.mention = f"<@{bot.user.id}>"
    message = fakes.make_message(
        author=fakes.make_member(guild),
        channel=fakes.make_channel(guild),
        guild=guild,
        content=guild.me.mention if content is None else content,
    )
    bot.user.mentioned_in.return_value = True
    for name, value in overrides.items():
        setattr(message, name, value)
    return message


class TestRepoData:
    async def test_counts(self, api: fakes.FakeAPI) -> None:
        api.add(
            r"api\.github\.com/repos/orangci/takina$", {"stargazers_count": 99, "forks_count": 9}
        )
        cog = PingResponse(fakes.make_bot())
        await cog.fetch_repo_data.coro(cog)
        assert (cog.stars, cog.forks) == (99, 9)

    async def test_empty_keeps_counts(self, api: fakes.FakeAPI) -> None:
        api.add(r"github", None)
        cog = PingResponse(fakes.make_bot())
        cog.stars = 5
        await cog.fetch_repo_data.coro(cog)
        assert cog.stars == 5

    @pytest.mark.parametrize(
        "error",
        [lyerrors.TakinaError("rate limited"), aiohttp.ClientConnectionError(), TimeoutError()],
    )
    async def test_failure_is_quiet(self, api: fakes.FakeAPI, error: Exception) -> None:
        # the loop would stop for good if this raised
        api.add(r"github", error)
        cog = PingResponse(fakes.make_bot())
        cog.stars = 5
        await cog.fetch_repo_data.coro(cog)
        assert cog.stars == 5

    async def test_missing_keys(self, api: fakes.FakeAPI) -> None:
        api.add(r"github", {"message": "Moved Permanently"})
        cog = PingResponse(fakes.make_bot())
        await cog.fetch_repo_data.coro(cog)
        assert (cog.stars, cog.forks) == (0, 0)


class TestAuthor:
    async def test_cached_user(self) -> None:
        bot = fakes.make_bot()
        orangc = fakes.make_user(name="orangc", user_id=ORANGC_ID)
        bot.get_user.return_value = orangc
        assert await PingResponse(bot).author() is orangc
        bot.fetch_user.assert_not_awaited()

    async def test_fetches_once(self) -> None:
        bot = fakes.make_bot()
        orangc = fakes.make_user(name="orangc", user_id=ORANGC_ID)
        bot.fetch_user.return_value = orangc
        cog = PingResponse(bot)

        assert await cog.author() is orangc
        assert await cog.author() is orangc
        bot.fetch_user.assert_awaited_once_with(ORANGC_ID)


class TestInfoEmbed:
    async def test_contents(self, started_bot: fakes.MagicMock) -> None:
        started_bot.guilds = [object()] * 1234
        started_bot.fetch_user.return_value = fakes.make_user(name="orangc")
        cog = PingResponse(started_bot)
        cog.stars = 4321

        message = mention_message(started_bot)
        embed = await cog.construct_info_embed(message)

        fakes.assert_embed_fits(embed)
        description = embed.description or ""
        assert "> **Prefix**: `.`, `takina `" in description
        assert "> **Guilds**: Takina is in 1,234 servers" in description
        assert "[4,321](https://github.com/orangci/takina/stargazers)" in description
        assert "> **Uptime**: 1d 1h 0m" in description
        assert f"> **Version**: [{config.BOT_VERSION}]({config.CHANGELOG_URL})" in description
        assert embed.author.name == "orangc"
        # no avatar of their own, so the fallback leaf
        assert embed.author.icon_url == "https://orangc.net/leaf.png"
        started_bot.get_prefix.assert_awaited_once_with(message)

    async def test_one_server(self, started_bot: fakes.MagicMock) -> None:
        started_bot.guilds = [object()]
        started_bot.fetch_user.return_value = fakes.make_user(name="orangc")
        embed = await PingResponse(started_bot).construct_info_embed(mention_message(started_bot))
        assert "Takina is in 1 server\n" in (embed.description or "")

    async def test_avatar(self, started_bot: fakes.MagicMock) -> None:
        orangc = fakes.make_user(name="orangc")
        orangc.avatar = SimpleNamespace(url="https://cdn.discordapp.com/avatars/orangc.png")
        started_bot.fetch_user.return_value = orangc
        embed = await PingResponse(started_bot).construct_info_embed(mention_message(started_bot))
        assert embed.author.icon_url == "https://cdn.discordapp.com/avatars/orangc.png"


class TestPingListener:
    @pytest.fixture
    def cog(self, started_bot: fakes.MagicMock) -> PingResponse:
        started_bot.fetch_user.return_value = fakes.make_user(name="orangc")
        return PingResponse(started_bot)

    async def test_bare_mention(self, cog: PingResponse, started_bot: fakes.MagicMock) -> None:
        message = mention_message(started_bot, content=f"  <@{started_bot.user.id}>  ")
        await cog.on_message(message)
        assert fakes.sent(message.reply)["mention_author"] is False
        fakes.sent_embed(message.reply)

    async def test_mention_with_text(self, cog: PingResponse, started_bot: fakes.MagicMock) -> None:
        # a mention in passing is a conversation, not a summons
        message = mention_message(started_bot, content=f"<@{started_bot.user.id}> hello")
        await cog.on_message(message)
        message.reply.assert_not_awaited()

    async def test_bots_ignored(self, cog: PingResponse, started_bot: fakes.MagicMock) -> None:
        message = mention_message(started_bot)
        message.author.bot = True
        await cog.on_message(message)
        message.reply.assert_not_awaited()

    async def test_not_mentioned(self, cog: PingResponse, started_bot: fakes.MagicMock) -> None:
        message = mention_message(started_bot)
        started_bot.user.mentioned_in.return_value = False
        await cog.on_message(message)
        message.reply.assert_not_awaited()

    async def test_dms_ignored(self, cog: PingResponse, started_bot: fakes.MagicMock) -> None:
        message = mention_message(started_bot, guild=None)
        await cog.on_message(message)
        message.reply.assert_not_awaited()

    async def test_before_login(self, cog: PingResponse, started_bot: fakes.MagicMock) -> None:
        message = mention_message(started_bot)
        started_bot.user = None
        await cog.on_message(message)
        message.reply.assert_not_awaited()

    async def test_info_command(self, cog: PingResponse, started_bot: fakes.MagicMock) -> None:
        guild = fakes.make_guild()
        ctx = fakes.make_ctx(bot=started_bot, guild=guild)
        await fakes.call(fakes.make_cog(PingResponse, started_bot).info, ctx)
        fakes.sent_embed(ctx.reply)

    async def test_info_needs_guild(self, started_bot: fakes.MagicMock) -> None:
        ctx = fakes.make_ctx(bot=started_bot)
        with pytest.raises(commands.CheckFailure):
            await fakes.run_checks(fakes.make_cog(PingResponse, started_bot).info, ctx)


AYAH: dict[str, Any] = {
    "data": {
        "text": "In the Name of Allah, the Most Beneficent, the Most Merciful.",
        "surah": {"englishName": "Al-Faatiha", "englishNameTranslation": "The Opening"},
    }
}


class TestQuranRegex:
    @pytest.mark.parametrize(
        ("content", "reference"),
        [
            ("quran 1:1", ("1", "1")),
            ("Qur'an 2:255", ("2", "255")),
            ("as the Koran (112:1) says", ("112", "1")),
            ("CORAN 3:7", ("3", "7")),
            ("quran(18:10)", ("18", "10")),
        ],
    )
    def test_matches(self, content: str, reference: tuple[str, str]) -> None:
        match = Quran(fakes.make_bot()).QURAN_REGEX.search(content)
        assert match is not None
        assert match.groups() == reference

    @pytest.mark.parametrize(
        "content",
        ["1:1", "quran", "the quranic 1:1", "quran 1234:1", "quran one:two", "xquran 1:1"],
    )
    def test_ignores(self, content: str) -> None:
        assert Quran(fakes.make_bot()).QURAN_REGEX.search(content) is None


class TestQuranListener:
    def message(self, content: str, *, bot: bool = False) -> fakes.MagicMock:
        return fakes.make_message(
            author=fakes.make_user(bot=bot), channel=fakes.make_channel(), content=content
        )

    async def test_replies(self, api: fakes.FakeAPI) -> None:
        api.add(r"api\.alquran\.cloud/v1/ayah/1:1/en\.hilali$", AYAH)
        message = self.message("what does quran 1:1 say?")
        await Quran(fakes.make_bot()).on_message(message)

        embed = fakes.sent_embed(message.reply)
        assert embed.title == "The Holy Qur'ān, Āyah 1 of Surah Al-Faatiha (The Opening)"
        assert embed.description == AYAH["data"]["text"]
        assert embed.footer.text == "English translation by Hilali & Khan"
        assert fakes.sent(message.reply)["mention_author"] is False

    @pytest.mark.parametrize("reference", ["0:1", "115:1", "1:0", "999:999"])
    async def test_out_of_range(self, api: fakes.FakeAPI, reference: str) -> None:
        message = self.message(f"quran {reference}")
        await Quran(fakes.make_bot()).on_message(message)
        assert api.calls == []
        message.reply.assert_not_awaited()

    async def test_bots_ignored(self, api: fakes.FakeAPI) -> None:
        message = self.message("quran 1:1", bot=True)
        await Quran(fakes.make_bot()).on_message(message)
        assert api.calls == []

    async def test_no_reference(self, api: fakes.FakeAPI) -> None:
        message = self.message("reimu forgot the donation box again")
        await Quran(fakes.make_bot()).on_message(message)
        assert api.calls == []

    @pytest.mark.parametrize(
        "response",
        [
            lyerrors.TakinaNotFoundError("past the end of the surah"),
            aiohttp.ClientConnectionError(),
            TimeoutError(),
            {"code": 200},
            {"data": None},
            {"data": {"text": "x"}},
        ],
    )
    async def test_failures_are_quiet(self, api: fakes.FakeAPI, response: Any) -> None:
        api.add(r"alquran", response)
        message = self.message("quran 1:300")
        await Quran(fakes.make_bot()).on_message(message)
        message.reply.assert_not_awaited()


class TestHallOfFame:
    DATA: ClassVar[dict[str, Any]] = {
        "turnins": 42,
        "totalScore": 9001,
        "totalRank": 3,
        "validatedScore": 9000,
        "validatedRank": 4,
        "hsacLevel": 7,
        "lsacLevel": 2,
    }

    async def test_profile(self, api: fakes.FakeAPI) -> None:
        api.add(r"anime\.jhiday\.net/hof/api/user/orangc$", self.DATA)
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(AWCC_HOF).hof, ctx, username="orangc")

        embed = fakes.sent_embed(ctx.reply)
        description = embed.description or ""
        assert embed.title == "orangc"
        assert embed.url == "https://anime.jhiday.net/hof/user/orangc"
        assert "> **MAL Profile**: https://myanimelist.net/profile/orangc" in description
        assert "> **Turnins**: 42" in description
        assert "> **Validated Rank**: 4" in description
        assert "> **LoScore Level**: 2" in description

    async def test_quoted(self, api: fakes.FakeAPI) -> None:
        api.add(r"jhiday", self.DATA)
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(AWCC_HOF).hof, ctx, username="../admin")
        assert api.urls()[0].endswith("/hof/api/user/..%2Fadmin")
        assert fakes.sent_embed(ctx.reply).url == "https://anime.jhiday.net/hof/user/..%2Fadmin"

    async def test_not_found(self, api: fakes.FakeAPI) -> None:
        api.add(r"jhiday", None)
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(fakes.make_cog(AWCC_HOF).hof, fakes.make_ctx(), username="nobody")
        assert "Hall of Fame" in api.calls[0][1]["not_found"]

    async def test_only_in_awcc(self) -> None:
        bot = fakes.make_bot()
        command = fakes.make_cog(AWCC_HOF, bot).hof
        elsewhere = fakes.make_ctx(bot=bot, guild=fakes.make_guild())
        with pytest.raises(commands.CheckFailure):
            await fakes.run_checks(command, elsewhere)

        awcc = fakes.make_guild(name="AWCC")
        awcc.id = AWCC_GUILD_ID
        assert await fakes.run_checks(command, fakes.make_ctx(bot=bot, guild=awcc))

    async def test_owner_anywhere(self) -> None:
        owner = fakes.make_user(name="orangc")
        bot = fakes.make_bot(owners={owner.id})
        ctx = fakes.make_ctx(bot=bot, author=owner)
        assert await fakes.run_checks(fakes.make_cog(AWCC_HOF, bot).hof, ctx)

    async def test_dms_refused(self) -> None:
        bot = fakes.make_bot()
        with pytest.raises(commands.CheckFailure):
            await fakes.run_checks(fakes.make_cog(AWCC_HOF, bot).hof, fakes.make_ctx(bot=bot))
