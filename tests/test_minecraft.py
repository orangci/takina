# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.minecraft.hypixel import SOCIAL_SITES, Hypixel, hypixel_errors, social_link
from takina.cogs.minecraft.wynncraft import Wynncraft, discord_timestamp
from takina.cogs.minecraft.mcserver import MinecraftServerStatus
from takina.cogs.minecraft import hypixel as hypixel_cog
from takina.cogs.minecraft.hypixel import zero_missing
from takina.cogs.minecraft.mcskin import Minecraft
from unittest.mock import AsyncMock, MagicMock
from hypixel.models.player import Player
from hypixel.models.guild import Guild
from dataclasses import dataclass
from takina.libs import lyerrors
from typing import Any, cast
from takina import config
from tests import fakes
import importlib
import hypixel
import pytest

# the package's own `utils` attribute is shadowed by a star import, so fetch the module itself
hypixel_utils = importlib.import_module("hypixel.utils")

REIMU_UUID = "a5f1c2d3e4b5a6978877665544332211"


def make_player(**overrides: Any) -> Player:
    """A real hypixel.py player, parsed from raw api data the way its client does."""
    raw: dict[str, Any] = {
        "_id": "hakurei",
        "uuid": REIMU_UUID,
        "displayname": "Reimu",
        "firstLogin": 1_600_000_000_000,
        "lastLogout": 1_700_000_000_000,
        **overrides,
    }
    return Player(raw={"player": raw}, _data=raw, **hypixel_utils._clean(dict(raw), mode="PLAYER"))


def make_hypixel_guild(**overrides: Any) -> Guild:
    raw: dict[str, Any] = {
        "_id": "shrine",
        "name": "Hakurei Shrine",
        "exp": 1_000_000,
        "created": 1_600_000_000_000,
        "members": [],
        "guildExpByGameType": {},
        **overrides,
    }
    return Guild(**hypixel_utils._clean(raw, mode="GUILD"))


def hypixel_cog_with(**responses: Any) -> Hypixel:
    cog = fakes.make_cog(Hypixel)
    client = MagicMock(spec=hypixel.Client)
    for name, value in responses.items():
        setattr(
            client,
            name,
            AsyncMock(side_effect=value)
            if isinstance(value, Exception)
            else AsyncMock(return_value=value),
        )
    cog._client = client
    return cog


class TestZeroMissing:
    def test_numbers_only(self) -> None:
        @dataclass
        class Stats:
            kills: int | None
            ratio: float | None
            title: str | None
            optional_level: "int | None"

        stats = Stats(kills=None, ratio=None, title=None, optional_level=None)
        zero_missing(stats)

        # a missing duels title stays missing rather than becoming a 0
        assert (stats.kills, stats.ratio, stats.title, stats.optional_level) == (0, 0, None, 0)

    def test_keeps_values(self) -> None:
        @dataclass
        class Stats:
            kills: int

        stats = Stats(kills=9)
        zero_missing(stats)
        assert stats.kills == 9

    def test_real_model(self) -> None:
        bedwars = make_player().bedwars
        # what the api does now and then, though the model says int
        cast(Any, bedwars).kills = None
        zero_missing(bedwars)
        assert bedwars.kills == 0


class TestSocialLink:
    @pytest.mark.parametrize(
        ("name", "value", "expected"),
        [
            ("twitter", "reimu", "[twitter](<https://x.com/reimu>)"),
            ("youtube", "zun", "[youtube](<https://youtube.com/@zun>)"),
            ("twitch", "marisa", "[twitch](<https://twitch.tv/marisa>)"),
            ("instagram", "cirno", "[instagram](<https://instagram.com/cirno>)"),
            ("hypixel_forums", "aya", "[hypixel_forums](<https://hypixel.net/members/aya>)"),
        ],
    )
    def test_handles(self, name: str, value: str, expected: str) -> None:
        assert social_link(name, value) == expected

    def test_full_url(self) -> None:
        assert social_link("twitter", "https://x.com/reimu") == "[twitter](<https://x.com/reimu>)"
        assert social_link("twitch", "http://twitch.tv/m") == "[twitch](<http://twitch.tv/m>)"

    def test_handle_quoted(self) -> None:
        # a handle is a single path segment, so slashes and spaces can't wander off
        assert (
            social_link("twitter", "../admin ?x") == "[twitter](<https://x.com/..%2Fadmin%20%3Fx>)"
        )

    def test_brackets_stripped(self) -> None:
        link = social_link("twitter", "https://x.com/reimu>)[evil](<https://evil.test")
        assert link.count("<") == 1
        assert link.count(">") == 1
        assert link.endswith(">)")

    def test_every_site_formats(self) -> None:
        for name in SOCIAL_SITES:
            assert "{}" not in social_link(name, "reimu")


