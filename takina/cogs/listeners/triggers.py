from takina.libs import lyerrors, lychecks, lyhelpers
from takina import config, database, models
from discord.ext import commands
from takina.libs import lyviews
import discord

MAX_TRIGGERS = 30
MAX_TRIGGER_NAME_LEN = 20
MAX_TRIGGER_LEN = 75
MAX_RESPONSE_LEN = 200


class TriggerResponses(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def get_guild_triggers(self, guild_id: int) -> models.TriggerResponsesModel:
        settings = await database.get(models.TriggerResponsesModel, guild_id=guild_id)
        if settings is None:
            settings = models.TriggerResponsesModel(guild_id=guild_id)
            await database.save(settings)

        return settings

    @commands.hybrid_group(
        name="trigger", description="Manage trigger responses.", invoke_without_command=True
    )
    @lychecks.guild_only()
    async def trigger(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @trigger.command(
        name="add",
        description="Add a new trigger response.",
        usage='r1999 "reverse: 1999" "Reverse: 1999 is PEAK"',
    )
    @lychecks.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def add_trigger(
        self, ctx: commands.Context, name: str, trigger: str, response: str
    ) -> None:
        assert ctx.guild is not None

        if len(name) > MAX_TRIGGER_NAME_LEN:
            raise lyerrors.TakinaUserInputError(
                f"Trigger name cannot exceed {MAX_TRIGGER_NAME_LEN} characters."
            )

        if len(trigger) > MAX_TRIGGER_LEN:
            raise lyerrors.TakinaUserInputError(
                f"Trigger text cannot exceed {MAX_TRIGGER_LEN} characters."
            )

        if len(response) > MAX_RESPONSE_LEN:
            raise lyerrors.TakinaUserInputError(
                f"Trigger response text cannot exceed {MAX_RESPONSE_LEN} characters."
            )

        settings = await self.get_guild_triggers(ctx.guild.id)

        for trigger_data in settings.triggers.values():
            if trigger_data["trigger"] == trigger:
                raise lyerrors.TakinaError(f"A trigger with the text `{trigger}` already exists.")

        if len(settings.triggers) >= MAX_TRIGGERS:
            raise lyerrors.TakinaError(f"Maximum of {MAX_TRIGGERS} triggers reached.")

        if name in settings.triggers:
            raise lyerrors.TakinaError(f"A trigger with the name `{name}` already exists.")

        settings.triggers[name] = {"trigger": trigger, "response": response}
        await database.save(settings)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Trigger `{name}` added."
        await ctx.reply(embed=embed, mention_author=False)

    @trigger.command(
        name="remove",
        aliases=["delete", "rm"],
        description="Remove an existing trigger.",
        usage="r1999",
    )
    @lychecks.has_permissions(manage_channels=True)
    @lychecks.guild_only()
    async def remove_trigger(self, ctx: commands.Context, name: str) -> None:
        assert ctx.guild is not None

        settings = await self.get_guild_triggers(ctx.guild.id)
        if name not in settings.triggers:
            raise lyerrors.TakinaError(f"No trigger with the name `{name}` exists.")

        del settings.triggers[name]
        await database.save(settings)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{config.emojis.SUCCESS} Trigger `{name}` removed."
        await ctx.reply(embed=embed, mention_author=False)

    @trigger.command(name="list", description="List all triggers for the server.")
    @lychecks.guild_only()
    async def list_triggers(self, ctx: commands.Context) -> None:
        assert ctx.guild is not None

        settings = await self.get_guild_triggers(ctx.guild.id)
        if not settings.triggers:
            raise lyerrors.TakinaError("No triggers are set for this server.")

        description = ""
        for name, data in settings.triggers.items():
            description += f"\n- `{name}`:\nTrigger — {data['trigger']}"
            description += f"\nResponse — {data['response']}"

        title = f"{await lyhelpers.fetch_random_emoji()}Trigger List"

        if len(description) > 4096:
            embeds = []
            current = ""

            for line in description.splitlines():
                if current and len(current) + len(line) + 1 > 4096:
                    embed = discord.Embed(title=title, colour=config.EMBED_COLOUR)
                    embed.description = current
                    embeds.append(embed)
                    current = ""

                current += f"\n{line}" if current else line

            if current:
                embed = discord.Embed(title=title, colour=config.EMBED_COLOUR)
                embed.description = current
                embeds.append(embed)

            paginator = lyviews.PaginatorView(ctx.author, embeds)
            await ctx.reply(embed=embeds[0], view=paginator, mention_author=False)
            return

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = title
        embed.description = description
        await ctx.reply(embed=embed, mention_author=False)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        prefixes = await self._bot.get_prefix(message)
        if isinstance(prefixes, str):
            prefixes = [prefixes]

        if any(message.content.startswith(prefix) for prefix in prefixes):
            return

        settings = await database.get(models.TriggerResponsesModel, guild_id=message.guild.id)
        if not settings:
            return

        for data in settings.triggers.values():
            if data["trigger"].lower() in message.content.lower():
                await message.channel.send(data["response"])
                return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TriggerResponses(bot))
