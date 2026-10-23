# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.cogs.management.embed_builder import EmbedBuilder, EmbedModal
from takina.cogs.management.channels import MAX_SLOWMODE, Channels
from takina.cogs.management.roles import Roles, check_assignable
from unittest.mock import MagicMock
from types import SimpleNamespace
from takina.libs import lyerrors
from typing import Any, cast
from takina import config
from tests import fakes
import discord
import pytest


@pytest.fixture
def world() -> SimpleNamespace:
    guild = fakes.make_guild()
    roles = SimpleNamespace(
        fairy=fakes.make_role(guild, position=1, name="Fairy"),
        helper=fakes.make_role(guild, position=10, name="Helper"),
        moderator=fakes.make_role(guild, position=20, name="Moderator"),
        admin=fakes.make_role(guild, position=30, name="Admin"),
        bot=fakes.make_role(guild, position=25, name="Takina"),
        booster=fakes.make_role(guild, position=5, name="Booster", managed=True),
    )
    guild.me = fakes.make_member(guild, name="takina", top_role=roles.bot, bot=True)
    owner = fakes.make_member(guild, name="yukari", top_role=roles.fairy)
    guild.owner = owner
    moderator = fakes.make_member(
        guild,
        name="reimu",
        top_role=roles.moderator,
        permissions=discord.Permissions(manage_roles=True, manage_channels=True),
    )
    cirno = fakes.make_member(guild, name="cirno", top_role=roles.fairy)
    return SimpleNamespace(guild=guild, roles=roles, owner=owner, moderator=moderator, cirno=cirno)


def ctx(world: SimpleNamespace, author: Any = None, **kwargs: Any) -> Any:
    return fakes.make_ctx(guild=world.guild, author=author or world.moderator, **kwargs)


class TestCheckAssignable:
    def test_allows_lower_role_to_lower_member(self, world: SimpleNamespace) -> None:
        check_assignable(ctx(world), world.cirno, world.roles.helper)

    def test_allows_self(self, world: SimpleNamespace) -> None:
        check_assignable(ctx(world), world.moderator, world.roles.helper)

    @pytest.mark.parametrize("role", ["moderator", "admin"])
    def test_refuses_role_at_or_above_own(self, world: SimpleNamespace, role: str) -> None:
        # manage roles alone once let anyone hand out administrator
        with pytest.raises(
            lyerrors.TakinaPermissionError, match="higher than or equal to your top role"
        ):
            check_assignable(ctx(world), world.cirno, getattr(world.roles, role))

    def test_refuses_member_at_or_above(self, world: SimpleNamespace) -> None:
        peer = fakes.make_member(world.guild, name="sanae", top_role=world.roles.moderator)
        with pytest.raises(lyerrors.TakinaPermissionError, match="roles of"):
            check_assignable(ctx(world), peer, world.roles.helper)

    def test_refuses_managed(self, world: SimpleNamespace) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError, match="managed"):
            check_assignable(ctx(world), world.cirno, world.roles.booster)

    def test_refuses_everyone(self, world: SimpleNamespace) -> None:
        with pytest.raises(lyerrors.TakinaUserInputError):
            check_assignable(ctx(world), world.cirno, world.guild.default_role)

    def test_owner_may_give_anything_below_the_bot(self, world: SimpleNamespace) -> None:
        check_assignable(ctx(world, world.owner), world.moderator, world.roles.moderator)

    def test_bot_cannot_reach_above_itself(self, world: SimpleNamespace) -> None:
        with pytest.raises(lyerrors.TakinaBotPermissionError, match="my top role"):
            check_assignable(ctx(world, world.owner), world.cirno, world.roles.admin)


