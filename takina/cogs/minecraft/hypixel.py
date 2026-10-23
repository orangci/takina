# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyhelpers, lyerrors, lychecks
from contextlib import contextmanager
from collections.abc import Generator
from discord.ext import commands
from urllib.parse import quote
from takina import config
import dataclasses
import discord
import hypixel
import typing

SOCIAL_SITES = {
    "twitter": "https://x.com/{}",
    "instagram": "https://instagram.com/{}",
    "youtube": "https://youtube.com/@{}",
    "twitch": "https://twitch.tv/{}",
    "hypixel_forums": "https://hypixel.net/members/{}",
}


def zero_missing(stats: typing.Any) -> None:
    # seriously wyh the hell would the hypixel api even return none instead of zero though
    # only numeric fields are touched, so text such as a duels title stays None
    hints = typing.get_type_hints(type(stats))

    for field in dataclasses.fields(stats):
        hint = hints[field.name]
        is_number = hint in (int, float) or any(
            arg in (int, float) for arg in typing.get_args(hint)
        )

        if is_number and getattr(stats, field.name) is None:
            setattr(stats, field.name, 0)


def social_link(name: str, value: str) -> str:
    # players type these in game, so they are either a full url or a bare handle
    if value.startswith(("https://", "http://")):
        url = value
    else:
        url = SOCIAL_SITES[name].format(quote(value, safe=""))

    # a stray bracket would end the markdown link early
    return f"[{name}](<{url.translate(str.maketrans('', '', '<>'))}>)"


def accuracy(hits: int, attempts: int) -> str:
    # hypixel.py's ar and mr are hits per miss, like a kdr, so not a percentage
    return f"{hits / attempts:.2%}" if attempts else "0.00%"


@contextmanager
def hypixel_errors() -> Generator[None]:
    try:
        yield
    except hypixel.HypixelException as error:
        raise lyerrors.TakinaError(str(error)) from error


