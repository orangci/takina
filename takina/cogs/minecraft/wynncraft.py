# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyhelpers, lychecks, lyerrors
from discord.ext import commands
from urllib.parse import quote
from datetime import datetime
from takina import config
import discord


def discord_timestamp(value: str | None, style: str = "R") -> str:
    if not value:
        return "Unknown"

    return f"<t:{int(datetime.fromisoformat(value).timestamp())}:{style}>"


class Wynncraft(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.hybrid_group(
        name="wynn",
        aliases=["wynncraft"],
        description="Wynncraft information commands.",
        invoke_without_command=True,
    )
    @lychecks.is_user_app()
    async def wynn(self, ctx: commands.Context):
        await ctx.send_help(ctx.command)

    @wynn.command(
        name="player",
        aliases=["member", "user"],
        description="Fetch and display a Wynncraft player's data.",
        usage="orangci",
    )
    async def player(self, ctx: commands.Context, username: str):
        await ctx.defer()

        player = await lyhelpers.request(
            f"https://api.wynncraft.com/v3/player/{quote(username, safe='')}",
            not_found=f"Could not find a Wynncraft member with the username `{username}`.",
        )

        if not player:
            raise lyerrors.TakinaNotFoundError(
                f"Could not find a Wynncraft member with the username `{username}`."
            )

        # a name several players have used gets a 300 listing them instead of a player
        if "uuid" not in player:
            raise lyerrors.TakinaUserInputError(
                f"Several Wynncraft players have gone by `{username}`. Try their UUID instead."
            )

        uuid = player["uuid"]

        try:
            characters = await lyhelpers.request(
                f"https://api.wynncraft.com/v3/player/{uuid}/characters"
            )
        except lyerrors.TakinaNotFoundError:
            # characters are optional; the player embed works without them
            characters = None

        if characters:
            sorted_characters = sorted(
                characters.values(), key=lambda character: character.get("level", 0), reverse=True
            )

            character_list = ", ".join(
                f"Lvl {character.get('level', 0)} {character.get('reskin') or str(character.get('type', '')).capitalize()}"
                for character in sorted_characters
            )

        guild = player.get("guild")

        global_data = player.get("globalData", {})
        pvp = global_data.get("pvp", {})

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = player.get("username")
        embed.url = f"https://wynncraft.com/stats/player/{uuid}"
        embed.set_thumbnail(url=f"https://visage.surgeplay.com/bust/256/{uuid}.webp")
        if player.get("veteran"):
            embed.set_footer(text="This user is a veteran.")

        if player.get("online"):
            embed.description = f"-# Currently online on {player.get('server')}."
        else:
            embed.description = f"-# Last seen {discord_timestamp(player.get('lastJoin'))}"

        if guild:
            guild_name = guild.get("name")
            guild_prefix = guild.get("prefix")
            guild_rank = str(guild.get("rank") or "Member").capitalize()
            embed.description += f"\n\n> **Guild**: {guild_rank} of [{guild_prefix}] {guild_name}"

        if (rank := player.get("rank")) not in ("Player", None):
            embed.description += f"\n> **Rank**: {rank}"

        embed.description += f"\n> **Playtime**: {player.get('playtime')} hours"

        first_join = player.get("firstJoin")
        embed.description += f"\n> **Joined**: {discord_timestamp(first_join, 'f')} ({discord_timestamp(first_join)})"
        embed.description += f"\n> **Mobs killed**: {global_data.get('mobsKilled')}"
        embed.description += f"\n> **Chests opened**: {global_data.get('chestsFound')}"
        embed.description += f"\n> **Quests completed**: {global_data.get('completedQuests')}"
        embed.description += (
            f"\n> **Dungeons completed**: {global_data.get('dungeons', {}).get('total', 0)}"
        )
        if characters:
            embed.description += f"\n> **Characters**: {character_list}"
        embed.description += f"\n> **Raids**: {global_data.get('raids', {}).get('total', 0)}"
        embed.description += f"\n> **Wars**: {global_data.get('wars', 0)}"
        if forum := player.get("forumLink"):
            embed.description += (
                f"\n> **Forum account**: [Linked](https://forums.wynncraft.com/members/{forum}/)"
            )

        if (pvp_kills := pvp.get("kills", 0)) and (pvp_deaths := pvp.get("deaths", 0)):
            embed.description += f"\n> **PVP**: {pvp_kills} kills / {pvp_deaths} deaths"

        embed.description = lyhelpers.truncate(embed.description, 4096)
        await ctx.reply(embed=embed, mention_author=False)

    @wynn.command(
        name="guild", description="Fetch and display a Wynncraft guild's data.", usage="Juniper"
    )
    async def guild(self, ctx: commands.Context, *, guild_name: str):
        await ctx.defer()

        try:
            guild = await lyhelpers.request(
                f"https://api.wynncraft.com/v3/guild/{quote(guild_name, safe='')}"
            )
        except lyerrors.TakinaNotFoundError:
            # not a guild name, so try it as a prefix
            guild = None

        if not guild:
            guild = await lyhelpers.request(
                f"https://api.wynncraft.com/v3/guild/prefix/{quote(guild_name.upper(), safe='')}",
                not_found="No guild found with that identifier.",
            )

            if not guild:
                raise lyerrors.TakinaNotFoundError("No guild found with that identifier.")

        prefix = guild.get("prefix")
        created = guild.get("created")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = f"[{prefix}] {guild.get('name')}"
        embed.url = f"https://wynncraft.com/stats/guild/{prefix}"

        embed.description = (
            f"> **Owner(s)**: {', '.join(guild.get('members', {}).get('owner', {}).keys())}\n"
        )
        embed.description += (
            f"> **Created**: {discord_timestamp(created, 'f')} ({discord_timestamp(created)})\n"
        )
        embed.description += f"> **Level**: {guild.get('level')} ({guild.get('xpPercent')}% XP)\n"
        embed.description += f"> **Territories controlled**: {guild.get('territories')}\n"
        embed.description += f"> **Wars participated**: {guild.get('wars')}\n"
        embed.description += f"> **Online members**: {guild.get('online')}"
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Wynncraft(bot))