class TestRoleCommands:
    async def test_add(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Roles)
        context = ctx(world)
        await fakes.call(cog.add, context, world.cirno, role=world.roles.helper)
        world.cirno.add_roles.assert_awaited_once_with(
            world.roles.helper, reason="Role added by reimu"
        )
        assert world.roles.helper.mention in (fakes.sent_embed(context.reply).description or "")

    async def test_add_to_self_by_default(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Roles)
        await fakes.call(cog.add, ctx(world), None, role=world.roles.helper)
        world.moderator.add_roles.assert_awaited_once()

    async def test_add_existing(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Roles)
        world.cirno.roles.append(world.roles.helper)
        with pytest.raises(lyerrors.TakinaError, match="already has"):
            await fakes.call(cog.add, ctx(world), world.cirno, role=world.roles.helper)

    async def test_add_refused_above_own(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Roles)
        with pytest.raises(lyerrors.TakinaPermissionError):
            await fakes.call(cog.add, ctx(world), world.cirno, role=world.roles.admin)
        world.cirno.add_roles.assert_not_awaited()

    async def test_remove(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Roles)
        world.cirno.roles.append(world.roles.helper)
        await fakes.call(cog.remove, ctx(world), world.cirno, role=world.roles.helper)
        world.cirno.remove_roles.assert_awaited_once_with(
            world.roles.helper, reason="Role removed by reimu"
        )

    async def test_remove_missing(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Roles)
        with pytest.raises(lyerrors.TakinaError, match="did not have"):
            await fakes.call(cog.remove, ctx(world), world.cirno, role=world.roles.helper)

    async def test_remove_refused_above_own(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Roles)
        world.cirno.roles.append(world.roles.admin)
        with pytest.raises(lyerrors.TakinaPermissionError):
            await fakes.call(cog.remove, ctx(world), world.cirno, role=world.roles.admin)

    async def test_info_moves_to_roleinfo(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Roles)
        context = ctx(world)
        context.bot.get_command.return_value = MagicMock()
        await fakes.call(cog.info, context, role=world.roles.helper)
        context.invoke.assert_awaited_once_with(
            context.bot.get_command.return_value, role=world.roles.helper
        )

    async def test_info_without_info_cog(self, world: SimpleNamespace) -> None:
        cog = fakes.make_cog(Roles)
        with pytest.raises(lyerrors.TakinaDisabledError):
            await fakes.call(cog.info, ctx(world), role=world.roles.helper)

    @pytest.mark.parametrize("name", ["role add", "role remove"])
    async def test_need_manage_roles(self, world: SimpleNamespace, name: str) -> None:
        cog = fakes.make_cog(Roles)
        command = next(c for c in cog.walk_commands() if c.qualified_name == name)
        with pytest.raises(lyerrors.TakinaPermissionError, match="Manage Roles"):
            await fakes.run_checks(command, ctx(world, world.cirno))


def modal(**values: str) -> EmbedModal:
    built = EmbedModal()
    inputs = {
        "title": built.title_input,
        "description": built.description_input,
        "colour": built.colour_input,
        "footer": built.footer_input,
        "fields": built.fields_input,
    }
    for name, value in values.items():
        inputs[name]._value = value
    return built


def answer(interaction: Any) -> tuple[discord.Embed, dict[str, Any]]:
    kwargs = fakes.sent(interaction.response.send_message)
    return kwargs["embed"], kwargs


