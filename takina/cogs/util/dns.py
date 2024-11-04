"""
BSD 3-Clause License

Copyright (c) 2024 - present, MaskDuck

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# code has been modified and is not the original code from MaskDuck

from __future__ import annotations

import nextcord
from dns import resolver as _dnsresolver
from nextcord.ext import commands
from __main__ import EMBED_COLOR
from ..libs.oclib import *


def construct_embed(url: str, full_answer: str):
    return nextcord.Embed(
        title=f"DNS Records for {url}",
        description=full_answer,
        color=EMBED_COLOR,
    )


class DNS(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot: commands.Bot = bot

    @commands.command(
        aliases=["dns"],
        help="Fetches DNS records for a domain. \nUsage: `dig <URL>`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def dig(self, ctx: commands.Context, url: str):
        record_types = ["A", "CNAME", "AAAA", "MX", "TXT", "SRV", "NS"]
        full_answer = ""

        for record_type in record_types:
            try:
                answers = _dnsresolver.resolve(url, record_type)
                records = "\n".join([str(ans) for ans in answers])
                if records:
                    emoji = await fetch_random_emoji()
                    full_answer += (
                        f"{emoji} **{record_type} Records**\n```{records}```\n"
                    )
            except _dnsresolver.NoAnswer:
                continue
            except _dnsresolver.NXDOMAIN:
                error_embed = nextcord.Embed(color=0xFF0037)
                error_embed.description = f"❌ Domain '{url}' does not exist."
                await ctx.reply(embed=error_embed, mention_author=False)
                return

        if full_answer:
            await ctx.reply(
                embed=construct_embed(url, full_answer), mention_author=False
            )
        else:
            error_embed = nextcord.Embed(color=0xFF0037)
            error_embed.description = f"❌ No records found for {url}."
            await ctx.reply(embed=error_embed, mention_author=False)

    @nextcord.slash_command(name="dig", description="Dig an URL for its DNS records.")
    async def dig_slash(
        self,
        interaction: nextcord.Interaction,
        url: str = nextcord.SlashOption(
            description="The URL to dig for DNS records. Be sure to remove http or https://",
            required=True,
        ),
    ) -> None:
        record_types = ["A", "CNAME", "AAAA", "MX", "TXT", "SRV", "NS"]
        full_answer = ""

        for record_type in record_types:
            try:
                answers = _dnsresolver.resolve(url, record_type)
                records = "\n".join([str(ans) for ans in answers])
                if records:
                    emoji = await fetch_random_emoji()
                    full_answer += (
                        f"{emoji} **{record_type} Records**\n```{records}```\n"
                    )
            except _dnsresolver.NoAnswer:
                continue
            except _dnsresolver.NXDOMAIN:
                error_embed = nextcord.Embed(color=0xFF0037)
                error_embed.description = f"❌ Domain '{url}' does not exist."
                await ctx.reply(embed=error_embed, mention_author=False)
                await interaction.send(embed=embed, ephemeral=True)
                return

        if full_answer:
            await interaction.send(
                embed=construct_embed(url, full_answer), ephemeral=True
            )
        else:
            await interaction.send(f"No records found for {url}.", ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(DNS(bot))
