# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.core.settings import FEATURE_COLUMNS, FEATURE_NAMES, Feature, Settings
from takina.models import GuildSettingsModel, StarboardSettingsModel
from unittest.mock import MagicMock
from types import SimpleNamespace
from takina.libs import lyerrors
from discord.ext import commands
from typing import Any, get_args
from takina import database
from tests import fakes
import discord
import pytest

pytestmark = pytest.mark.usefixtures("db")


@pytest.fixture
def world() -> SimpleNamespace:
    guild = fakes.make_guild(name="Gensokyo")
    cog = fakes.make_cog(Settings)
    admin = fakes.make_member(guild, permissions=discord.Permissions(manage_guild=True))
    return SimpleNamespace(guild=guild, cog=cog, admin=admin)


def ctx(world: SimpleNamespace) -> MagicMock:
    return fakes.make_ctx(guild=world.guild, author=world.admin)


def command(world: SimpleNamespace, name: str) -> Any:
    return next(c for c in world.cog.walk_commands() if c.qualified_name == name)


async def guild_settings(world: SimpleNamespace) -> GuildSettingsModel:
    settings = await database.get(GuildSettingsModel, guild_id=world.guild.id)
    assert settings is not None
    return settings


class TestShow:
    async def test_defaults(self, world: SimpleNamespace) -> None:
        context = ctx(world)
        await fakes.call(world.cog.show, context)
        description = fakes.sent_embed(context.reply).description or ""
        assert "Settings for **Gensokyo**" in description
        assert "**Modlog channel**: Not set" in description
        assert "**Honeypot channel**: Not set" in description
        assert "**Reports channel**: Not set" in description
        assert "**Starboard**: Not set" in description
        assert "**GitHub previews**: On" in description

    async def test_configured(self, world: SimpleNamespace) -> None:
        await database.save(
            GuildSettingsModel(
                guild_id=world.guild.id,
                modlog_channel_id=1,
                honeypot_channel_id=2,
                reports_channel_id=3,
                reports_notification_role_id=4,
                github_previews=False,
            )
        )
        await database.save(
            StarboardSettingsModel(
                guild_id=world.guild.id, starboard_channel_id=5, minimum_reaction_count=1200
            )
        )

        context = ctx(world)
        await fakes.call(world.cog.guild_settings, context)
        description = fakes.sent_embed(context.reply).description or ""
        assert "**Modlog channel**: <#1>" in description
        assert "**Honeypot channel**: <#2>" in description
        assert "**Reports channel**: <#3>, pings <@&4>" in description
        assert "**Starboard**: <#5>, 1,200 reactions" in description
        assert "**GitHub previews**: Off" in description

    async def test_ping_without_channel_hidden(self, world: SimpleNamespace) -> None:
        await database.save(
            GuildSettingsModel(guild_id=world.guild.id, reports_notification_role_id=4)
        )
        context = ctx(world)
        await fakes.call(world.cog.show, context)
        assert "<@&4>" not in (fakes.sent_embed(context.reply).description or "")


class TestSetters:
    async def test_modlog(self, world: SimpleNamespace) -> None:
        channel = fakes.make_channel(world.guild)
        context = ctx(world)
        await fakes.call(world.cog.modlog_channel, context, channel)
        assert (await guild_settings(world)).modlog_channel_id == channel.id
        assert channel.mention in (fakes.sent_embed(context.reply).description or "")

    async def test_honeypot(self, world: SimpleNamespace) -> None:
        channel = fakes.make_channel(world.guild)
        context = ctx(world)
        await fakes.call(world.cog.honeypot, context, channel)
        assert (await guild_settings(world)).honeypot_channel_id == channel.id
        assert "timeout members" in (fakes.sent_embed(context.reply).description or "")

    async def test_reports_with_role(self, world: SimpleNamespace) -> None:
        channel = fakes.make_channel(world.guild)
        role = fakes.make_role(world.guild)
        await fakes.call(world.cog.reports, ctx(world), channel, role)
        settings = await guild_settings(world)
        assert settings.reports_channel_id == channel.id
        assert settings.reports_notification_role_id == role.id

    async def test_reports_keeps_role_when_omitted(self, world: SimpleNamespace) -> None:
        role = fakes.make_role(world.guild)
        await fakes.call(world.cog.reports, ctx(world), fakes.make_channel(world.guild), role)
        new_channel = fakes.make_channel(world.guild)
        await fakes.call(world.cog.reports, ctx(world), new_channel)

        settings = await guild_settings(world)
        assert settings.reports_channel_id == new_channel.id
        assert settings.reports_notification_role_id == role.id

    async def test_starboard(self, world: SimpleNamespace) -> None:
        channel = fakes.make_channel(world.guild)
        context = ctx(world)
        await fakes.call(world.cog.starboard, context, channel, 7)
        starboard = await database.get(StarboardSettingsModel, guild_id=world.guild.id)
        assert starboard is not None
        assert (starboard.starboard_channel_id, starboard.minimum_reaction_count) == (channel.id, 7)
        assert "**Minimum reactions**: 7" in (fakes.sent_embed(context.reply).description or "")

    @pytest.mark.parametrize("enabled", [True, False])
    async def test_github_previews(self, world: SimpleNamespace, enabled: bool) -> None:
        context = ctx(world)
        await fakes.call(world.cog.github_previews, context, enabled)
        assert (await guild_settings(world)).github_previews is enabled
        word = "on" if enabled else "off"
        assert f"now {word}" in (fakes.sent_embed(context.reply).description or "")

    async def test_setters_keep_other_settings(self, world: SimpleNamespace) -> None:
        modlog, honeypot = fakes.make_channel(world.guild), fakes.make_channel(world.guild)
        await fakes.call(world.cog.modlog_channel, ctx(world), modlog)
        await fakes.call(world.cog.honeypot, ctx(world), honeypot)
        await fakes.call(world.cog.github_previews, ctx(world), False)

        settings = await guild_settings(world)
        assert settings.modlog_channel_id == modlog.id
        assert settings.honeypot_channel_id == honeypot.id


