# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from unittest.mock import MagicMock
from takina.libs import lyviews
from takina import config
from tests import fakes
import discord
import asyncio
import pytest


def pages(count: int) -> list[discord.Embed]:
    return [discord.Embed(description=f"Page {number}") for number in range(1, count + 1)]


class TestAuthorView:
    async def test_author_may_interact(self) -> None:
        author = fakes.make_user(name="reimu")
        view = lyviews.AuthorView(author)
        interaction = fakes.make_interaction(user=author)

        assert await view.interaction_check(interaction)
        interaction.response.send_message.assert_not_awaited()

    async def test_others_are_refused_privately(self) -> None:
        view = lyviews.AuthorView(fakes.make_user(name="reimu"))
        interaction = fakes.make_interaction(user=fakes.make_user(name="marisa"))

        assert not await view.interaction_check(interaction)
        kwargs = fakes.sent(interaction.response.send_message)
        assert kwargs["ephemeral"] is True
        assert kwargs["embed"].colour.value == config.ERROR_COLOUR
        assert "someone else's message" in kwargs["embed"].description

    async def test_same_id_counts_as_author(self) -> None:
        # a member and a user object for one person compare by id
        author = fakes.make_user(name="reimu")
        same_person = fakes.make_user(name="reimu", user_id=author.id)
        view = lyviews.AuthorView(author)
        assert await view.interaction_check(fakes.make_interaction(user=same_person))

    async def test_timeout_disables_items(self) -> None:
        view = lyviews.PaginatorView(fakes.make_user(), pages(3))
        view.message = MagicMock(spec=discord.Message)
        await view.on_timeout()

        assert all(isinstance(item, discord.ui.Button) and item.disabled for item in view.children)
        view.message.edit.assert_awaited_once_with(view=view)

    async def test_timeout_without_message(self) -> None:
        view = lyviews.AuthorView(fakes.make_user())
        await view.on_timeout()

    async def test_timeout_after_message_deleted(self) -> None:
        view = lyviews.PaginatorView(fakes.make_user(), pages(2))
        view.message = MagicMock(spec=discord.Message)
        view.message.edit.side_effect = discord.NotFound(MagicMock(status=404), "gone")
        await view.on_timeout()


class TestPaginatorView:
    async def test_needs_pages(self) -> None:
        with pytest.raises(ValueError):
            lyviews.PaginatorView(fakes.make_user(), [])

    async def test_starts_on_first_page(self) -> None:
        view = lyviews.PaginatorView(fakes.make_user(), pages(3))
        assert view.page == 0
        assert view.first.disabled and view.previous.disabled
        assert not view.next.disabled and not view.last.disabled

    async def test_single_page_disables_everything(self) -> None:
        view = lyviews.PaginatorView(fakes.make_user(), pages(1))
        assert all(isinstance(item, discord.ui.Button) and item.disabled for item in view.children)

    async def test_walks_forwards_and_back(self) -> None:
        embeds = pages(3)
        user = fakes.make_user()
        view = lyviews.PaginatorView(user, embeds)

        interaction = fakes.make_interaction(user=user)
        await view.next.callback(interaction)
        assert view.page == 1
        interaction.response.edit_message.assert_awaited_with(embed=embeds[1], view=view)
        assert not view.previous.disabled and not view.next.disabled

        await view.next.callback(fakes.make_interaction(user=user))
        assert view.page == 2
        assert view.next.disabled and view.last.disabled

        await view.previous.callback(fakes.make_interaction(user=user))
        assert view.page == 1

    async def test_jumps_to_ends(self) -> None:
        embeds = pages(5)
        user = fakes.make_user()
        view = lyviews.PaginatorView(user, embeds)

        interaction = fakes.make_interaction(user=user)
        await view.last.callback(interaction)
        assert view.page == 4
        interaction.response.edit_message.assert_awaited_with(embed=embeds[4], view=view)

        interaction = fakes.make_interaction(user=user)
        await view.first.callback(interaction)
        assert view.page == 0
        interaction.response.edit_message.assert_awaited_with(embed=embeds[0], view=view)

    async def test_send_replies_with_first_page(self) -> None:
        ctx = fakes.make_ctx()
        embeds = pages(2)
        view = await lyviews.PaginatorView.send(ctx, embeds)

        kwargs = fakes.sent(ctx.reply)
        assert kwargs["embed"] is embeds[0]
        assert kwargs["view"] is view
        assert kwargs["mention_author"] is False
        # the message is what lets the buttons be disabled on timeout
        assert view.message is ctx.reply.return_value
        assert view.author is ctx.author


class TestModerationConfirmationView:
    def view(self, ctx: MagicMock) -> lyviews.ModerationConfirmationView:
        return lyviews.ModerationConfirmationView(
            ctx=ctx, member=fakes.make_user(name="cirno"), action="ban", reason="Freezing frogs"
        )

    async def test_mentions_member(self) -> None:
        cirno = fakes.make_user(name="cirno")
        view = lyviews.ModerationConfirmationView(
            ctx=fakes.make_ctx(), member=cirno, action="ban", reason="Freezing frogs"
        )
        assert view.member == cirno.mention

    async def test_text_member_kept(self) -> None:
        view = lyviews.ModerationConfirmationView(
            ctx=fakes.make_ctx(), member="<@1>, <@2>", action="mass ban", reason="Raid"
        )
        assert view.member == "<@1>, <@2>"

    async def test_confirm(self) -> None:
        ctx = fakes.make_ctx()
        view = self.view(ctx)
        prompt = asyncio.create_task(view.prompt())
        await asyncio.sleep(0)

        embed = fakes.sent_embed(ctx.reply)
        assert "Are you sure you want to **ban** <@" in (embed.description or "")
        assert "**Reason**: Freezing frogs" in (embed.description or "")

        interaction = fakes.make_interaction(user=ctx.author)
        await view.confirm.callback(interaction)
        assert await prompt is True
        interaction.response.edit_message.assert_awaited_once_with(view=None)

    async def test_cancel(self) -> None:
        ctx = fakes.make_ctx()
        view = self.view(ctx)
        prompt = asyncio.create_task(view.prompt())
        await asyncio.sleep(0)

        await view.cancel.callback(fakes.make_interaction(user=ctx.author))
        assert await prompt is False

    async def test_timeout_counts_as_no(self) -> None:
        ctx = fakes.make_ctx()
        view = self.view(ctx)
        prompt = asyncio.create_task(view.prompt())
        await asyncio.sleep(0)

        # what discord.py does once the timeout passes with nobody clicking
        view._dispatch_timeout()
        assert await asyncio.wait_for(prompt, 1) is False

    async def test_edit_success(self) -> None:
        ctx = fakes.make_ctx()
        view = self.view(ctx)
        view.message = MagicMock(spec=discord.Message)
        embed = discord.Embed(description="Banned.")
        await view.edit_success(embed)
        view.message.edit.assert_awaited_once_with(embed=embed, view=None)
