from takina import config, database, models
from takina.libs import lychecks
from discord.ext import commands
import discord


class Prefix(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.guild_only()
    @lychecks.has_permissions(administrator=True)
    @commands.hybrid_command(
        name="prefix", description=f"Set a custom prefix for {config.BOT_NAME}"
    )
    async def set_prefix(self, ctx: commands.Context, new_prefix: str):
        assert ctx.guild is not None

        prefix = await database.get(models.PrefixModel, guild_id=ctx.guild.id)

        if prefix is None:
            prefix = models.PrefixModel(guild_id=ctx.guild.id, prefix=new_prefix)
        else:
            prefix.prefix = new_prefix

        await database.save(prefix)

        embed = discord.Embed(
            color=config.EMBED_COLOR, description=f"✅ Prefix updated to: `{new_prefix}`"
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Prefix(bot))
