from discord import app_commands
from discord.ext import commands
from takina import config
import discord

# global cooldown for all commands
_cooldown = commands.CooldownMapping.from_cooldown(
    config.COMMANDS_COOLDOWN, 5.0, lambda m: m.author.id
)


def setup(bot: commands.Bot) -> None:
    @bot.check
    async def global_cooldown(ctx: commands.Context) -> bool:
        bucket = _cooldown.get_bucket(ctx.message)
        if bucket is None:
            return True

        return bucket.update_rate_limit() is None


def has_permissions(**perms: bool):
    async def predicate(ctx: commands.Context):
        if await ctx.bot.is_owner(ctx.author):
            return True

        if ctx.guild is None:
            return False

        if isinstance(ctx.author, discord.Member):
            permissions = ctx.author.guild_permissions
        else:
            return False

        return all(getattr(permissions, name) == value for name, value in perms.items())

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