class TestHypixelErrors:
    def test_wraps(self) -> None:
        with pytest.raises(lyerrors.TakinaError, match="Reimu") as caught, hypixel_errors():
            raise hypixel.PlayerNotFound("Reimu")
        assert isinstance(caught.value.__cause__, hypixel.HypixelException)

    def test_others_pass(self) -> None:
        with pytest.raises(KeyError), hypixel_errors():
            raise KeyError("not hypixel's")


class TestHypixelLifecycle:
    async def test_client_lifecycle(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = MagicMock()
        client.close = AsyncMock()
        made: list[Any] = []

        def make_client(key: str) -> Any:
            made.append(key)
            return client

        monkeypatch.setattr(hypixel_cog.hypixel, "Client", make_client)
        cog = Hypixel(fakes.make_bot())
        await cog.cog_load()
        assert made == [config.HYPIXEL_API_KEY]
        assert cog.client is client

        await cog.cog_unload()
        client.close.assert_awaited_once()

    async def test_unload_without_client(self) -> None:
        await Hypixel(fakes.make_bot()).cog_unload()

    async def test_setup_needs_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(config, "HYPIXEL_API_KEY", "")
        bot = fakes.make_bot()
        with pytest.raises(lyerrors.TakinaMissingEnvironmentVariableError):
            await hypixel_cog.setup(bot)
        bot.add_cog.assert_not_awaited()


# five of ten, which is 50% accuracy however one counts it
SHOOTING = [
    ("skywars", {"SkyWars": {"arrows_shot": 10, "arrows_hit": 5}}, "5 hits, 10 shots"),
    ("blitz", {"HungerGames": {"arrows_fired": 10, "arrows_hit": 5}}, "5 hits, 10 shots"),
    ("duels", {"Duels": {"bow_shots": 10, "bow_hits": 5}}, "5 hits, 10 shots"),
    ("duels", {"Duels": {"melee_swings": 10, "melee_hits": 5}}, "5 hits, 10 swings"),
]


class TestHypixelEmbeds:
    async def test_status(self) -> None:
        cog = hypixel_cog_with(player_count=123_456)
        embed = await cog.build_hypixel_status_embed()
        assert "123,456 players" in (embed.description or "")

    async def test_status_error(self) -> None:
        cog = hypixel_cog_with(player_count=hypixel.ApiError(MagicMock(), "Hypixel"))
        with pytest.raises(lyerrors.TakinaError):
            await cog.build_hypixel_status_embed()

    async def test_guild(self) -> None:
        guild = make_hypixel_guild(
            tag="HKR",
            preferredGames=["BEDWARS"],
            description="Donations welcome.",
            publiclyListed=True,
            joinable=False,
        )
        cog = hypixel_cog_with(guild_from_name=guild)
        embed = await cog.build_hypixel_guild_embed("hakurei shrine")

        fakes.assert_embed_fits(embed)
        description = embed.description or ""
        assert embed.title == "Hakurei Shrine"
        assert "> **Tag**: [HKR]" in description
        assert "> **Preferred Games**: Bed Wars" in description
        assert "> **Publicly Listed**: Yes" in description
        assert "> **Joinable**: No" in description
        assert "> **Created**: <t:1600000000:D>" in description
        assert description.endswith("\nDonations welcome.")
        assert embed.footer.text == "Hypixel Guild ID: shrine"

    async def test_bare_guild(self) -> None:
        cog = hypixel_cog_with(guild_from_name=make_hypixel_guild())
        description = (await cog.build_hypixel_guild_embed("x")).description or ""
        assert "Tag" not in description
        assert "Preferred Games" not in description
        assert "Experience Kings" not in description

    async def test_player(self) -> None:
        player = make_player(
            newPackageRank="MVP_PLUS",
            socialMedia={
                "links": {
                    "TWITTER": "https://x.com/reimu",
                    "YOUTUBE": "hakurei",
                    "DISCORD": "reimu_*hakurei*",
                }
            },
            stats={
                "Bedwars": {"Experience": 5000, "kills_bedwars": 10, "wins_bedwars": 3},
                "SkyWars": {"skywars_experience": 20, "kills": 4},
                "Duels": {"wins": 2, "kills": 7},
            },
        )
        cog = hypixel_cog_with(player=player)
        embed = await cog.build_hypixel_player_embed("reimu")

        fakes.assert_embed_fits(embed)
        description = embed.description or ""
        assert embed.title == "Reimu"
        assert description.startswith("-# Last seen <t:1700000000:R>\n\n")
        assert "> **First joined**: <t:1600000000:D>" in description
        assert "[twitter](<https://x.com/reimu>)" in description
        assert "[youtube](<https://youtube.com/@hakurei>)" in description
        assert r"Discord: reimu\_\*hakurei\*" in description
        assert "> **Bedwars**: Level" in description
        assert "> **Skywars**: Level" in description
        assert "> **Duels**:" in description
        assert embed.footer.text == "Hypixel User ID: hakurei"

    async def test_quiet_player(self) -> None:
        # a player who never played anything gets no game lines, and no "None" anywhere
        cog = hypixel_cog_with(player=make_player(lastLogout=None))
        description = (await cog.build_hypixel_player_embed("reimu")).description or ""
        assert not description.startswith("-#")
        for game in ["Bedwars", "Skywars", "Duels", "Socials", "Rank", "Achievements"]:
            assert f"**{game}**" not in description
        assert "None" not in description

    async def test_player_not_found(self) -> None:
        cog = hypixel_cog_with(player=hypixel.PlayerNotFound("cirno"))
        with pytest.raises(lyerrors.TakinaError):
            await cog.build_hypixel_player_embed("cirno")

    @pytest.mark.parametrize(
        ("builder", "heading"),
        [
            ("bedwars", "Bedwars"),
            ("blitz", "Blitz"),
            ("duels", "Duels"),
            ("murder_mystery", "Murder Mystery"),
            ("paintball", "Paintball"),
            ("skywars", "Skywars"),
            ("uhc", "UHC"),
        ],
    )
    async def test_games_survive_empty_stats(self, builder: str, heading: str) -> None:
        cog = hypixel_cog_with(player=make_player())
        embed = await getattr(cog, f"build_hypixel_{builder}_embed")("reimu")

        fakes.assert_embed_fits(embed)
        assert embed.title == f"Reimu's {heading} Statistics"
        assert "None" not in (embed.description or "")
        assert embed.footer.text == "Hypixel User ID: hakurei"

    async def test_bedwars_numbers(self) -> None:
        player = make_player(
            stats={
                "Bedwars": {
                    "Experience": 123_456,
                    "kills_bedwars": 1_500,
                    "deaths_bedwars": 500,
                    "beds_broken_bedwars": 42,
                    "winstreak": 4,
                }
            }
        )
        cog = hypixel_cog_with(player=player)
        description = (await cog.build_hypixel_bedwars_embed("reimu")).description or ""

        assert "> **Kills**: 1,500" in description
        assert "> **Beds broken**: 42" in description
        assert "> **KDR**: 3.0" in description
        assert "> **Current winstreak**: 4" in description

    async def test_archery_only_when_shot(self) -> None:
        unshot = await hypixel_cog_with(player=make_player()).build_hypixel_skywars_embed("r")
        assert "Archery" not in (unshot.description or "")

    @pytest.mark.parametrize(("builder", "stats", "line"), SHOOTING)
    async def test_shooting_lines(self, builder: str, stats: dict, line: str) -> None:
        cog = hypixel_cog_with(player=make_player(stats=stats))
        embed = await getattr(cog, f"build_hypixel_{builder}_embed")("reimu")
        assert line in (embed.description or "")

    # hypixel.py's ar and mr are hits per miss, like a kdr, not hits per shot
    @pytest.mark.xfail(strict=True, reason="ar and mr are formatted as accuracy, but are ratios")
    @pytest.mark.parametrize(("builder", "stats", "line"), SHOOTING)
    async def test_accuracy(self, builder: str, stats: dict, line: str) -> None:
        cog = hypixel_cog_with(player=make_player(stats=stats))
        embed = await getattr(cog, f"build_hypixel_{builder}_embed")("reimu")
        assert f"{line} (50.00% accuracy)" in (embed.description or "")

    async def test_long_description_truncated(self) -> None:
        player = make_player()
        cog = hypixel_cog_with(player=player)
        embed = await cog.stats_embed(player, "Reimu", ["> " + "fumo " * 100] * 20)
        fakes.assert_embed_fits(embed)
        assert (embed.description or "").endswith("…")

    async def test_commands_defer_and_reply(self) -> None:
        cog = hypixel_cog_with(player=make_player(), player_count=1)
        for command in [cog.hypixel_status]:
            ctx = fakes.make_ctx()
            await fakes.call(command, ctx)
            ctx.defer.assert_awaited_once()
            fakes.sent_embed(ctx.reply)

        for command in [
            cog.hypixel_player,
            cog.hypixel_bedwars,
            cog.hypixel_blitz,
            cog.hypixel_duels,
            cog.hypixel_murder_mystery,
            cog.hypixel_paintball,
            cog.hypixel_skywars,
            cog.hypixel_uhc,
        ]:
            ctx = fakes.make_ctx()
            await fakes.call(command, ctx, "reimu")
            ctx.defer.assert_awaited_once()
            assert fakes.sent(ctx.reply)["mention_author"] is False

    async def test_group_sends_help(self) -> None:
        cog = fakes.make_cog(Hypixel)
        ctx = fakes.make_ctx()
        await fakes.call(cog.hypixel_group, ctx)
        ctx.send_help.assert_awaited_once()


class TestDiscordTimestamp:
    def test_relative(self) -> None:
        assert discord_timestamp("2024-01-01T00:00:00+00:00") == "<t:1704067200:R>"

    def test_style(self) -> None:
        assert discord_timestamp("2024-01-01T00:00:00Z", "f") == "<t:1704067200:f>"

    @pytest.mark.parametrize("value", [None, ""])
    def test_unknown(self, value: str | None) -> None:
        assert discord_timestamp(value) == "Unknown"


WYNN_PLAYER: dict[str, Any] = {
    "uuid": "0d3e6f1a-1111-2222-3333-444455556666",
    "username": "Klein",
    "online": False,
    "server": None,
    "lastJoin": "2024-01-01T00:00:00Z",
    "firstJoin": "2020-01-01T00:00:00Z",
    "rank": "Player",
    "playtime": 1234.5,
    "veteran": True,
    "guild": {"name": "Tarot Club", "prefix": "TAR", "rank": "OWNER"},
    "forumLink": 9001,
    "globalData": {
        "mobsKilled": 1000,
        "chestsFound": 50,
        "completedQuests": 20,
        "dungeons": {"total": 3},
        "raids": {"total": 2},
        "wars": 1,
        "pvp": {"kills": 5, "deaths": 4},
    },
}


class TestWynnPlayer:
    async def test_full(self, api: fakes.FakeAPI) -> None:
        api.add(r"/v3/player/Klein$", WYNN_PLAYER)
        api.add(
            r"/characters$",
            {
                "a": {"level": 20, "type": "MAGE", "reskin": None},
                "b": {"level": 106, "type": "ARCHER", "reskin": "Hunter"},
            },
        )
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Wynncraft).player, ctx, "Klein")

        embed = fakes.sent_embed(ctx.reply)
        description = embed.description or ""
        uuid = WYNN_PLAYER["uuid"]
        assert embed.title == "Klein"
        assert embed.url == f"https://wynncraft.com/stats/player/{uuid}"
        assert embed.thumbnail.url == f"https://visage.surgeplay.com/bust/256/{uuid}.webp"
        assert embed.footer.text == "This user is a veteran."
        assert description.startswith("-# Last seen <t:1704067200:R>")
        assert "> **Guild**: Owner of [TAR] Tarot Club" in description
        # "Player" is everyone's rank, so it isn't shown
        assert "**Rank**" not in description
        assert "> **Characters**: Lvl 106 Hunter, Lvl 20 Mage" in description
        assert "> **PVP**: 5 kills / 4 deaths" in description
        assert "[Linked](https://forums.wynncraft.com/members/9001/)" in description

    async def test_online_without_extras(self, api: fakes.FakeAPI) -> None:
        player = {"uuid": "u", "username": "Audrey", "online": True, "server": "EU7", "rank": "VIP"}
        api.add(r"/v3/player/Audrey$", player)
        api.add(r"/characters$", lyerrors.TakinaNotFoundError("no characters"))
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Wynncraft).player, ctx, "Audrey")

        embed = fakes.sent_embed(ctx.reply)
        description = embed.description or ""
        assert description.startswith("-# Currently online on EU7.")
        assert "> **Rank**: VIP" in description
        assert "Characters" not in description
        assert "Guild" not in description
        assert "PVP" not in description
        assert "> **Joined**: Unknown (Unknown)" in description
        assert embed.footer.text is None

    async def test_name_quoted(self, api: fakes.FakeAPI) -> None:
        api.add(r"/v3/player/", None)
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(fakes.make_cog(Wynncraft).player, fakes.make_ctx(), "../guild/x")
        assert api.urls()[0] == "https://api.wynncraft.com/v3/player/..%2Fguild%2Fx"

    async def test_ambiguous(self, api: fakes.FakeAPI) -> None:
        # several players share the name, so wynncraft lists them instead
        api.add(r"/v3/player/Sun$", {"uuid-one": {}, "uuid-two": {}})
        with pytest.raises(lyerrors.TakinaUserInputError, match="UUID"):
            await fakes.call(fakes.make_cog(Wynncraft).player, fakes.make_ctx(), "Sun")

    async def test_not_found_message(self, api: fakes.FakeAPI) -> None:
        api.add(r"/v3/player/", lyerrors.TakinaNotFoundError("nope"))
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(fakes.make_cog(Wynncraft).player, fakes.make_ctx(), "nobody")
        assert "nobody" in api.calls[0][1]["not_found"]


