# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors, lychecks, lyhelpers, lyviews
from contextlib import redirect_stdout
from discord.ext import commands
from typing import TYPE_CHECKING, Any, cast
from takina import config
import importlib
import traceback
import textwrap
import logging
import discord
import time
import io

if TYPE_CHECKING:
    from takina.__main__ import Bot

logger = logging.getLogger("takina.owner_utils")


class OwnerUtils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        # owners outside the cache would otherwise be fetched on every .maintainers
        self._owner_cache: dict[int, discord.User] = {}

    def cleanup_code(self, content):
        # for cleaning up codeblocks
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])
        return content.strip("` \n")

    async def run_eval(self, ctx, body):
        env = {
            "bot": self._bot,
            "ctx": ctx,
            "guild": ctx.guild,
            "channel": ctx.channel,
            "author": ctx.author,
            "__import__": __import__,
        }

        env.update(globals())
        body = self.cleanup_code(body)
        stdout = io.StringIO()
        code = f"async def _eval():\n{textwrap.indent(body, '    ')}"

        try:
            exec(code, env)  # noqa: S102
        except Exception as e:  # noqa: BLE001
            return f"```py\n{e.__class__.__name__}: {e}\n```"

        try:
            with redirect_stdout(stdout):
                result = await cast(Any, env["_eval"])()
        except Exception:  # noqa: BLE001
            return f"```py\n{stdout.getvalue()}{traceback.format_exc()}\n```"

        value = stdout.getvalue()
        if result is None:
            if value:
                return f"```py\n{value}\n```"
            else:
                return
        else:
            return f"```py\n{value}{result}\n```"

    @commands.command(hidden=True, name="eval")
    @commands.is_owner()
    async def eval(self, ctx: commands.Context, *, code: str):
        result = await self.run_eval(ctx, code)
        await ctx.message.add_reaction("✅")
        if result:
            await ctx.reply(result, mention_author=False)

    @commands.command(hidden=True, name="guilds")
    @commands.is_owner()
    async def guilds(self, ctx: commands.Context):
        """Lists all guilds the bot is in, ranked from most members to least."""
        guilds_sorted = sorted(self._bot.guilds, key=lambda g: g.member_count or 0, reverse=True)
        description = ""
        for guild in guilds_sorted:
            entry = f"\n**{guild.name}**"

            if len(description) + len(entry) > 4096:
                break
            description += entry

        if not description:
            description = "No guilds available to display."

        embed = discord.Embed(title="Guilds", description=description, colour=config.EMBED_COLOUR)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def disable(self, ctx: commands.Context, cmd: str):
        await self._set_enabled(ctx, cmd, False)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def enable(self, ctx: commands.Context, cmd: str):
        await self._set_enabled(ctx, cmd, True)

    async def _set_enabled(self, ctx: commands.Context, name: str, enabled: bool) -> None:
        action = "enable" if enabled else "disable"
        command = self._bot.get_command(name)
        if command is None:
            raise lyerrors.TakinaNotFoundError("Command not found.")

        # resolved first, so an alias of enable or disable cannot switch them off
        if command.qualified_name in ("enable", "disable"):
            raise lyerrors.TakinaUserInputError(f"You cannot {action} the `{command}` command.")

        command.enabled = enabled
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Successfully {action}d `{command}`."
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(hidden=True, aliases=["maintainer", "perms", "owner", "owners"])
    async def maintainers(self, ctx: commands.Context):
        assert self._bot.owner_ids is not None
        owner_names = ", ".join(
            [await self._owner_name(owner_id) for owner_id in self._bot.owner_ids]
        )

        if ctx.author.id in self._bot.owner_ids:
            intro = (
                f"You have maintainer-level permissions when interacting with {config.BOT_NAME}."
            )
        else:
            intro = f"You are not a maintainer of {config.BOT_NAME}."

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = (
            f"{intro} Current users who hold maintainer-level permissions: {owner_names}"
        )
        await ctx.reply(embed=embed, mention_author=False)

    async def _owner_name(self, owner_id: int) -> str:
        owner = self._bot.get_user(owner_id) or self._owner_cache.get(owner_id)
        if owner is None:
            try:
                owner = await self._bot.fetch_user(owner_id)
            except discord.NotFound:
                return f"Unknown User (ID: {owner_id})"

            self._owner_cache[owner_id] = owner

        return f"**{owner.display_name}**"

    @commands.command(hidden=True, aliases=["rx"])
    @commands.is_owner()
    async def reload_exts(self, ctx: commands.Context, cog: str | None = None):
        importlib.reload(config)
        importlib.reload(lyhelpers)
        lyhelpers.setup(cast("Bot", self._bot))
        importlib.reload(lyerrors)
        importlib.reload(lychecks)
        importlib.reload(lyviews)

        if cog is None:
            failed_cogs = []
            for extension in list(self._bot.extensions.keys()):
                try:
                    await self._bot.reload_extension(extension)
                except commands.ExtensionError as e:
                    failed_cogs.append(f"{extension}: {e}")

            if failed_cogs:
                error_message = "Reloaded all except the following cogs:\n\n" + "\n> ".join(
                    failed_cogs
                )
                logger.warning(error_message)
                raise lyerrors.TakinaError(error_message)
            else:
                embed = discord.Embed(
                    colour=config.EMBED_COLOUR,
                    description=f"{config.emojis.SUCCESS} Successfully reloaded all cogs.",
                )
                await ctx.reply(embed=embed, mention_author=False)
                logger.info("reloaded all cogs")

        else:
            full_cog_name = f"takina.cogs.{cog}" if not cog.startswith("takina.cogs.") else cog

            if full_cog_name in self._bot.extensions:
                try:
                    await self._bot.reload_extension(full_cog_name)
                    embed = discord.Embed(
                        colour=config.EMBED_COLOUR,
                        description=f"{config.emojis.SUCCESS} Successfully reloaded `{full_cog_name}`.",
                    )
                    await ctx.reply(embed=embed, mention_author=False)
                    logger.info(f"reloaded {full_cog_name}")
                except commands.ExtensionError as e:
                    raise lyerrors.TakinaError(f"Failed to reload `{full_cog_name}`: {e}")
            else:
                raise lyerrors.TakinaError(f"Cog `{full_cog_name}` is not loaded.")

    @commands.command(hidden=True, aliases=["rsc"])
    @commands.is_owner()
    async def reload_slash_command(self, ctx: commands.Context) -> None:
        start = time.perf_counter()
        synced = await self._bot.tree.sync()
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        elapsed = time.perf_counter() - start
        embed.description = f"{config.emojis.SUCCESS} Successfully synced {len(synced):,} bot application commands in {elapsed:.4f} seconds."
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(hidden=True, aliases=["ux"])
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, cog: str) -> None:
        try:
            await self._bot.unload_extension("takina.cogs." + cog)
            embed = discord.Embed(colour=config.EMBED_COLOUR)
            embed.description = f"{config.emojis.SUCCESS} Successfully unloaded `cogs.{cog}`."
            await ctx.reply(embed=embed, mention_author=False)
        except commands.ExtensionNotLoaded:
            raise lyerrors.TakinaError(f"`cogs.{cog}` was already unloaded.")

    @commands.command(hidden=True, aliases=["lx"])
    @commands.is_owner()
    async def load(self, ctx: commands.Context, cog: str) -> None:
        try:
            await self._bot.load_extension("takina.cogs." + cog)
        except commands.ExtensionAlreadyLoaded:
            raise lyerrors.TakinaError(f"`cogs.{cog}` was already loaded.")
        except commands.ExtensionNotFound:
            raise lyerrors.TakinaNotFoundError(f"`cogs.{cog}` does not exist.")
        except commands.ExtensionError as e:
            raise lyerrors.TakinaError(f"Failed to load `cogs.{cog}`: {e}")
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Successfully loaded `cogs.{cog}`."
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(hidden=True)
    @lychecks.guild_only()
    @commands.is_owner()
    async def send(
        self, ctx: commands.Context, channel: discord.TextChannel | None = None, *, message: str
    ):
        channel = channel or cast(discord.TextChannel, ctx.channel)

        await channel.send(message)
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Message sent."
        if ctx.interaction is not None:
            await ctx.reply(embed=embed, ephemeral=True)

    @commands.command(hidden=True, aliases=["ci"])
    @commands.is_owner()
    async def command_info(self, ctx: commands.Context, *, name: str):
        command = self._bot.get_command(name)

        if not command:
            raise lyerrors.TakinaNotFoundError("That command doesn't seem to exist.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = f"Command: {command.qualified_name}"

        embed.description = f"\n> **Description**: {command.description}"
        embed.description += f"\n> **Usage**: {command.signature}"
        embed.description += f"\n> **Enabled**: {command.enabled}"
        embed.description += f"\n> **Hidden**: {command.hidden}"

        app_command = getattr(command, "app_command", None)

        if app_command:
            contexts = (
                ", ".join(
                    name
                    for name, attr in (
                        ("Guilds", "guild"),
                        ("DMs", "dm_channel"),
                        ("Private Channels", "private_channel"),
                    )
                    if getattr(app_command.allowed_contexts, attr, False)
                )
                or "Default"
            )

            installs = (
                ", ".join(
                    name
                    for name, attr in (("Guilds", "guild"), ("Users", "user"))
                    if getattr(app_command.allowed_installs, attr, False)
                )
                or "Default"
            )

            embed.description += f"\n> **Contexts**: {contexts}"
            embed.description += f"\n> **Allowed Installs**: {installs}"

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OwnerUtils(bot))
