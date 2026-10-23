# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors
from discord.ext import commands
from tests import fakes
from typing import Any
import discord
import pytest

OWNER_ID = 961063229168164864


def checked(*decorators: Any) -> commands.Command:
    async def reimu(ctx: commands.Context) -> None:
        pass

    command: Any = reimu
    for decorator in reversed(decorators):
        command = decorator(command)
    return commands.command()(command) if not isinstance(command, commands.Command) else command


def owner() -> Any:
    return fakes.make_user(name="orangc", user_id=OWNER_ID)


class TestHasPermissions:
    def command(self) -> commands.Command:
        return checked(lychecks.has_permissions(manage_messages=True, ban_members=True))

    async def test_allows_with_permissions(self) -> None:
        guild = fakes.make_guild()
        author = fakes.make_member(
            guild, permissions=discord.Permissions(manage_messages=True, ban_members=True)
        )
        assert await fakes.run_checks(self.command(), fakes.make_ctx(guild=guild, author=author))

    async def test_names_every_missing_permission(self) -> None:
        guild = fakes.make_guild()
        ctx = fakes.make_ctx(guild=guild)
        with pytest.raises(lyerrors.TakinaPermissionError) as error:
            await fakes.run_checks(self.command(), ctx)
        assert "Manage Messages" in error.value.message
        assert "Ban Members" in error.value.message

    async def test_names_only_missing(self) -> None:
        guild = fakes.make_guild()
        author = fakes.make_member(guild, permissions=discord.Permissions(manage_messages=True))
        with pytest.raises(lyerrors.TakinaPermissionError) as error:
            await fakes.run_checks(self.command(), fakes.make_ctx(guild=guild, author=author))
        assert "Ban Members" in error.value.message
        assert "Manage Messages" not in error.value.message

    async def test_administrator_implies_all(self) -> None:
        guild = fakes.make_guild()
        author = fakes.make_member(guild, permissions=discord.Permissions(administrator=True))
        assert await fakes.run_checks(self.command(), fakes.make_ctx(guild=guild, author=author))

    async def test_owner_bypasses(self) -> None:
        guild = fakes.make_guild()
        bot = fakes.make_bot(owners={OWNER_ID})
        author = fakes.make_member(guild, user_id=OWNER_ID)
        ctx = fakes.make_ctx(bot=bot, guild=guild, author=author)
        assert await fakes.run_checks(self.command(), ctx)

    async def test_dms_pass(self) -> None:
        assert await fakes.run_checks(self.command(), fakes.make_ctx())

    async def test_non_member_author_in_guild(self) -> None:
        guild = fakes.make_guild()
        ctx = fakes.make_ctx(guild=guild, author=fakes.make_user())
        with pytest.raises(lyerrors.TakinaPermissionError, match="Unable to determine"):
            await fakes.run_checks(self.command(), ctx)


class TestGuildOnly:
    async def test_refuses_dms(self) -> None:
        command = checked(lychecks.guild_only())
        with pytest.raises(commands.CheckFailure):
            await fakes.run_checks(command, fakes.make_ctx())

    async def test_allows_guilds(self) -> None:
        command = checked(lychecks.guild_only())
        assert await fakes.run_checks(command, fakes.make_ctx(guild=fakes.make_guild()))

    def test_hides_from_dms_and_user_installs(self) -> None:
        async def callback(ctx: commands.Context) -> None:
            pass

        command = lychecks.guild_only()(commands.hybrid_command(name="reimu")(callback))
        contexts = command.app_command.allowed_contexts
        installs = command.app_command.allowed_installs
        assert contexts.guild and not contexts.dm_channel
        assert installs.guild and not installs.user


class TestSespGuildOnly:
    async def test_matching_guild(self) -> None:
        guild = fakes.make_guild()
        command = checked(lychecks.sesp_guild_only(guild.id))
        assert await fakes.run_checks(command, fakes.make_ctx(guild=guild))

    async def test_other_guild(self) -> None:
        command = checked(lychecks.sesp_guild_only(275341388554698753))
        with pytest.raises(commands.CheckFailure):
            await fakes.run_checks(command, fakes.make_ctx(guild=fakes.make_guild()))

    async def test_dms(self) -> None:
        command = checked(lychecks.sesp_guild_only(275341388554698753))
        with pytest.raises(commands.CheckFailure):
            await fakes.run_checks(command, fakes.make_ctx())

    async def test_owner_anywhere(self) -> None:
        command = checked(lychecks.sesp_guild_only(275341388554698753))
        ctx = fakes.make_ctx(bot=fakes.make_bot(owners={OWNER_ID}), author=owner())
        assert await fakes.run_checks(command, ctx)


