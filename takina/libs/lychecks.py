# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from discord import app_commands
from discord.ext import commands
from takina.libs import lyerrors
from takina import config
import discord

# global cooldown for all commands
_cooldown = commands.CooldownMapping.from_cooldown(
    config.COMMANDS_COOLDOWN, 5.0, lambda message: message.author.id
)


def setup(bot: commands.Bot) -> None:
    @bot.before_invoke
    async def global_cooldown(ctx: commands.Context) -> None:
        if await ctx.bot.is_owner(ctx.author):
            return

        bucket = _cooldown.get_bucket(ctx.message)
        if bucket is None:
            return

        retry_after = bucket.update_rate_limit()
        if retry_after is not None:
            raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.user)


def cooldown(rate: int, per: float, type: commands.BucketType = commands.BucketType.member):
    """
    `commands.cooldown`, except bot owners are never rate limited.

    Example:
        @lychecks.cooldown(1, 60)  # once a minute per member
    """

    def factory(ctx: commands.Context) -> commands.Cooldown | None:
        owner_ids = ctx.bot.owner_ids or {ctx.bot.owner_id}
        if ctx.author.id in owner_ids:
            return None

        # a fresh cooldown per bucket, as discord.py keeps one per member
        return commands.Cooldown(rate, per)

    return commands.dynamic_cooldown(factory, type)


def has_permissions(**perms: bool):
    async def predicate(ctx: commands.Context):
        # heh. bot owners can skip checks
        # yes, i know, how sneaky
        # but it's useful for testing purposes anyway
        # and neither of us are the type to abuse this
        # teehee
        if await ctx.bot.is_owner(ctx.author):
            return True

        # has_permissions is to block you when you're not allowed to do something in a server
        # but if you aren't even in a server
        # nobody cares, do yo thing buddy
        if ctx.guild is None:
            return True

        if not isinstance(ctx.author, discord.Member):
            raise lyerrors.TakinaPermissionError("Unable to determine your permissions.")

        permissions = ctx.author.guild_permissions

        missing = [
            name.replace("_", " ").title()
            for name, value in perms.items()
            if getattr(permissions, name) != value
        ]

        if missing:
            raise lyerrors.TakinaPermissionError(
                f"You are missing the following permissions required to use this command: {', '.join(missing)}."
            )

        return True

    return commands.check(predicate)


def is_user_app():
    def decorator(command):
        command = app_commands.allowed_installs(users=True)(command)
        command = app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)(
            command
        )

        return command

    return decorator


def dms_only():
    return app_commands.allowed_contexts(guilds=False, dms=True, private_channels=True)


# what the hell are guild apps for, anyway? sure, i'll make this now, but
# i really doubt i'll ever use them, you know?
def is_guild_app():
    return app_commands.allowed_installs(guilds=True)


# this is for commands that are meant to work only in specific servers
# which is mostly just sesp cog commands
# sesp stands for specific server, by the way
def sesp_guild_only(guild_id: int):
    async def predicate(ctx: commands.Context):
        if await ctx.bot.is_owner(ctx.author):
            return True

        return ctx.guild and ctx.guild.id == guild_id

    return commands.check(predicate)


# this makes a hybrid command a slash command
# i mean, ONLY a slash command
# why not just make slash commands the normal way?
# error handling shenanigans. don't even ask.
# yes. yes, i know this is really damned stupid.
def slash_only():
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.interaction is None:
            # a plain check failure is silent, which leaves prefix users guessing
            raise lyerrors.TakinaUserInputError(
                f"This command only works as a slash command: `/{ctx.command}`."
            )

        return True

    return commands.check(predicate)


# this is also stupid
# but for some reason commands.guild_only doesn't work
# don't ask me why
def guild_only():
    async def predicate(ctx: commands.Context) -> bool:
        return ctx.guild is not None

    def decorator(command):
        command = commands.check(predicate)(command)
        command = app_commands.allowed_installs(users=False, guilds=True)(command)
        command = app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)(
            command
        )

        return command

    return decorator
