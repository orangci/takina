import nextcord
from nextcord.ext import commands
import os
from __main__ import cogs, cogs_blacklist, BOT_NAME

class OwnerUtils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot: commands.Bot = bot

    @commands.command()
    @commands.is_owner()
    async def disable(self, ctx: commands.Context, cmd: str):
        if cmd == "disable":
            await ctx.reply("You cannot disable the disable command.", mention_author=False)
        else:
            command = self._bot.get_command(cmd)
            if command is None:
                await ctx.reply("Command not found.", mention_author=False)
                return
            command.enabled = False
            await ctx.reply(f"Successfully disabled `{command}`.", mention_author=False)

    @commands.command()
    @commands.is_owner()
    async def enable(self, ctx: commands.Context, cmd: str):
        if cmd == "disable":
            await ctx.reply("You cannot enable the enable command.", mention_author=False)
        else:
            command = self._bot.get_command(cmd)
            if command is None:
                await ctx.reply("Command not found.", mention_author=False)
                return
            command.enabled = True
            await ctx.reply(f"Successfully enabled `{command}`.", mention_author=False)

    @commands.command(aliases=["maintainer","perms"])
    async def owner(self, ctx: commands.Context):
        owner_names = []
        for owner_id in self._bot.owner_ids:
            owner = self._bot.get_user(owner_id) or await self._bot.fetch_user(owner_id)
            if owner:
                owner_names.append("**" + owner.display_name + "**")
            else:
                owner_names.append(f"Unknown User (ID: {owner_id})")
        for owner_id in self._bot.owner_ids:
            if ctx.author == owner_id:
                is_owner = True
                return

        owner_names_str = ", ".join(owner_names)
        if is_owner:
            await ctx.reply(
                f"You have maintainer level permissions when interacting with {BOT_NAME}. Current users who hold maintainer level permissions: {owner_names_str}"
            , mention_author=False)
        else:
            await ctx.reply(
                f"You are not a maintainer of {BOT_NAME}. Current users who hold maintainer-level permissions: {owner_names_str}"
            , mention_author=False)

    @commands.command(aliases=["rx"])
    @commands.is_owner()
    async def reload_exts(self, ctx: commands.Context, *args):
        if not args:
            reloaded_cogs = []
            failed_cogs = []

            for ext in cogs:
                if ext in self._bot.cogs:
                    try:
                        self._bot.reload_extension("cogs." + ext)
                        reloaded_cogs.append(ext)
                    except Exception as e:
                        failed_cogs.append(f"{ext}: {e}")

            success_message = f"Successfully reloaded all cogs."
            if failed_cogs:
                error_message = (
                    f"\nFailed to reload the following cogs:\n"
                    + "\n".join(failed_cogs)
                )
                await ctx.reply(f"{success_message}{error_message}", mention_author=False)
            else:
                await ctx.reply(success_message, mention_author=False)

        else:
            cog = args[0]
            if "cogs." + cog in self._bot.cogs:
                try:
                    self._bot.reload_extension("cogs." + cog)
                    await ctx.reply(f"Successfully reloaded `cogs.{cog}`.", mention_author=False)
                except Exception as error:
                    await ctx.reply(f"Failed to reload `{cog}`: {error}", mention_author=False)
            else:
                await ctx.reply(f"cog `cogs.{cog}` is not loaded.", mention_author=False)

    @commands.command(aliases=["rsc"])
    @commands.is_owner()
    async def reload_slash_command(self, ctx: commands.Context) -> None:
        await ctx.bot.sync_application_commands()
        await ctx.reply("Successfully synced bot application commands.", mention_author=False)

    @commands.command(aliases=["ux"])
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, *args) -> None:
        cog = args[0]
        try:
            self._bot.unload_extension("cogs." + cog)
            await ctx.reply(f"Successfully unloaded `cogs.{cog}`.", mention_author=False)
        except commands.cogNotLoaded:
            await ctx.reply(f"`cogs.{cog}` was already unloaded.", mention_author=False)

    @commands.command(aliases=["lx"])
    @commands.is_owner()
    async def load(self, ctx: commands.Context, *args) -> None:
        cog = args[0]
        try:
            self._bot.load_extension("cogs." + cog)
        except commands.cogAlreadyLoaded:
            await ctx.reply(f"'cogs.{cog}' was already loaded.", mention_author=False)
        await ctx.reply(f"Successfully loaded `cogs.{cog}`.", mention_author=False)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(OwnerUtils(bot))
