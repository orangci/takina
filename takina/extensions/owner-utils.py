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
            await ctx.send("You cannot disable the disable command.")
        else:
            command = self._bot.get_command(command)
            if command is None:
                await ctx.send("Command not found.")
                return
            command.enabled = not command.enabled
            await ctx.send(f"Successfully disabled {command}.")

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
            await ctx.send(
                f"You have maintainer-level permissions when interacting with Takina. Current users who hold maintainer-level permissions: {owner_names_str}"
            )
        else:
            await ctx.send(
                f"You are not a maintainer of Takina. Current users who hold maintainer-level permissions: {owner_names_str}"
            )

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
                await ctx.send(f"{success_message}{error_message}")
            else:
                await ctx.send(success_message)

        else:
            try:
                extension = args[0]
                self._bot.reload_extension("extensions." + extension)
                await ctx.send(f"Successfully reloaded `extensions.{extension}`.")
            except Exception as error:
                await ctx.send(f"Failed to reload `{extension}`: {error}")

    @commands.command(alises=["rsc"])
    @commands.is_owner()
    async def reload_slash_command(self, ctx: commands.Context) -> None:
        await ctx.bot.sync_application_commands()
        await ctx.send("Successfully synced bot application commands.")

    @commands.command(aliases=["ux"])
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, *args) -> None:
        extension = args[0]
        try:
            self._bot.unload_extension("extensions." + extension)
            await ctx.send(f"Successfully unloaded `extensions.{extension}`.")
        except commands.ExtensionNotLoaded:
            await ctx.send(f"`extensions.{extension}` was already unloaded.")

    @commands.command(aliases=["lx"])
    @commands.is_owner()
    async def load(self, ctx: commands.Context, *args) -> None:
        extension = args[0]
        try:
            self._bot.load_extension("extensions." + extension)
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f"'extensions.{extension}' was already loaded.")
        await ctx.send(f"Successfully loaded `extensions.{extension}`.")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(OwnerUtils(bot))