WYNN_GUILD: dict[str, Any] = {
    "name": "Tarot Club",
    "prefix": "TAR",
    "created": "2020-01-01T00:00:00Z",
    "level": 80,
    "xpPercent": 45,
    "territories": 12,
    "wars": 300,
    "online": 7,
    "members": {"owner": {"Klein": {}}},
}


class TestWynnGuild:
    async def test_by_name(self, api: fakes.FakeAPI) -> None:
        api.add(r"/v3/guild/Tarot%20Club$", WYNN_GUILD)
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Wynncraft).guild, ctx, guild_name="Tarot Club")

        embed = fakes.sent_embed(ctx.reply)
        description = embed.description or ""
        assert embed.title == "[TAR] Tarot Club"
        assert embed.url == "https://wynncraft.com/stats/guild/TAR"
        assert "> **Owner(s)**: Klein" in description
        assert "> **Level**: 80 (45% XP)" in description
        assert "> **Created**: <t:1577836800:f> (<t:1577836800:R>)" in description
        assert len(api.calls) == 1

    @pytest.mark.parametrize("miss", [lyerrors.TakinaNotFoundError("nope"), None])
    async def test_falls_back_to_prefix(self, api: fakes.FakeAPI, miss: Any) -> None:
        api.add(r"/v3/guild/tar$", miss)
        api.add(r"/v3/guild/prefix/TAR$", WYNN_GUILD)
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Wynncraft).guild, ctx, guild_name="tar")

        assert api.urls()[-1].endswith("/v3/guild/prefix/TAR")
        assert fakes.sent_embed(ctx.reply).title == "[TAR] Tarot Club"

    async def test_neither(self, api: fakes.FakeAPI) -> None:
        api.add(r"/v3/guild/", None)
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(fakes.make_cog(Wynncraft).guild, fakes.make_ctx(), guild_name="x")

    async def test_group_sends_help(self) -> None:
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Wynncraft).wynn, ctx)
        ctx.send_help.assert_awaited_once()


