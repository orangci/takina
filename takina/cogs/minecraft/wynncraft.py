from takina.libs import lyhelpers, lychecks, lyerrors
from discord.ext import commands
from datetime import datetime
from takina import config
import discord


class Wynncraft(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.hybrid_group(
        name="wynn", aliases=["wynncraft"], description="Wynncraft information commands."
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
        player = await lyhelpers.request(f"https://api.wynncraft.com/v3/player/{username}")

        if not player:
            raise lyerrors.TakinaNotFoundError(
                f"Could not find a Wynncraft member with the username `{username}`."
            )

        characters = await lyhelpers.request(
            f"https://api.wynncraft.com/v3/player/{username}/characters"
        )

        if characters:
            sorted_characters = sorted(
                characters.values(), key=lambda character: character["level"], reverse=True
            )

            character_list = ", ".join(
                f"Lvl {character['level']} {character['reskin'] or character['type'].capitalize()}"
                for character in sorted_characters
            )

        uuid = player.get("uuid")
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
            embed.description = f"-# Last seen <t:{int(datetime.fromisoformat(player.get('lastJoin')).timestamp())}:R>"

        if guild:
            guild_name = guild.get("name")
            guild_prefix = guild.get("prefix")
            guild_rank = guild.get("rank")
            embed.description += f"\n\n> **Guild**: {guild_rank.lower().capitalize()} of [{guild_prefix}] {guild_name}"

        if (rank := player.get("rank")) != "Player":
            embed.description += f"\n> **Rank**: {rank}"

        embed.description += f"\n> **Playtime**: {player.get('playtime')} hours"

        join_date_timestamp = int(datetime.fromisoformat(player.get("firstJoin")).timestamp())
        formatted_join_date = f"<t:{join_date_timestamp}> (<t:{join_date_timestamp}:R>)"
        embed.description += f"\n> **Joined**: {formatted_join_date}"
        embed.description += f"\n> **Mobs killed**: {global_data.get('mobsKilled')}"
        embed.description += f"\n> **Chests opened**: {global_data.get('chestsFound')}"
        embed.description += f"\n> **Quests completed**: {global_data.get('completedQuests')}"
        embed.description += (
            f"\n> **Dungeons completed**: {global_data.get('dungeons', {}).get('total', 0)}"
        )
        if characters:
            embed.description += f"\n> **Characters**: {character_list}"
        embed.description += f"\n> **Raids**: {global_data.get('raids', {}).get('total', 0)}"
        embed.description += f"\n> **Wars**: {global_data.get('wars', 0):}"
        if forum := player.get("forumLink"):
            embed.description += (
                f"\n> **Forum account**: [Linked](https://forums.wynncraft.com/members/{forum}/)"
            )

        if (pvp_kills := pvp.get("kills", 0)) and (pvp_deaths := pvp.get("deaths", 0)):
            embed.description += f"\n> **PVP**: {pvp_kills} kills / {pvp_deaths} deaths"

        await ctx.reply(embed=embed, mention_author=False)

    @wynn.command(
        name="guild", description="Fetch and display a Wynncraft guild's data.", usage="Juniper"
    )
    async def guild(self, ctx: commands.Context, *, guild_name: str):
        guild = await lyhelpers.request(f"https://api.wynncraft.com/v3/guild/{guild_name}")

        if not guild:
            guild = await lyhelpers.request(
                f"https://api.wynncraft.com/v3/guild/prefix/{guild_name.upper()}"
            )

            if not guild:
                raise lyerrors.TakinaNotFoundError("No guild found with that identifier.")

        prefix = guild.get("prefix")
        created_at = int(datetime.fromisoformat(guild.get("created")).timestamp())

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = f"[{prefix}] {guild.get('name')}"
        embed.url = f"https://wynncraft.com/stats/guild/{prefix}"

        embed.description = (
            f"> **Owner(s)**: {', '.join(guild.get('members', {}).get('owner', {}).keys())}\n"
        )
        embed.description += f"> **Created**: <t:{created_at}> (<t:{created_at}:R>)\n"
        embed.description += f"> **Level**: {guild.get('level')} ({guild.get('xpPercent')}% XP)\n"
        embed.description += f"> **Territories controlled**: {guild.get('territories')}\n"
        embed.description += f"> **Wars participated**: {guild.get('wars')}\n"
        embed.description += f"> **Online members**: {guild.get('online')}"
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Wynncraft(bot))