class TestEmbedBuilder:
    async def test_full_embed(self) -> None:
        interaction = fakes.make_interaction(user=fakes.make_user())
        await modal(
            title="Bunbunmaru News",
            description="Extra! Extra!",
            colour="ff0037",
            footer="Aya Shameimaru",
            fields="Scoop: Cirno froze the lake; Weather: Sunny",
        ).on_submit(interaction)

        embed, kwargs = answer(interaction)
        assert "ephemeral" not in kwargs
        assert embed.title == "Bunbunmaru News"
        assert embed.description == "Extra! Extra!"
        assert embed.colour is not None and embed.colour.value == 0xFF0037
        assert embed.footer.text == "Aya Shameimaru"
        assert [(field.name, field.value) for field in embed.fields] == [
            ("Scoop", "Cirno froze the lake"),
            ("Weather", "Sunny"),
        ]

    async def test_minimal(self) -> None:
        interaction = fakes.make_interaction(user=fakes.make_user())
        await modal(description="Just text").on_submit(interaction)
        embed, _ = answer(interaction)
        assert embed.title is None and embed.fields == []
        assert embed.colour is not None and embed.colour.value == config.EMBED_COLOUR

    async def test_colon_in_value_kept(self) -> None:
        interaction = fakes.make_interaction(user=fakes.make_user())
        await modal(description="x", fields="Time: 14:00").on_submit(interaction)
        embed, _ = answer(interaction)
        assert embed.fields[0].value == "14:00"

    async def test_parts_without_colon_skipped(self) -> None:
        interaction = fakes.make_interaction(user=fakes.make_user())
        await modal(description="x", fields="no colon here; a: b").on_submit(interaction)
        embed, _ = answer(interaction)
        assert [field.name for field in embed.fields] == ["a"]

    @pytest.mark.parametrize(
        ("values", "message"),
        [
            ({"colour": "#nothex"}, "is not a hex colour"),
            ({"fields": "; ".join(f"n{i}: v" for i in range(26))}, "at most 25 fields"),
            ({"fields": ": empty name"}, "Each field needs"),
            ({"fields": "empty value: "}, "Each field needs"),
            ({"fields": "n" * 257 + ": v"}, "Each field needs"),
            ({"fields": "n: " + "v" * 1025}, "Each field needs"),
            (
                {
                    "title": "t" * 256,
                    "footer": "f" * 2048,
                    "fields": "; ".join(f"n{i}: " + "v" * 1000 for i in range(4)),
                },
                "6,000 characters",
            ),
        ],
    )
    async def test_refusals_are_private(self, values: dict[str, str], message: str) -> None:
        interaction = fakes.make_interaction(user=fakes.make_user())
        await modal(description="x", **values).on_submit(interaction)
        embed, kwargs = answer(interaction)
        assert kwargs["ephemeral"] is True
        assert message in (embed.description or "")
        assert embed.colour is not None and embed.colour.value == config.ERROR_COLOUR

    async def test_on_error_answers_once(self) -> None:
        interaction = fakes.make_interaction(user=fakes.make_user())
        await EmbedModal().on_error(interaction, RuntimeError("boom"))
        assert "could not be sent" in (
            fakes.sent_embed(interaction.response.send_message).description or ""
        )

        interaction = fakes.make_interaction(user=fakes.make_user())
        interaction.response.is_done.return_value = True
        await EmbedModal().on_error(interaction, RuntimeError("boom"))
        interaction.response.send_message.assert_not_awaited()

    def test_modal_limits_match_discord(self) -> None:
        built = EmbedModal()
        assert built.title_input.max_length == 256
        assert built.description_input.max_length == 4000
        assert built.footer_input.max_length == 2048

    async def test_command_opens_modal(self) -> None:
        cog = EmbedBuilder(fakes.make_bot())
        interaction = fakes.make_interaction(user=fakes.make_user())
        await cast(Any, cog.embed_command.callback)(cog, interaction)
        assert isinstance(interaction.response.send_modal.await_args_list[-1].args[0], EmbedModal)

    def test_command_defaults_to_manage_channels(self) -> None:
        permissions = EmbedBuilder.embed_command.default_permissions
        assert permissions is not None and permissions.manage_channels