class TestMcStatus:
    async def test_online(self, api: fakes.FakeAPI) -> None:
        api.add(
            r"mcstatus\.io/v2/status/java/hypixel\.net:25565$",
            {
                "online": True,
                "host": "hypixel.net",
                "version": {"name_clean": "1.8-1.21"},
                "motd": {"clean": "Hypixel Network `[1.8-1.21]`"},
            },
        )
        ctx = fakes.make_ctx()
        await fakes.call(
            fakes.make_cog(MinecraftServerStatus).mcstatus, ctx, server_name=" hypixel.net:25565 "
        )

        embed = fakes.sent_embed(ctx.reply)
        description = embed.description or ""
        assert embed.title == "hypixel.net"
        assert embed.image.url == "https://api.mcstatus.io/v2/widget/java/hypixel.net:25565"
        assert description.startswith("-# 1.8-1.21 (Java)")
        # the motd's backticks can't close the code block
        assert "```Hypixel Network '[1.8-1.21]'```" in description

    @pytest.mark.parametrize("data", [None, {}, {"online": False}])
    async def test_offline(self, api: fakes.FakeAPI, data: Any) -> None:
        api.add(r"mcstatus", data)
        with pytest.raises(lyerrors.TakinaNotFoundError):
            await fakes.call(
                fakes.make_cog(MinecraftServerStatus).mcstatus, fakes.make_ctx(), server_name="x"
            )

    async def test_path_quoted(self, api: fakes.FakeAPI) -> None:
        api.add(r"mcstatus", {"online": True})
        ctx = fakes.make_ctx()
        await fakes.call(
            fakes.make_cog(MinecraftServerStatus).mcstatus, ctx, server_name="a/../b c"
        )
        assert api.urls()[0] == "https://api.mcstatus.io/v2/status/java/a%2F..%2Fb%20c"
        # the host falls back to what was typed
        assert fakes.sent_embed(ctx.reply).title == "a/../b c"
        assert fakes.sent_embed(ctx.reply).description == ""

    async def test_long_motd(self, api: fakes.FakeAPI) -> None:
        api.add(r"mcstatus", {"online": True, "motd": {"clean": "Gensokyo " * 500}})
        ctx = fakes.make_ctx()
        await fakes.call(
            fakes.make_cog(MinecraftServerStatus).mcstatus, ctx, server_name="gensokyo.net"
        )
        fakes.sent_embed(ctx.reply)


