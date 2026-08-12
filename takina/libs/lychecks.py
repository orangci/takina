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
        bucket = _cooldown.get_bucket(ctx.message)
        if bucket is None:
            return

        retry_after = bucket.update_rate_limit()
        if retry_after is not None:
            raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.user)


def has_permissions(**perms: bool):
    async def predicate(ctx: commands.Context):
        # heh. bot owners can skip checks
        # yes, i know, how sneaky
        # but it's useful for testing purposes anyway
        # and neither of us are the type to abuse this
        # teehee
        if await ctx.bot.is_owner(ctx.author):
            return True

        if ctx.guild is None:
            raise lyerrors.TakinaPermissionError("This command can only be used in a server.")

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
            return False

        return True


# this is also stupid
# but for some reason commands.guild_only doesn't work
# don't ask me why
def guild_only():
    def decorator(command):
        command = app_commands.allowed_installs(users=False, guilds=True)(command)
        command = app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)(
            command
        )

        return command

    return decorator