class TestChannels:
    @pytest.fixture
    def cog(self) -> Channels:
        return fakes.make_cog(Channels)

    async def test_slowmode_set(self, world: SimpleNamespace, cog: Channels) -> None:
        context = ctx(world)
        await fakes.call(cog.slowmode, context, "1h 30m")
        context.channel.edit.assert_awaited_once_with(slowmode_delay=5400)
        assert "Slowmode set to 1h 30m" in (fakes.sent_embed(context.reply).description or "")

    @pytest.mark.parametrize("word", ["off", "OFF", "disable", "0s"])
    async def test_slowmode_off(self, world: SimpleNamespace, cog: Channels, word: str) -> None:
        context = ctx(world)
        await fakes.call(cog.slowmode, context, word)
        context.channel.edit.assert_awaited_once_with(slowmode_delay=0)
        assert "disabled" in (fakes.sent_embed(context.reply).description or "")

    async def test_slowmode_too_long(self, world: SimpleNamespace, cog: Channels) -> None:
        context = ctx(world)
        with pytest.raises(lyerrors.TakinaUserInputError, match="six hours"):
            await fakes.call(cog.slowmode, context, "7h")
        context.channel.edit.assert_not_awaited()

    async def test_slowmode_maximum(self, world: SimpleNamespace, cog: Channels) -> None:
        context = ctx(world)
        await fakes.call(cog.slowmode, context, "6h")
        context.channel.edit.assert_awaited_once_with(slowmode_delay=MAX_SLOWMODE)

    async def test_slowmode_show(self, world: SimpleNamespace, cog: Channels) -> None:
        context = ctx(world)
        context.channel.slowmode_delay = 90
        await fakes.call(cog.slowmode, context)
        assert "set to 1m 30s" in (fakes.sent_embed(context.reply).description or "")

        context = ctx(world)
        context.channel.slowmode_delay = 0
        await fakes.call(cog.slowmode, context)
        assert "not enabled" in (fakes.sent_embed(context.reply).description or "")

    async def test_slowmode_other_channel(self, world: SimpleNamespace, cog: Channels) -> None:
        other = fakes.make_channel(world.guild)
        context = ctx(world)
        await fakes.call(cog.slowmode, context, "5s", other)
        other.edit.assert_awaited_once_with(slowmode_delay=5)
        context.channel.edit.assert_not_awaited()

    async def test_wrong_channel_kind(self, world: SimpleNamespace, cog: Channels) -> None:
        context = ctx(world, channel=fakes.make_channel(world.guild, discord.ForumChannel))
        with pytest.raises(lyerrors.TakinaUserInputError, match="text channels"):
            await fakes.call(cog.lock, context)

    async def test_lock_and_unlock(self, world: SimpleNamespace, cog: Channels) -> None:
        context = ctx(world)
        overwrite = discord.PermissionOverwrite(add_reactions=False)
        context.channel.overwrites_for.return_value = overwrite

        await fakes.call(cog.lock, context)
        args, kwargs = context.channel.set_permissions.await_args_list[-1]
        assert args[0] is world.guild.default_role
        locked = kwargs["overwrite"]
        assert locked.send_messages is False and locked.send_messages_in_threads is False
        # other overwrites the server set stay as they were
        assert locked.add_reactions is False
        assert kwargs["reason"] == "Locked by reimu."

        await fakes.call(cog.unlock, context)
        unlocked = context.channel.set_permissions.await_args_list[-1].kwargs["overwrite"]
        assert unlocked.send_messages is None and unlocked.send_messages_in_threads is None
        assert unlocked.add_reactions is False

    async def test_lock_thread(self, world: SimpleNamespace, cog: Channels) -> None:
        thread = fakes.make_channel(world.guild, discord.Thread)
        context = ctx(world, channel=thread)
        await fakes.call(cog.lock, context)
        thread.edit.assert_awaited_once_with(locked=True, reason="Locked by reimu.")
        assert "has been locked" in (fakes.sent_embed(context.reply).description or "")

    @pytest.mark.parametrize("name", ["slowmode", "lock", "unlock"])
    async def test_need_manage_channels(
        self, world: SimpleNamespace, cog: Channels, name: str
    ) -> None:
        with pytest.raises(lyerrors.TakinaPermissionError, match="Manage Channels"):
            await fakes.run_checks(getattr(cog, name), ctx(world, world.cirno))