class TestDisable:
    def test_every_feature_has_a_home(self) -> None:
        for feature in get_args(Feature):
            assert feature in FEATURE_NAMES
            assert feature == "starboard" or feature in FEATURE_COLUMNS
            column = FEATURE_COLUMNS.get(feature)
            assert column is None or column in GuildSettingsModel.model_fields

    @pytest.mark.parametrize("feature", sorted(FEATURE_COLUMNS))
    async def test_clears_the_column(self, world: SimpleNamespace, feature: str) -> None:
        await database.save(
            GuildSettingsModel(
                guild_id=world.guild.id,
                modlog_channel_id=1,
                honeypot_channel_id=2,
                reports_channel_id=3,
                reports_notification_role_id=4,
            )
        )
        context = ctx(world)
        await fakes.call(world.cog.disable, context, feature)

        settings = await guild_settings(world)
        for other, column in FEATURE_COLUMNS.items():
            assert (getattr(settings, column) is None) is (other == feature)
        assert "has been disabled" in (fakes.sent_embed(context.reply).description or "")

    @pytest.mark.parametrize("feature", get_args(Feature))
    async def test_not_set_up(self, world: SimpleNamespace, feature: str) -> None:
        with pytest.raises(lyerrors.TakinaError, match="not set up"):
            await fakes.call(world.cog.disable, ctx(world), feature)

    async def test_reports_ping_alone(self, world: SimpleNamespace) -> None:
        await database.save(
            GuildSettingsModel(
                guild_id=world.guild.id, reports_channel_id=3, reports_notification_role_id=4
            )
        )
        await fakes.call(world.cog.disable, ctx(world), "reports-ping")
        settings = await guild_settings(world)
        assert settings.reports_channel_id == 3
        assert settings.reports_notification_role_id is None

    async def test_starboard_keeps_its_setup(self, world: SimpleNamespace) -> None:
        await database.save(
            StarboardSettingsModel(
                guild_id=world.guild.id,
                starboard_channel_id=5,
                minimum_reaction_count=9,
                whitelisted_channel_ids=[6],
            )
        )
        await fakes.call(world.cog.disable, ctx(world), "starboard")

        starboard = await database.get(StarboardSettingsModel, guild_id=world.guild.id)
        assert starboard is not None
        assert starboard.starboard_channel_id is None
        assert starboard.minimum_reaction_count == 9
        assert starboard.whitelisted_channel_ids == [6]


class TestChecks:
    @pytest.mark.parametrize(
        "name",
        [
            "settings guild",
            "settings guild show",
            "settings guild modlog-channel",
            "settings guild honeypot",
            "settings guild reports",
            "settings guild starboard",
            "settings guild github-previews",
            "settings guild disable",
        ],
    )
    async def test_manage_server(self, world: SimpleNamespace, name: str) -> None:
        moderator = fakes.make_member(
            world.guild, permissions=discord.Permissions(manage_channels=True, ban_members=True)
        )
        with pytest.raises(lyerrors.TakinaPermissionError, match="Manage Guild"):
            await fakes.run_checks(
                command(world, name), fakes.make_ctx(guild=world.guild, author=moderator)
            )

        assert await fakes.run_checks(command(world, name), ctx(world))

    @pytest.mark.parametrize("name", ["settings guild", "settings guild disable"])
    async def test_not_in_dms(self, world: SimpleNamespace, name: str) -> None:
        with pytest.raises(commands.CheckFailure):
            await fakes.run_checks(command(world, name), fakes.make_ctx())

    async def test_user_settings_stub(self, world: SimpleNamespace) -> None:
        context = fakes.make_ctx()
        await fakes.call(world.cog.user_settings, context)
        assert "not available yet" in (fakes.sent_embed(context.reply).description or "")

    async def test_root_sends_help(self, world: SimpleNamespace) -> None:
        context = ctx(world)
        await fakes.call(world.cog.settings, context)
        context.send_help.assert_awaited_once()
