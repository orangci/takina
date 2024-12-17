import os
import nextcord
from nextcord.ext import commands, application_checks
from nextcord import Interaction, SlashOption, Embed
from motor.motor_asyncio import AsyncIOMotorClient
from __main__ import DB_NAME, EMBED_COLOR
from ..libs.oclib import fetch_random_emoji

MAX_TRIGGERS = 30
MAX_TRIGGER_NAME_LEN = 20
MAX_TRIGGER_LEN = 75
MAX_RESPONSE_LEN = 200

class TriggerResponses(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(os.getenv("MONGO")).get_database(DB_NAME)

    async def get_guild_triggers(self, guild_id: int):
        """Fetch all triggers for a guild."""
        return await self.db.triggers.find_one({"guild_id": guild_id}) or {"guild_id": guild_id, "triggers": {}}

    async def update_guild_triggers(self, guild_id: int, triggers: dict):
        """Update triggers for a guild."""
        await self.db.triggers.update_one(
            {"guild_id": guild_id}, {"$set": {"triggers": triggers}}, upsert=True
        )

    @commands.group(name="trigger", invoke_without_command=True)
    async def trigger(self, ctx: commands.Context):
        """Manage trigger responses."""
        embed = Embed(color=EMBED_COLOR)
        embed.description = "Available subcommands: `add`, `remove`, `list`."
        await ctx.reply(
            embed=embed,
            mention_author=False,
        )

    @commands.has_permissions(manage_server=True)
    @trigger.command(name="add", help="Usage: `trigger add <triggername> \"trigger\" \"trigger response\"`")
    async def add_trigger(self, ctx: commands.Context, name: str, trigger: str, response: str):
        """Add a new trigger response."""
        if len(name) > MAX_TRIGGER_NAME_LEN:
            embed = Embed(color=0xFF0037)
            embed.description = f":x: Trigger name cannot exceed {MAX_TRIGGER_NAME_LEN} characters."
            return await ctx.reply(embed=embed, mention_author=False)

        if len(trigger) > MAX_TRIGGER_LEN:
            embed = Embed(color=0xFF0037)
            embed.description = f":x: Trigger text cannot exceed {MAX_TRIGGER_LEN} characters."
            return await ctx.reply(embed=embed, mention_author=False)

        if len(response) > MAX_RESPONSE_LEN:
            embed = Embed(color=0xFF0037)
            embed.description = f":x: Trigger response text cannot exceed {MAX_RESPONSE_LEN} characters."
            return await ctx.reply(embed=embed, mention_author=False)

        guild_data = await self.get_guild_triggers(ctx.guild.id)
        triggers = guild_data["triggers"]

        if len(triggers) >= MAX_TRIGGERS:
            embed = Embed(color=0xFF0037)
            embed.description = f":x: Maximum of {MAX_TRIGGERS} triggers reached."
            return await ctx.reply(embed=embed, mention_author=False)

        if name in triggers:
            embed = Embed(color=0xFF0037)
            embed.description = f":x: A trigger with the name `{name}` already exists."
            return await ctx.reply(
                embed=embed, mention_author=False
            )

        triggers[name] = {"trigger": trigger, "response": response}
        await self.update_guild_triggers(ctx.guild.id, triggers)
        embed = Embed(color=EMBED_COLOR)
        embed.description = f"✅ Trigger `{name}` added."
        await ctx.reply(embed=embed, mention_author=False)

    @commands.has_permissions(manage_server=True)
    @trigger.command(name="remove", help="Usage: `trigger remove <triggername>`")
    async def remove_trigger(self, ctx: commands.Context, name: str):
        """Remove an existing trigger."""
        guild_data = await self.get_guild_triggers(ctx.guild.id)
        triggers = guild_data["triggers"]

        if name not in triggers:
            embed = Embed(color=0xFF0037)
            embed.description = f":x: No trigger with the name `{name}` exists."
            return await ctx.reply(
                embed=embed, mention_author=False
            )

        del triggers[name]
        await self.update_guild_triggers(ctx.guild.id, triggers)
        embed = Embed(color=EMBED_COLOR)
        embed.description = f"✅ Trigger `{name}` removed."
        await ctx.reply(embed=embed, mention_author=False)

    @trigger.command(name="list")
    async def list_triggers(self, ctx: commands.Context):
        """List all triggers for the guild."""
        guild_data = await self.get_guild_triggers(ctx.guild.id)
        triggers = guild_data["triggers"]

        if not triggers:
            embed = Embed(color=0xFF0037)
            embed.description = ":x: No triggers set for this server."
            return await ctx.reply(embed=embed, mention_author=False)

        embed = Embed(title=f"{await fetch_random_emoji()} Trigger List", color=EMBED_COLOR)
        embed.description = ""
        for name, data in triggers.items():
            embed.description += f"\n- `{name}`:\nTrigger — `{data['trigger']}`\nResponse — `{data['response']}`"
        await ctx.reply(embed=embed, mention_author=False)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_data = await self.get_guild_triggers(message.guild.id)
        triggers = guild_data["triggers"]

        for data in triggers.values():
            if data["trigger"] in message.content:
                await message.channel.send(data["response"])
                break

class SlashTriggerResponses(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(os.getenv("MONGO")).get_database(DB_NAME)

    async def get_guild_triggers(self, guild_id: int):
        """Fetch all triggers for a guild."""
        return await self.db.triggers.find_one({"guild_id": guild_id}) or {"guild_id": guild_id, "triggers": {}}

    async def update_guild_triggers(self, guild_id: int, triggers: dict):
        """Update triggers for a guild."""
        await self.db.triggers.update_one(
            {"guild_id": guild_id}, {"$set": {"triggers": triggers}}, upsert=True
        )

    @nextcord.slash_command(name="trigger", description="Manage trigger responses.")
    async def slash_trigger(self, interaction: Interaction):
        """Base slash command for trigger management."""
        pass

    @application_checks.has_permissions(manage_server=True)
    @slash_trigger.subcommand(name="add")
    async def slash_add_trigger(
        self,
        interaction: Interaction,
        name: str = SlashOption(description="The name of the trigger."),
        trigger: str = SlashOption(description="The text to trigger the response."),
        response: str = SlashOption(description="The response to send when triggered."),
    ):
        """Add a new trigger response."""
        if len(name) > MAX_TRIGGER_NAME_LEN:
            embed = Embed(color=0xFF0037)
            embed.description = f":x: Trigger name cannot exceed {MAX_TRIGGER_NAME_LEN} characters."
            return await interaction.send(embed=embed, ephemeral=True)

        if len(trigger) > MAX_TRIGGER_LEN:
            embed = Embed(color=0xFF0037)
            embed.description = f":x: Trigger text cannot exceed {MAX_TRIGGER_LEN} characters."
            return await interaction.send(embed=embed, ephemeral=True)

        if len(response) > MAX_RESPONSE_LEN:
            embed = Embed(color=0xFF0037)
            embed.description = f":x: Trigger response text cannot exceed {MAX_RESPONSE_LEN} characters."
            return await interaction.send(embed=embed, ephemeral=True)

        guild_data = await self.get_guild_triggers(interaction.guild.id)
        triggers = guild_data["triggers"]

        if len(triggers) >= MAX_TRIGGERS:
            embed = Embed(color=0xFF0037)
            embed.description = f":x: Maximum of {MAX_TRIGGERS} triggers reached."
            return await interaction.send(embed=embed, ephemeral=True)

        if name in triggers:
            embed = Embed(color=0xFF0037)
            embed.description = f":x: A trigger with the name `{name}` already exists."
            return await interaction.send(
                embed=embed, ephemeral=True
            )

        triggers[name] = {"trigger": trigger, "response": response}
        await self.update_guild_triggers(interaction.guild.id, triggers)
        embed = Embed(color=EMBED_COLOR)
        embed.description = f"✅ Trigger `{name}` added."
        await interaction.send(embed=embed, ephemeral=True)

    @application_checks.has_permissions(manage_server=True)
    @slash_trigger.subcommand(name="remove")
    async def slash_remove_trigger(
        self,
        interaction: Interaction,
        name: str = SlashOption(description="The name of the trigger to remove."),
    ):
        """Remove an existing trigger."""
        guild_data = await self.get_guild_triggers(interaction.guild.id)
        triggers = guild_data["triggers"]

        if name not in triggers:
            embed = Embed(color=0xFF0037)
            embed.description = f":x: No trigger with the name `{name}` exists."
            return await interaction.send(
                embed=embed, ephemeral=True
            )

        del triggers[name]
        await self.update_guild_triggers(interaction.guild.id, triggers)
        embed = Embed(color=EMBED_COLOR)
        embed.description = f"✅ Trigger `{name}` removed."
        await interaction.send(embed=embed, ephemeral=True)

    @slash_trigger.subcommand(name="list")
    async def slash_list_triggers(self, interaction: Interaction):
        """List all triggers for the guild."""
        guild_data = await self.get_guild_triggers(interaction.guild.id)
        triggers = guild_data["triggers"]

        if not triggers:
            embed = Embed(color=0xFF0037)
            embed.description = ":x: No triggers set for this server."
            return await interaction.send(
                embed=embed, ephemeral=True
            )

        embed = Embed(title=f"{await fetch_random_emoji()} Trigger List", color=EMBED_COLOR)
        for name, data in triggers.items():
            embed.description += f"\n- `{name}`:\nTrigger — `{data['trigger']}`\nResponse — `{data['response']}`"
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(TriggerResponses(bot))
    bot.add_cog(SlashTriggerResponses(bot))