class TestMcSkin:
    async def test_skin(self, api: fakes.FakeAPI) -> None:
        api.add(r"api\.mojang\.com/users/profiles/minecraft/", {"id": REIMU_UUID, "name": "Reimu"})
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Minecraft).mcskin, ctx, "rEiMu")

        embed = fakes.sent_embed(ctx.reply)
        assert embed.title == "Reimu"
        assert embed.image.url == f"https://visage.surgeplay.com/full/384/{REIMU_UUID}"
        assert embed.footer.text == f"UUID: {REIMU_UUID}"

    async def test_not_found(self, api: fakes.FakeAPI) -> None:
        api.add(r"mojang", None)
        with pytest.raises(lyerrors.TakinaNotFoundError, match="cirno"):
            await fakes.call(fakes.make_cog(Minecraft).mcskin, fakes.make_ctx(), "cirno")

    async def test_name_quoted(self, api: fakes.FakeAPI) -> None:
        api.add(r"mojang", {"id": REIMU_UUID})
        ctx = fakes.make_ctx()
        await fakes.call(fakes.make_cog(Minecraft).mcskin, ctx, "a/b?c")

        assert api.urls()[0].endswith("/minecraft/a%2Fb%3Fc")
        assert fakes.sent_embed(ctx.reply).title == "a/b?c"
