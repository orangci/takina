from takina.libs import lyerrors, lyhelpers, lychecks
from discord.ext import commands
from takina import config
import asyncio
import discord
import os
import shutil


QALC_PACKAGE = os.getenv("QALC") or shutil.which("qalc")


class Qalc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    async def qalc_expression(self, expr: str) -> str | None:
        assert QALC_PACKAGE is not None
        proc = await asyncio.create_subprocess_exec(
            QALC_PACKAGE, "-t", expr, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, _ = await proc.communicate()
        except asyncio.CancelledError:
            if proc.returncode is None:
                proc.kill()
            await proc.wait()
            raise

        if proc.returncode != 0:
            return None

        return stdout.decode().strip()

    @commands.hybrid_command(
        name="qalc",
        aliases=["calc", "calculate", "qalculate", "qc", "calculator"],
        description="Mathematical calculation evaluation.",
        usage="6 * 7",
    )
    @lychecks.is_user_app()
    async def qalc(self, ctx: commands.Context, *, calculation: str):
        try:
            async with asyncio.timeout(config.QALC_TIMEOUT):
                result = await self.qalc_expression(calculation)
        except TimeoutError:
            raise lyerrors.TakinaError("Calculation timed out.")

        if not result:
            raise lyerrors.TakinaUserInputError("Invalid expression.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{await lyhelpers.fetch_random_emoji()} {result}"
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    if QALC_PACKAGE is None and not config.NIXOS_INSTANCE:
        raise lyerrors.TakinaMissingEnvironmentVariableError(
            "Libqalculate is not installed/available on the system."
        )

    await bot.add_cog(Qalc(bot))