class TestSlashOnly:
    async def test_refuses_prefix_with_a_reason(self) -> None:
        command = checked(lychecks.slash_only())
        with pytest.raises(lyerrors.TakinaUserInputError, match="only works as a slash command"):
            await fakes.run_checks(command, fakes.make_ctx())

    async def test_allows_slash(self) -> None:
        command = checked(lychecks.slash_only())
        assert await fakes.run_checks(command, fakes.make_ctx(interaction=True))


class TestAppDecorators:
    def hybrid(self) -> commands.HybridCommand:
        async def callback(ctx: commands.Context) -> None:
            pass

        return commands.hybrid_command(name="marisa")(callback)

    def test_is_user_app(self) -> None:
        command = lychecks.is_user_app()(self.hybrid())
        assert command.app_command.allowed_installs.user
        contexts = command.app_command.allowed_contexts
        assert contexts.guild and contexts.dm_channel and contexts.private_channel

    def test_dms_only(self) -> None:
        command = lychecks.dms_only()(self.hybrid())
        contexts = command.app_command.allowed_contexts
        assert not contexts.guild and contexts.dm_channel

    def test_is_guild_app(self) -> None:
        command = lychecks.is_guild_app()(self.hybrid())
        assert command.app_command.allowed_installs.guild


class TestCooldown:
    def command(self) -> commands.Command:
        return checked(lychecks.cooldown(1, 60))

    async def test_second_use_is_refused(self) -> None:
        command = self.command()
        guild = fakes.make_guild()
        ctx = fakes.make_ctx(guild=guild)

        command._prepare_cooldowns(ctx)
        with pytest.raises(commands.CommandOnCooldown):
            command._prepare_cooldowns(ctx)

    async def test_members_are_separate(self) -> None:
        command = self.command()
        guild = fakes.make_guild()

        command._prepare_cooldowns(fakes.make_ctx(guild=guild))
        command._prepare_cooldowns(fakes.make_ctx(guild=guild))

    async def test_owners_never_wait(self) -> None:
        command = self.command()
        bot = fakes.make_bot(owners={OWNER_ID})
        guild = fakes.make_guild()
        ctx = fakes.make_ctx(
            bot=bot, guild=guild, author=fakes.make_member(guild, user_id=OWNER_ID)
        )

        for _ in range(5):
            command._prepare_cooldowns(ctx)

    async def test_single_owner_id(self) -> None:
        command = self.command()
        bot = fakes.make_bot()
        bot.owner_ids = set()
        bot.owner_id = OWNER_ID
        guild = fakes.make_guild()
        ctx = fakes.make_ctx(
            bot=bot, guild=guild, author=fakes.make_member(guild, user_id=OWNER_ID)
        )

        for _ in range(3):
            command._prepare_cooldowns(ctx)


class TestGlobalCooldown:
    @pytest.fixture
    def hook(self) -> Any:
        bot = commands.Bot(command_prefix=".", intents=discord.Intents.none())
        lychecks.setup(bot)
        lychecks._cooldown._cache.clear()
        return bot._before_invoke

    async def test_allows_a_burst_then_refuses(self, hook: Any) -> None:
        ctx = fakes.make_ctx()
        for _ in range(lychecks.config.COMMANDS_COOLDOWN):
            await hook(ctx)

        with pytest.raises(commands.CommandOnCooldown):
            await hook(ctx)

    async def test_owners_exempt(self, hook: Any) -> None:
        bot = fakes.make_bot(owners={OWNER_ID})
        ctx = fakes.make_ctx(bot=bot, author=owner())
        for _ in range(lychecks.config.COMMANDS_COOLDOWN * 3):
            await hook(ctx)

    async def test_per_user(self, hook: Any) -> None:
        for _ in range(lychecks.config.COMMANDS_COOLDOWN * 2):
            await hook(fakes.make_ctx())
