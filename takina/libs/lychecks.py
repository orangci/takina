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
            raise commands.CommandOnCooldown(
                bucket, retry_after, commands.BucketType.user
            )


def has_permissions(**perms: bool):
    async def predicate(ctx: commands.Context):
        if await ctx.bot.is_owner(ctx.author):
            return True

        if ctx.guild is None:
            raise lyerrors.TakinaPermissionError(
                "This command can only be used in a server."
            )

        if not isinstance(ctx.author, discord.Member):
            raise lyerrors.TakinaPermissionError(
                "Unable to determine your permissions."
            )

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
    return app_commands.allowed_installs(users=True, guilds=False)


def dms_only():
    return app_commands.allowed_contexts(guilds=False, dms=True, private_channels=True)


# what the hell are guild apps for, anyway? sure, i'll these them now, but
# i really doubt i'll ever use them, you know?
def is_guild_app():
    return app_commands.allowed_installs(users=False, guilds=True)


def is_user_and_guild_app():
    return app_commands.allowed_installs(users=True, guilds=True)