class Hypixel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._client: hypixel.Client | None = None

    async def cog_load(self):
        # one client for the cog, so its response cache lasts between commands
        self._client = hypixel.Client(config.HYPIXEL_API_KEY)

    async def cog_unload(self):
        if self._client is not None:
            await self._client.close()

    @property
    def client(self) -> hypixel.Client:
        assert self._client is not None
        return self._client

    async def fetch_player(self, username: str) -> hypixel.Player:
        with hypixel_errors():
            return await self.client.player(username)

    async def stats_embed(
        self, player: hypixel.Player, heading: str, lines: list[str]
    ) -> discord.Embed:
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = await lyhelpers.fetch_random_emoji() + heading
        embed.description = ""

        if player.last_logout:
            embed.description = f"-# Last seen <t:{int(player.last_logout.timestamp())}:R>\n\n"

        embed.description = lyhelpers.truncate(embed.description + "\n".join(lines), 4096)
        embed.set_footer(text=f"Hypixel User ID: {player.id}")
        return embed

    async def build_hypixel_status_embed(self) -> discord.Embed:
        with hypixel_errors():
            player_count = await self.client.player_count()

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = await lyhelpers.fetch_random_emoji() + "Hypixel Status"
        embed.description = (
            f"Hypixel is up at `hypixel.net` with {player_count:,} players currently online!"
        )
        return embed

    async def build_hypixel_guild_embed(self, guild_name: str) -> discord.Embed:
        with hypixel_errors():
            guild = await self.client.guild_from_name(guild_name)

        created = int(guild.created.timestamp())

        lines = []
        lines.append(f"> **Level**: {guild.level:,}, with {guild.exp:,} guild EXP")
        lines.append(f"> **Created**: <t:{created}:D> (<t:{created}:R>)")
        lines.append(f"> **Members**: {len(guild.members):,}")
        if guild.tag:
            lines.append(f"> **Tag**: [{guild.tag}]")
        if guild.preferred_games:
            lines.append(
                f"> **Preferred Games**: {', '.join(game.clean_name for game in guild.preferred_games)}"
            )
        lines.append(f"> **Publicly Listed**: {'Yes' if guild.publicly_listed else 'No'}")
        lines.append(f"> **Joinable**: {'Yes' if guild.joinable else 'No'}")
        if guild.most_online_players:
            lines.append(f"> **Most Online Players**: {guild.most_online_players:,}")
        if guild.experience_kings:
            lines.append(f"> **Experience Kings**: {guild.experience_kings:,}")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = await lyhelpers.fetch_random_emoji() + guild.name
        embed.description = "\n".join(lines)

        if guild.description:
            embed.description += "\n" + guild.description

        embed.description = lyhelpers.truncate(embed.description, 4096)
        embed.set_footer(text=f"Hypixel Guild ID: {guild.id}")
        return embed

    async def build_hypixel_player_embed(self, username: str) -> discord.Embed:
        player = await self.fetch_player(username)
        bedwars, skywars, duels = player.bedwars, player.skywars, player.duels

        socials = [
            social_link(name, value)
            for name in SOCIAL_SITES
            if (value := getattr(player.socials, name))
        ]
        if player.socials.discord:
            socials.append(f"Discord: {discord.utils.escape_markdown(player.socials.discord)}")

        for stats in (player, bedwars, skywars, duels):
            zero_missing(stats)

        first_join = int(player.first_login.timestamp())

        lines = []
        lines.append(f"> **First joined**: <t:{first_join}:D> (<t:{first_join}:R>)")
        lines.append(
            f"> **Level**: {player.level:,}, with {player.network_exp:,} network EXP and {player.karma:,} karma"
        )
        if player.rank:
            lines.append(f"> **Rank**: {player.rank}")
        if player.most_recent_game:
            lines.append(f"> **Last played**: {player.most_recent_game.clean_name}")
        if socials:
            lines.append(f"> **Socials**: {', '.join(socials)}")
        if len(player.achievements) > 0:
            lines.append(
                f"> **Achievements**: {len(player.achievements):,} ({player.achievement_points:,} achievement points)"
            )
        if bedwars.exp > 0:
            lines.append(
                f"> **Bedwars**: Level {bedwars.level:,} ({bedwars.exp:,} EXP), with {bedwars.beds_broken:,} beds broken, {bedwars.kills:,} kills ({bedwars.final_kills:,} final), {bedwars.deaths:,} deaths ({bedwars.final_deaths:,} final), {bedwars.wins:,} wins ({bedwars.winstreak:,} current winstreak), and {bedwars.losses:,} losses. Ratios: KDR {bedwars.kdr}, FKDR {bedwars.fkdr}, WLR {bedwars.wlr}"
            )
        if skywars.exp > 0:
            lines.append(
                f"> **Skywars**: Level {skywars.level:,} ({skywars.exp:,} EXP), with {skywars.kills:,} kills, {skywars.deaths:,} deaths, {skywars.wins:,} wins ({skywars.winstreak:,} current winstreak), and {skywars.losses:,} losses. Ratios: KDR {skywars.kdr}, WLR {skywars.wlr}"
            )
        if duels.wins > 0:
            lines.append(
                f"> **Duels**: {duels.title or 'No Title'}, with {duels.kills:,} kills, {duels.deaths:,} deaths, {duels.wins:,} wins, {duels.losses:,} losses, and a WLR of {duels.wlr}"
            )

        return await self.stats_embed(player, player.name, lines)

    async def build_hypixel_bedwars_embed(self, username: str) -> discord.Embed:
        player = await self.fetch_player(username)
        bedwars = player.bedwars
        zero_missing(bedwars)

        lines = []
        lines.append(f"> **Level**: {bedwars.level:,} ({bedwars.exp:,} EXP)")
        lines.append(f"> **Coins**: {bedwars.coins:,}")
        lines.append(f"> **Games played**: {bedwars.games:,}")
        lines.append(f"> **Kills**: {bedwars.kills:,} ({bedwars.final_kills:,} final)")
        lines.append(f"> **Deaths**: {bedwars.deaths:,} ({bedwars.final_deaths:,} final)")
        lines.append(
            f"> **Void deaths**: {bedwars.void_deaths:,} ({bedwars.void_final_deaths:,} final)"
        )
        lines.append(
            f"> **Fall deaths**: {bedwars.fall_deaths:,} ({bedwars.fall_final_deaths:,} final)"
        )
        lines.append(f"> **KDR**: {bedwars.kdr}")
        lines.append(f"> **FKDR**: {bedwars.fkdr}")
        lines.append(f"> **Beds broken**: {bedwars.beds_broken:,}")
        lines.append(f"> **Beds lost**: {bedwars.beds_lost:,}")
        lines.append(f"> **BBLR**: {bedwars.bblr}")
        lines.append(f"> **Wins**: {bedwars.wins:,}")
        lines.append(f"> **Losses**: {bedwars.losses:,}")
        lines.append(f"> **WLR**: {bedwars.wlr}")

        if bedwars.winstreak:
            lines.append(f"> **Current winstreak**: {bedwars.winstreak:,}")

        return await self.stats_embed(player, f"{player.name}'s Bedwars Statistics", lines)

    async def build_hypixel_blitz_embed(self, username: str) -> discord.Embed:
        player = await self.fetch_player(username)
        blitz = player.blitz
        zero_missing(blitz)

        lines = []
        lines.append(f"> **Coins**: {blitz.coins:,}")
        lines.append(f"> **Games played**: {blitz.games:,}")
        lines.append(f"> **Kills**: {blitz.kills:,}")
        lines.append(f"> **Deaths**: {blitz.deaths:,}")
        lines.append(f"> **KDR**: {blitz.kdr}")
        lines.append(
            f"> **Wins**: {blitz.wins:,} ({blitz.wins_solo:,} solo, {blitz.wins_team:,} team)"
        )
        lines.append(f"> **WLR**: {blitz.wlr}")
        lines.append(f"> **Chests opened**: {blitz.chests_opened:,}")

        if blitz.arrows_shot > 0:
            lines.append(
                f"> **Archery**: {blitz.arrows_hit:,} hits, {blitz.arrows_shot:,} shots ({accuracy(blitz.arrows_hit, blitz.arrows_shot)} accuracy)"
            )

        return await self.stats_embed(player, f"{player.name}'s Blitz Statistics", lines)

    async def build_hypixel_duels_embed(self, username: str) -> discord.Embed:
        player = await self.fetch_player(username)
        duels = player.duels
        zero_missing(duels)

        lines = []

        if duels.title:
            lines.append(f"> **Title**: {duels.title}")

        lines.append(f"> **Coins**: {duels.coins:,}")
        lines.append(f"> **Kills**: {duels.kills:,}")
        lines.append(f"> **Deaths**: {duels.deaths:,}")
        lines.append(f"> **Wins**: {duels.wins:,}")
        lines.append(f"> **Losses**: {duels.losses:,}")
        lines.append(f"> **WLR**: {duels.wlr}")

        if duels.melee_swings > 0:
            lines.append(
                f"> **Melee**: {duels.melee_hits:,} hits, {duels.melee_swings:,} swings ({accuracy(duels.melee_hits, duels.melee_swings)} accuracy)"
            )

        if duels.arrows_shot > 0:
            lines.append(
                f"> **Archery**: {duels.arrows_hit:,} hits, {duels.arrows_shot:,} shots ({accuracy(duels.arrows_hit, duels.arrows_shot)} accuracy)"
            )

        return await self.stats_embed(player, f"{player.name}'s Duels Statistics", lines)

    async def build_hypixel_murder_mystery_embed(self, username: str) -> discord.Embed:
        player = await self.fetch_player(username)
        murder = player.murder_mystery
        zero_missing(murder)

        lines = []
        lines.append(f"> **Coins**: {murder.coins:,}")
        lines.append(f"> **Games played**: {murder.games:,}")
        lines.append(
            f"> **Wins**: {murder.wins:,} ({murder.murderer_wins:,} murderer, {murder.detective_wins:,} detective)"
        )
        lines.append(f"> **Kills**: {murder.kills:,}")
        lines.append(f"> **Deaths**: {murder.deaths:,}")
        lines.append(f"> **KDR**: {murder.kdr}")
        lines.append(
            f"> **Weapon kills**: {murder.knife_kills:,} knife, {murder.thrown_knife_kills:,} thrown knife, {murder.bow_kills:,} bow"
        )

        return await self.stats_embed(player, f"{player.name}'s Murder Mystery Statistics", lines)

    async def build_hypixel_paintball_embed(self, username: str) -> discord.Embed:
        player = await self.fetch_player(username)
        paintball = player.paintball
        zero_missing(paintball)

        lines = []
        lines.append(f"> **Coins**: {paintball.coins:,}")
        lines.append(f"> **Wins**: {paintball.wins:,}")
        lines.append(f"> **Kills**: {paintball.kills:,}")
        lines.append(f"> **Deaths**: {paintball.deaths:,}")
        lines.append(f"> **KDR**: {paintball.kdr}")
        lines.append(f"> **Killstreaks**: {paintball.killstreaks:,}")
        lines.append(f"> **SKR**: {paintball.skr}")
        lines.append(f"> **Shots fired**: {paintball.shots_fired:,}")

        return await self.stats_embed(player, f"{player.name}'s Paintball Statistics", lines)

    async def build_hypixel_skywars_embed(self, username: str) -> discord.Embed:
        player = await self.fetch_player(username)
        skywars = player.skywars
        zero_missing(skywars)

        lines = []
        lines.append(f"> **Level**: {skywars.level:,} ({skywars.exp:,} EXP)")
        lines.append(f"> **Coins**: {skywars.coins:,}")
        lines.append(f"> **Souls**: {skywars.souls:,}")
        lines.append(f"> **Games played**: {skywars.games:,}")
        lines.append(f"> **Kills**: {skywars.kills:,}")
        lines.append(f"> **Deaths**: {skywars.deaths:,}")
        lines.append(f"> **KDR**: {skywars.kdr}")
        lines.append(f"> **Wins**: {skywars.wins:,}")
        lines.append(f"> **Losses**: {skywars.losses:,}")
        lines.append(f"> **WLR**: {skywars.wlr}")

        if skywars.winstreak:
            lines.append(f"> **Current winstreak**: {skywars.winstreak:,}")

        if skywars.arrows_shot > 0:
            lines.append(
                f"> **Archery**: {skywars.arrows_hit:,} hits, {skywars.arrows_shot:,} shots ({accuracy(skywars.arrows_hit, skywars.arrows_shot)} accuracy)"
            )

        return await self.stats_embed(player, f"{player.name}'s Skywars Statistics", lines)

    async def build_hypixel_uhc_embed(self, username: str) -> discord.Embed:
        player = await self.fetch_player(username)
        uhc = player.uhc
        zero_missing(uhc)

        lines = []
        lines.append(f"> **Level**: {uhc.level:,}")
        lines.append(f"> **Score**: {uhc.score:,}")
        lines.append(f"> **Coins**: {uhc.coins:,}")
        lines.append(f"> **Wins**: {uhc.wins:,}")
        lines.append(f"> **Kills**: {uhc.kills:,}")
        lines.append(f"> **Deaths**: {uhc.deaths:,}")
        lines.append(f"> **KDR**: {uhc.kdr}")
        lines.append(f"> **Heads eaten**: {uhc.heads_eaten:,}")
        lines.append(f"> **Ultimates crafted**: {uhc.ultimates_crafted:,}")

        return await self.stats_embed(player, f"{player.name}'s UHC Statistics", lines)

    @commands.hybrid_group(
        name="hypixel",
        aliases=["hypickle", "hy"],
        description="Base hypixel command, if no subcommand is passed.",
        invoke_without_command=True,
    )
    @lychecks.is_user_app()
    async def hypixel_group(self, ctx: commands.Context):
        await ctx.send_help(ctx.command)

    @hypixel_group.command(name="status", description="Display Hypixel's status.")
    async def hypixel_status(self, ctx: commands.Context):
        await ctx.defer()
        embed = await self.build_hypixel_status_embed()
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel_group.command(
        name="guild",
        aliases=["clan", "team", "club", "gang"],
        description="Display information on a Hypixel guild.",
    )
    async def hypixel_guild(self, ctx: commands.Context, *, guild_name: str):
        await ctx.defer()
        embed = await self.build_hypixel_guild_embed(guild_name)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel_group.command(
        name="player",
        aliases=["member", "user", "profile"],
        description="Display information on a Hypixel member.",
    )
    async def hypixel_player(self, ctx: commands.Context, username: str):
        await ctx.defer()
        embed = await self.build_hypixel_player_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel_group.command(
        name="bedwars",
        aliases=["bwars", "bed", "bw"],
        description="Display information on a Hypixel member's bedwars statistics.",
    )
    async def hypixel_bedwars(self, ctx: commands.Context, username: str):
        await ctx.defer()
        embed = await self.build_hypixel_bedwars_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel_group.command(
        name="blitz", description="Display information on a Hypixel member's blitz statistics."
    )
    async def hypixel_blitz(self, ctx: commands.Context, username: str):
        await ctx.defer()
        embed = await self.build_hypixel_blitz_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel_group.command(
        name="duels",
        aliases=["duel"],
        description="Display information on a Hypixel member's duels statistics.",
    )
    async def hypixel_duels(self, ctx: commands.Context, username: str):
        await ctx.defer()
        embed = await self.build_hypixel_duels_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel_group.command(
        name="murdermystery",
        aliases=["mmystery", "murder_mystery", "mystery", "murder"],
        description="Display information on a Hypixel member's murder mystery statistics.",
    )
    async def hypixel_murder_mystery(self, ctx: commands.Context, username: str):
        await ctx.defer()
        embed = await self.build_hypixel_murder_mystery_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel_group.command(
        name="paintball",
        aliases=["pb", "paint", "pball"],
        description="Display information on a Hypixel member's paintball statistics.",
    )
    async def hypixel_paintball(self, ctx: commands.Context, username: str):
        await ctx.defer()
        embed = await self.build_hypixel_paintball_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel_group.command(
        name="skywars",
        aliases=["swars", "sky", "sw"],
        description="Display information on a Hypixel member's skywars statistics.",
    )
    async def hypixel_skywars(self, ctx: commands.Context, username: str):
        await ctx.defer()
        embed = await self.build_hypixel_skywars_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel_group.command(
        name="uhc", description="Display information on a Hypixel member's UHC statistics."
    )
    async def hypixel_uhc(self, ctx: commands.Context, username: str):
        await ctx.defer()
        embed = await self.build_hypixel_uhc_embed(username)
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    if config.HYPIXEL_API_KEY:
        await bot.add_cog(Hypixel(bot))
    else:
        raise lyerrors.TakinaMissingEnvironmentVariableError(
            "Visit https://developer.hypixel.net for an API key."
        )
