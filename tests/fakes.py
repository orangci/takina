# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
"""
Stand-ins for discord objects and the web, small enough to read at a glance.

Members, channels and contexts are specced mocks, so `isinstance` checks in the cogs behave
and their coroutine methods are AsyncMocks. Roles are real `discord.Role`s, as their ordering
is exactly what permission checks compare.
"""

from unittest.mock import AsyncMock, MagicMock
from discord.ext import commands
from typing import Any
import itertools
import discord
import re

_ids = itertools.count(100_000_000_000_000_000)


def next_id() -> int:
    return next(_ids)


class FakeAPI:
    """
    Canned answers for `lyhelpers.request`, matched by regex against the url.

    Example:
        api.add(r"api\\.github\\.com/users/reimu", {"login": "reimu"})
        api.add(r"nekos\\.best", lyerrors.TakinaNotFoundError("Not found."))
    """

    def __init__(self) -> None:
        self.routes: list[tuple[re.Pattern[str], Any]] = []
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def add(self, pattern: str, response: Any) -> None:
        # later routes win, so a test can override a default it set up earlier
        self.routes.insert(0, (re.compile(pattern), response))

    async def request(self, url: str, *args: Any, **kwargs: Any) -> Any:
        self.calls.append((url, kwargs))

        for pattern, response in self.routes:
            if not pattern.search(url):
                continue

            if isinstance(response, BaseException):
                raise response

            if callable(response):
                response = response(url, kwargs)

            if kwargs.get("with_headers"):
                return response if isinstance(response, tuple) else (response, {})

            return response

        raise AssertionError(f"unexpected request to {url}")

    def urls(self) -> list[str]:
        return [url for url, _ in self.calls]


def make_guild(*, name: str = "Gensokyo", filesize_limit: int = 10 * 1024 * 1024) -> MagicMock:
    guild = MagicMock(spec=discord.Guild)
    guild.id = next_id()
    guild.name = name
    guild.__str__.return_value = name
    guild.filesize_limit = filesize_limit
    guild.owner = None
    guild.owner_id = None
    guild.me = None
    guild.roles = []
    guild.channels = []
    guild.get_member.return_value = None
    guild.get_channel.return_value = None
    guild.default_role = make_role(guild, position=0, role_id=guild.id, name="@everyone")
    return guild


def make_role(
    guild: Any,
    *,
    position: int = 1,
    role_id: int | None = None,
    name: str = "Shrine Maiden",
    managed: bool = False,
    permissions: int = 0,
) -> discord.Role:
    data: Any = {
        "id": role_id or next_id(),
        "name": name,
        "position": position,
        "permissions": str(permissions),
        "color": 0,
        "hoist": False,
        "managed": managed,
        "mentionable": False,
    }
    return discord.Role(guild=guild, state=MagicMock(), data=data)


def make_user(*, name: str = "marisa", bot: bool = False, user_id: int | None = None) -> MagicMock:
    user = MagicMock(spec=discord.User)
    _fill_user(user, name=name, bot=bot, user_id=user_id)
    return user


def make_member(
    guild: Any,
    *,
    name: str = "reimu",
    top_role: discord.Role | None = None,
    permissions: discord.Permissions | None = None,
    bot: bool = False,
    user_id: int | None = None,
) -> MagicMock:
    member = MagicMock(spec=discord.Member)
    _fill_user(member, name=name, bot=bot, user_id=user_id)
    member.guild = guild
    member.top_role = top_role or guild.default_role
    member.roles = [guild.default_role] + ([top_role] if top_role else [])
    # discord hands administrators every permission, whatever their roles grant
    permissions = permissions or discord.Permissions.none()
    member.guild_permissions = (
        discord.Permissions.all() if permissions.administrator else permissions
    )
    member.guild_avatar = None
    member.guild_banner = None
    member.joined_at = None
    member.timed_out_until = None
    return member


def _fill_user(user: MagicMock, *, name: str, bot: bool, user_id: int | None) -> None:
    user.id = user_id or next_id()
    user.name = name
    user.display_name = name.title()
    user.global_name = None
    user.bot = bot
    user.mention = f"<@{user.id}>"
    user.__str__.return_value = name
    user.avatar = None
    user.banner = None
    user.display_avatar.url = f"https://cdn.discordapp.com/embed/avatars/{user.id % 6}.png"
    user.created_at = discord.utils.snowflake_time(user.id)


def make_channel(
    guild: Any = None,
    kind: type = discord.TextChannel,
    *,
    name: str = "hakurei-shrine",
    nsfw: bool = False,
) -> MagicMock:
    channel = MagicMock(spec=kind)
    channel.id = next_id()
    channel.name = name
    channel.guild = guild
    channel.mention = f"<#{channel.id}>"
    channel.jump_url = f"https://discord.com/channels/{guild.id if guild else '@me'}/{channel.id}"
    channel.is_nsfw.return_value = nsfw
    if hasattr(kind, "get_partial_message"):
        channel.get_partial_message.return_value = MagicMock(spec=discord.PartialMessage)
    return channel


