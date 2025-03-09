import nextcord
from nextcord.ext import commands, menus
import os
from __main__ import cogs, cogs_blacklist
from config import *
import subprocess
import importlib
from .libs import oclib


class OwnerUtils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(hidden=True, name="guilds")
    @commands.is_owner()
    async def guilds(self, ctx: commands.Context):
        """Lists all guilds the bot is in, ranked from most members to least."""
        guilds_sorted = sorted(
            self.bot.guilds, key=lambda g: g.member_count, reverse=True
        )
        description = ""
        for guild in guilds_sorted:
            entry = f"\n**{guild.name}**"

            if len(description) + len(entry) > 4096:
                break
            description += entry

        if not description:
            description = "No guilds available to display."

        embed = nextcord.Embed(
            title="Guilds", description=description, color=EMBED_COLOR
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def disable(self, ctx: commands.Context, cmd: str):
        if cmd == "disable":
            await ctx.reply(
                "You cannot disable the disable command.", mention_author=False
            )
        else:
            command = self.bot.get_command(cmd)
            if command is None:
                embed = nextcord.Embed(color=ERROR_COLOR)
                embed.description = "❌ Command not found."
                await ctx.reply(embed=embed, mention_author=False)
                return
            command.enabled = False
            embed = nextcord.Embed(color=EMBED_COLOR)
            embed.description = f"✅ Successfully disabled `{command}`."
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def enable(self, ctx: commands.Context, cmd: str):
        if cmd == "disable":
            await ctx.reply(
                "You cannot enable the enable command.", mention_author=False
            )
        else:
            command = self.bot.get_command(cmd)
            if command is None:
                embed = nextcord.Embed(color=ERROR_COLOR)
                embed.description = "❌ Command not found."
                await ctx.reply(embed=embed, mention_author=False)
                return
            command.enabled = True
            embed = nextcord.Embed(color=EMBED_COLOR)
            embed.description = f"✅ Successfully enabled `{command}`."
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(hidden=True, aliases=["maintainer", "perms"])
    async def owner(self, ctx: commands.Context):
        owner_names = []
        for owner_id in self.bot.owner_ids:
            owner = self.bot.get_user(owner_id) or await self.bot.fetch_user(owner_id)
            if owner:
                owner_names.append("**" + owner.display_name + "**")
            else:
                owner_names.append(f"Unknown User (ID: {owner_id})")

        is_owner = await self.bot.is_owner(ctx.author)
        owner_names_str = ", ".join(owner_names)
        if is_owner:
            embed = nextcord.Embed(color=EMBED_COLOR)
            embed.description = f"You have maintainer level permissions when interacting with {BOT_NAME}. Current users who hold maintainer level permissions: {owner_names_str}"
            await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = nextcord.Embed(color=EMBED_COLOR)
            embed.description = f"You are not a maintainer of {BOT_NAME}. Current users who hold maintainer-level permissions: {owner_names_str}"
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(hidden=True, aliases=["rx"])
    @commands.is_owner()
    async def reload_exts(self, ctx: commands.Context, *args):
        importlib.reload(oclib)

        if not args:
            failed_cogs = []
            for cog in list(
                self.bot.extensions.keys()
            ):  # Iterate over loaded extensions
                try:
                    self.bot.reload_extension(cog)
                except Exception as e:
                    failed_cogs.append(f"{cog}: {e}")

            if failed_cogs:
                error_message = (
                    f"❌ Reloaded all except the following cogs:\n\n"
                    + "\n> ".join(failed_cogs)
                )
                embed = nextcord.Embed(color=ERROR_COLOR, description=error_message)
                await ctx.reply(embed=embed, mention_author=False)
            else:
                embed = nextcord.Embed(
                    color=EMBED_COLOR, description="✅ Successfully reloaded all cogs."
                )
                await ctx.reply(embed=embed, mention_author=False)

        else:
            cog = args[0]
            full_cog_name = f"cogs.{cog}" if not cog.startswith("cogs.") else cog

            if full_cog_name in self.bot.extensions:
                try:
                    self.bot.reload_extension(full_cog_name)
                    embed = nextcord.Embed(
                        color=EMBED_COLOR,
                        description=f"✅ Successfully reloaded `{full_cog_name}`.",
                    )
                    await ctx.reply(embed=embed, mention_author=False)
                except Exception as e:
                    embed = nextcord.Embed(
                        color=ERROR_COLOR,
                        description=f"❌ Failed to reload `{full_cog_name}`: {e}",
                    )
                    await ctx.reply(embed=embed, mention_author=False)
            else:
                embed = nextcord.Embed(
                    color=ERROR_COLOR,
                    description=f"❌ Cog `{full_cog_name}` is not loaded.",
                )
                await ctx.reply(embed=embed, mention_author=False)

    @commands.command(hidden=True, aliases=["rsc"])
    @commands.is_owner()
    async def reload_slash_command(self, ctx: commands.Context) -> None:
        await ctx.bot.sync_application_commands()
        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = "✅ Successfully synced bot application commands."
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(hidden=True, aliases=["ux"])
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, *args) -> None:
        cog = args[0]
        try:
            self.bot.unload_extension("cogs." + cog)
            embed = nextcord.Embed(color=EMBED_COLOR)
            embed.description = f"✅ Successfully unloaded `cogs.{cog}`."
            await ctx.reply(embed=embed, mention_author=False)
        except commands.ExtensionNotLoaded:
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = f"❌ `cogs.{cog}` was already unloaded."
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(hidden=True, aliases=["lx"])
    @commands.is_owner()
    async def load(self, ctx: commands.Context, *args) -> None:
        cog = args[0]
        try:
            self.bot.load_extension("cogs." + cog)
        except commands.ExtensionNotLoaded:
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = f"❌ `cogs.{cog}` was already loaded."
            await ctx.reply(embed=embed, mention_author=False)
        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = f"✅ Successfully loaded `cogs.{cog}`."
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def pull(self, ctx: commands.Context):
        current_dir = os.getcwd()

        def run_git_pull(directory):
            try:
                result = subprocess.run(
                    ["git", "pull"],
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return result.stdout
            except subprocess.CalledProcessError as e:
                return e.stderr

        current_dir_result = run_git_pull(current_dir)

        embed = nextcord.Embed()

        if "Already up to date." in current_dir_result:
            # No changes
            embed.color = ERROR_COLOR
            embed.description = ":x: I'm already up to date with upstream."
        elif "Updating" in current_dir_result:
            # Successfully pulled
            modified = []
            created = []
            deleted = []
            commit_id = None

            for line in current_dir_result.splitlines():
                if line.startswith("Updating"):
                    commit_id = line.split("..")[-1].strip()  # Extract latest commit ID
                if line.startswith("   "):  # Parse files from git output
                    if "modified:" in line:
                        modified.append(line.split("modified:")[1].strip())
                    elif "create mode" in line:
                        created.append(line.split("create mode")[1].strip())
                    elif "delete mode" in line:
                        deleted.append(line.split("delete mode")[1].strip())

            embed.color = EMBED_COLOR
            embed.description = (
                "✅ Successfully pulled changes from upstream git repository."
            )

            if commit_id:
                embed.set_footer(text=f"Commit ID: {commit_id}")
        else:
            # Error occurred
            embed.color = ERROR_COLOR
            embed.description = (
                f":x: An error occurred:\n```\n{current_dir_result.strip()}\n```"
            )

        # Send the embed
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def send(
        self,
        ctx: commands.Context,
        channel: nextcord.TextChannel = None,
        *,
        message: str,
    ):
        if channel and message:
            await channel.send(message)
        elif message:
            await ctx.send(message)
        else:
            raise commands.UserInputError

    @nextcord.slash_command(name="send", description="Maintainer only command.")
    async def slash_send(
        self,
        interaction: nextcord.Interaction,
        message: str = nextcord.SlashOption(
            name="message",
            description="The message to send.",
            required=True,
        ),
        channel: nextcord.TextChannel = nextcord.SlashOption(
            name="channel",
            description="The channel to send the message to (optional).",
            required=False,
        ),
    ) -> None:
        if interaction.user.id not in self.bot.owner_ids:
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = ":x: You are not authorized to use this command."
            await interaction.send(embed=embed, ephemeral=True)
            return

        target_channel = channel or interaction.channel
        await target_channel.send(message)
        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = f"✅ Successfully sent message in {target_channel.mention}."
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(OwnerUtils(bot))
