# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors, lyhelpers, lychecks
from discord.ext import commands
from urllib.parse import quote
from takina import config
import discord


class MinecraftServerStatus(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.hybrid_command(
        description="Display a Minecraft server's status.",
        usage="hypixel.net",
        aliases=["mcserver"],
    )
    @lychecks.is_user_app()
    async def mcstatus(self, ctx: commands.Context, *, server_name: commands.Range[str, 1, 255]):
        await ctx.defer()

        # the colon stays, as addresses may carry a port
        address = quote(server_name.strip(), safe=":")
        data = await lyhelpers.request(
            f"https://api.mcstatus.io/v2/status/java/{address}",
            not_found="Server not found or is offline.",
        )

        if not data or not data.get("online"):
            raise lyerrors.TakinaNotFoundError("Server not found or is offline.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = lyhelpers.truncate(
            await lyhelpers.fetch_random_emoji() + (data.get("host") or server_name), 256
        )
        embed.set_image(url=f"https://api.mcstatus.io/v2/widget/java/{address}")
        embed.description = ""

        if data.get("version"):
            embed.description += f"-# {data['version']['name_clean']} (Java)"
        if motd := (data.get("motd") or {}).get("clean"):
            # a backtick in the motd would close the code block early
            embed.description += (
                f"\n\n**MOTD**:\n```{lyhelpers.truncate(motd.replace('`', "'"), 1000)}```"
            )

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(MinecraftServerStatus(bot))
