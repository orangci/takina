import nextcord
from nextcord.ext import commands
import os
from __main__ import extensions


class OwnerUtils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot: commands.Bot = bot

    @commands.command()
    @commands.is_owner()
    async def disable(self, ctx: commands.Context, command: str):
        if cmd == "disable":
            await ctx.reply("You cannot disable the disable command.", mention_author=False)
        else:
            command = self._bot.get_command(command)
            if command is None:
                await ctx.reply("Command not found.", mention_author=False)
                return
            command.enabled = not command.enabled
            await ctx.reply(f"Successfully disabled {command}.", mention_author=False)

    @commands.command(aliases=["perms", "owners", "maintainer", "maintainers"])
    async def owner(self, ctx: commands.Context):
        owner_names = []
        for owner_id in self._bot.owner_ids:
            owner = self._bot.get_user(owner_id) or await self._bot.fetch_user(owner_id)
            if owner:
                owner_names.append("**" + owner.display_name + "**")
                is_owner = True
            else:
                owner_names.append(f"Unknown User (ID: {owner_id})")

        owner_names_str = ", ".join(owner_names)
        if is_owner:
            await ctx.reply(
                f"You have maintainer-level permissions when interacting with Takina. Current users who hold maintainer-level permissions: {owner_names_str}"
            , mention_author=False)
        else:
            await ctx.reply(
                f"You are not a maintainer of Takina. Current users who hold maintainer-level permissions: {owner_names_str}"
            , mention_author=False)

    @commands.command(aliases=["rx"])
    @commands.is_owner()
    async def reload_exts(self, ctx: commands.Context, *args):
        if not args:
            reloaded_extensions = []
            failed_extensions = []

            for ext in extensions:
                try:
                    self._bot.reload_extension(ext)
                    reloaded_extensions.append(ext)
                except Exception as e:
                    failed_extensions.append(f"{ext}: {e}")

            success_message = f"Successfully reloaded all extensions."
            if failed_extensions:
                error_message = (
                    f"\nFailed to reload the following extensions:\n"
                    + "\n".join(failed_extensions)
                )
                await ctx.reply(f"{success_message}{error_message}", mention_author=False)
            else:
                await ctx.reply(success_message, mention_author=False)

        else:
            try:
                extension = args[0]
                self._bot.reload_extension("extensions." + extension)
                await ctx.reply(f"Successfully reloaded `extensions.{extension}`.", mention_author=False)
            except Exception as error:
                await ctx.reply(f"Failed to reload `{extension}`: {error}", mention_author=False)

    @commands.command(alises=["rsc"])
    @commands.is_owner()
    async def reload_slash_command(self, ctx: commands.Context) -> None:
        await ctx.bot.sync_application_commands()
        await ctx.reply("Successfully synced bot application commands.", mention_author=False)

    @commands.command(aliases=["ux"])
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, *args) -> None:
        extension = args[0]
        try:
            self._bot.unload_extension("extensions." + extension)
            await ctx.reply(f"Successfully unloaded `extensions.{extension}`.", mention_author=False)
        except commands.ExtensionNotLoaded:
            await ctx.reply(f"`extensions.{extension}` was already unloaded.", mention_author=False)

    @commands.command(aliases=["lx"])
    @commands.is_owner()
    async def load(self, ctx: commands.Context, *args) -> None:
        extension = args[0]
        try:
            self._bot.load_extension("extensions." + extension)
        except commands.ExtensionAlreadyLoaded:
            await ctx.reply(f"'extensions.{extension}' was already loaded.", mention_author=False)
        await ctx.reply(f"Successfully loaded `extensions.{extension}`.", mention_author=False)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(OwnerUtils(bot))