def make_message(
    *,
    author: Any,
    channel: Any,
    content: str = "",
    guild: Any = None,
    attachments: list[Any] | None = None,
) -> MagicMock:
    message = MagicMock(spec=discord.Message)
    message.id = next_id()
    message.author = author
    message.channel = channel
    message.guild = guild
    message.content = content
    message.attachments = attachments or []
    message.embeds = []
    message.stickers = []
    message.reactions = []
    message.mentions = []
    message.created_at = discord.utils.utcnow()
    message.edited_at = None
    message.jump_url = f"{channel.jump_url}/{message.id}"
    return message


def make_bot(*, owners: set[int] | None = None) -> MagicMock:
    bot = MagicMock(spec=commands.Bot)
    bot.owner_ids = owners or set()
    bot.owner_id = None
    bot.user = make_user(name="takina", bot=True)
    bot.application_id = bot.user.id
    bot.cached_messages = []
    bot.guilds = []
    bot.latency = 0.042
    bot.get_user.return_value = None
    bot.get_channel.return_value = None
    bot.get_guild.return_value = None
    bot.get_command.return_value = None

    async def is_owner(user: Any) -> bool:
        return user.id in bot.owner_ids

    bot.is_owner.side_effect = is_owner
    bot.can_run.return_value = True
    return bot


def make_ctx(
    *,
    bot: Any = None,
    guild: Any = None,
    author: Any = None,
    channel: Any = None,
    interaction: bool = False,
    invoked_with: str | None = None,
) -> MagicMock:
    """A context in `guild` (None for DMs), invoked by prefix unless `interaction` is set."""
    ctx = MagicMock(spec=commands.Context)
    ctx.bot = bot or make_bot()
    ctx.guild = guild
    ctx.author = author or (make_member(guild) if guild else make_user())
    ctx.channel = channel or make_channel(guild)
    ctx.me = guild.me if guild and guild.me else ctx.bot.user
    ctx.interaction = MagicMock(spec=discord.Interaction) if interaction else None
    ctx.invoked_with = invoked_with
    ctx.invoked_subcommand = None
    ctx.command = None
    ctx.prefix = "."
    ctx.clean_prefix = "."
    ctx.message = make_message(author=ctx.author, channel=ctx.channel, guild=guild)
    return ctx


def make_interaction(*, user: Any) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = user
    interaction.response = MagicMock(spec=discord.InteractionResponse)
    interaction.response.is_done.return_value = False
    return interaction


def make_attachment(
    *, filename: str = "yukkuri.png", size: int = 1024, content_type: str = "image/png"
) -> MagicMock:
    attachment = MagicMock(spec=discord.Attachment)
    attachment.id = next_id()
    attachment.filename = filename
    attachment.size = size
    attachment.content_type = content_type
    attachment.url = f"https://cdn.discordapp.com/attachments/{attachment.id}/{filename}"
    attachment.to_file.return_value = MagicMock(spec=discord.File)
    return attachment


def sent(mock: AsyncMock, call: int = -1) -> dict[str, Any]:
    """The keyword arguments of a reply or send, with the content as `content`."""
    assert mock.await_args_list, f"{mock} was never awaited"
    args, kwargs = mock.await_args_list[call]
    return {"content": args[0] if args else kwargs.get("content"), **kwargs}


def sent_embed(mock: AsyncMock, call: int = -1) -> discord.Embed:
    embed = sent(mock, call).get("embed")
    assert isinstance(embed, discord.Embed), f"{mock} sent no embed"
    assert_embed_fits(embed)
    return embed


def assert_embed_fits(embed: discord.Embed) -> None:
    # discord refuses the whole message when any of these is broken
    assert len(embed.title or "") <= 256, "title over 256 characters"
    assert len(embed.description or "") <= 4096, "description over 4096 characters"
    assert len(embed.fields) <= 25, "more than 25 fields"
    for field in embed.fields:
        assert 0 < len(field.name or "") <= 256, f"field name {field.name!r} out of bounds"
        assert 0 < len(field.value or "") <= 1024, f"field {field.name!r} value out of bounds"
    assert len(embed.footer.text or "") <= 2048, "footer over 2048 characters"
    assert len(embed.author.name or "") <= 256, "author over 256 characters"
    assert len(embed) <= 6000, "embed over 6000 characters"


async def run_checks(command: commands.Command, ctx: Any) -> bool:
    """Every check on `command`, as discord.py runs them before a prefix or slash invocation."""
    if not await command.can_run(ctx):
        # what Command.prepare raises when a check answers False rather than raising
        raise commands.CheckFailure(f"the checks for {command.qualified_name} failed")
    return True


def make_cog[T: commands.Cog](cog_class: type[T], bot: Any = None) -> T:
    """The cog with its commands bound to it, as adding it to a bot would, but without one."""
    cog = cog_class(bot or make_bot())
    for command in cog.walk_commands():
        command.cog = cog
    return cog


async def call(command: commands.Command, ctx: Any, *args: Any, **kwargs: Any) -> Any:
    """Run the command's body alone, skipping converters and checks."""
    assert command.cog is not None, f"{command} is not bound; build the cog with make_cog"
    return await command.callback(command.cog, ctx, *args, **kwargs)
