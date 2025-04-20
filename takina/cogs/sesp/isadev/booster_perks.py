# SPDX-License-Identifier: AGPL-3.0-or-later
import nextcord
from nextcord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
from config import *
from .libs.lib import *


class CustomRoleManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(MONGO_URI).get_database(DB_NAME)

    async def user_has_bypass(self, guild_id: int, user_id: int):
        """Check if a user has been granted a boost bypass by an admin."""
        result = await self.db.bypass.find_one(
            {"guild_id": guild_id, "user_id": user_id}
        )
        return bool(result)

    async def set_bypass(self, guild_id: int, user_id: int, bypass: bool):
        """Set or remove bypass for a user."""
        if bypass:
            await self.db.bypass.update_one(
                {"guild_id": guild_id, "user_id": user_id},
                {"$set": {"bypass": True}},
                upsert=True,
            )
        else:
            await self.db.bypass.delete_one({"guild_id": guild_id, "user_id": user_id})

    async def get_custom_role(self, guild: nextcord.Guild, user: nextcord.Member):
        """Retrieve the user's custom role if they have one."""
        result = await self.db.custom_roles.find_one(
            {"guild_id": guild.id, "user_id": user.id}
        )
        if result:
            return guild.get_role(result["role_id"])
        return None

    async def create_custom_role(self, guild: nextcord.Guild, user: nextcord.Member):
        """Create a custom role for the user."""
        # Create the new role first without specifying position
        new_role = await guild.create_role(name=f"{user.name}'s boostrole")
        await user.add_roles(new_role)

        # Adjust the role position after creation
        position_role = guild.get_role(POSITION_ROLE_ID)
        if position_role:
            await new_role.edit(position=position_role.position - 1)

        # Save the role in the database
        await self.db.custom_roles.update_one(
            {"guild_id": guild.id, "user_id": user.id},
            {"$set": {"role_id": new_role.id}},
            upsert=True,
        )
        return new_role

    async def delete_custom_role(self, guild: nextcord.Guild, user: nextcord.Member):
        """Delete the user's custom role if it exists."""
        custom_role = await self.get_custom_role(guild, user)
        if custom_role:
            await custom_role.delete()
            await self.db.custom_roles.delete_one(
                {"guild_id": guild.id, "user_id": user.id}
            )

    @commands.Cog.listener()
    async def on_member_update(self, before: nextcord.Member, after: nextcord.Member):
        """Check if a user stopped boosting and delete their custom role if they don't have bypass."""
        if before.guild.id != after.guild.id:
            return

        booster_role = nextcord.utils.get(after.guild.roles, id=BOOSTER_ROLE_ID)
        if booster_role not in after.roles and booster_role in before.roles:
            if not await self.user_has_bypass(after.guild.id, after.id):
                await self.delete_custom_role(after.guild, after)

    @commands.group(invoke_without_command=True)
    @is_in_guild()
    async def boostrole(self, ctx: commands.Context):
        """Group of commands to manage your custom role."""
        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = "Available subcommands: `create`, `name`, `colour`, `icon`."
        await ctx.reply(embed=embed, mention_author=False)

    @boostrole.command()
    @is_in_guild()
    @commands.has_permissions(administrator=True)
    async def bypass(self, ctx: commands.Context, user: nextcord.Member, bypass: bool):
        """Grant or remove a boost bypass for a user. Usage: `boostrole bypass @member true/false`."""
        await self.set_bypass(ctx.guild.id, user.id, bypass)
        status = "granted" if bypass else "revoked"
        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"✅ Booster role requirement bypass {status} for {user.mention}."
        )
        await ctx.reply(embed=embed, mention_author=False)

    @boostrole.command(name="create")
    @is_in_guild()
    async def create_custom_role_command(self, ctx: commands.Context):
        """Create a custom role for the user. Usage: `boostrole create`. Use `boostrole name`, `boostrole colour #ffffff`, and `boostrole icon icon_url` to set the name, colour, and icon respectively."""
        # Check if the user already has a custom role
        if await self.get_custom_role(ctx.guild, ctx.author):
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = ":x: You already have a custom role."
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Check if the user is a booster or has bypass
        booster_role = nextcord.utils.get(ctx.guild.roles, id=BOOSTER_ROLE_ID)
        if booster_role not in ctx.author.roles and not await self.user_has_bypass(
            ctx.guild.id, ctx.author.id
        ):
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = (
                ":x: You must be boosting the server to create a custom role."
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        new_role = await self.create_custom_role(ctx.guild, ctx.author)
        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = (
            f":white_check_mark: Your custom role {new_role.mention} has been created!"
        )
        await ctx.reply(embed=embed, mention_author=False)

    @boostrole.command(name="name")
    @is_in_guild()
    async def set_custom_role_name(self, ctx: commands.Context, *, name: str):
        """Set the name of the user's custom role. Usage: `boostrole name nerd`."""
        custom_role = await self.get_custom_role(ctx.guild, ctx.author)
        if custom_role is None:
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = ":x: You don't have a custom role. Please create one first by running `boostrole create`."
            await ctx.reply(embed=embed, mention_author=False)
            return

        await custom_role.edit(name=name)
        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = f":white_check_mark: Your custom role {custom_role.mention} has been renamed to **{name}**."
        await ctx.reply(embed=embed, mention_author=False)

    @boostrole.command(name="colour", aliases=["color"])
    @is_in_guild()
    async def set_custom_role_colour(
        self, ctx: commands.Context, colour: nextcord.Colour
    ):
        """Set the colour of the user's custom role. Usage: `boostrole colour #ffaa00`."""
        custom_role = await self.get_custom_role(ctx.guild, ctx.author)
        if custom_role is None:
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = ":x: You don't have a custom role."
            await ctx.reply(embed=embed, mention_author=False)
            return

        await custom_role.edit(colour=colour)
        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"✅ Your custom role colour has been changed to **{colour}**."
        )
        await ctx.reply(embed=embed, mention_author=False)

    @boostrole.command(name="icon")
    @is_in_guild()
    async def set_custom_role_icon(self, ctx: commands.Context, icon: str = None):
        """Set the icon of the user's custom role. Usage: `boostrole icon` with an attached image."""
        custom_role = await self.get_custom_role(ctx.guild, ctx.author)

        if custom_role is None:
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = ":x: You don't have a custom role."
            await ctx.reply(embed=embed, mention_author=False)
            return

        if icon and not ctx.message.attachments:
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = ":x: You must attach the icon file to your command in order for the command to work."
            await ctx.reply(embed=embed, mention_author=False)

        if ctx.message.attachments:
            icon = ctx.message.attachments[0]

        if not icon:
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = (
                ":x: You need to provide a valid URL or an image attachment."
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        try:
            await custom_role.edit(icon=icon)
            embed = nextcord.Embed(color=EMBED_COLOR)
            embed.description = "✅ Your custom role icon has been updated."
            await ctx.reply(embed=embed, mention_author=False)
        except nextcord.HTTPException as e:
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = f":x: Failed to update the role icon: {str(e)}"
            await ctx.reply(embed=embed, mention_author=False)


def setup(bot: commands.Bot):
    bot.add_cog(CustomRoleManager(bot))
