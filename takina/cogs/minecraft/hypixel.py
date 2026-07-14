# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from nextcord.ext import commands
from ..libs import oclib
import nextcord
import hypixel
import config


class Hypixel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def sanitise_stats(self, obj):
        # this function is to make values that are None zero so that :, works on them
        # seriously wyh the hell would the hypixel api even return none instead of zero though
        # that is SO annoying
        for key, value in vars(obj).items():
            if value is None:
                setattr(obj, key, 0)

    async def build_hypixel_status_embed(self):
        client = hypixel.Client(config.HYPIXEL_API_KEY)
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        async with client:
            try:
                embed.title = await oclib.fetch_random_emoji() + "Hypixel Status"
                embed.description = f"Hypixel is up at `hypixel.net` with {await client.player_count():,} players currently online!"
            except hypixel.HypixelException as error:
                embed.description = f":x: {error}"
                embed.color = config.ERROR_COLOR
                embed.title = None
        return embed

    async def build_hypixel_guild_embed(self, guild_name: str) -> nextcord.Embed:
        client = hypixel.Client(config.HYPIXEL_API_KEY)
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        async with client:
            try:
                guild = await client.guild_from_name(guild_name)

                embed.title = await oclib.fetch_random_emoji() + guild.name

                created = str(int(guild.created.timestamp()))

                lines = []

                lines.append(f"> **Level**: {guild.level:,}, with {guild.exp:,} guild EXP")
                lines.append(f"> **Created**: <t:{created}:D> (<t:{created}:R>)")
                lines.append(f"> **Members**: {len(guild.members):,}")
                if guild.tag:
                    lines.append(f"> **Tag**: [{guild.tag}]")
                if guild.preferred_games:
                    lines.append(f"> **Preferred Games**: {', '.join(game.clean_name for game in guild.preferred_games)}")
                lines.append(f"> **Publicly Listed**: {'Yes' if guild.publicly_listed else 'No'}")
                lines.append(f"> **Joinable**: {'Yes' if guild.joinable else 'No'}")
                if guild.most_online_players:
                    lines.append(f"> **Most Online Players**: {guild.most_online_players:,}")
                if guild.experience_kings:
                    lines.append(f"> **Experience Kings**: {guild.experience_kings:,}")

                embed.description = "\n".join(lines)

                if guild.description:
                    embed.description += "\n" + guild.description

                embed.set_footer(text=f"Hypixel Guild ID: {guild.id}")

            except hypixel.HypixelException as error:
                embed.description = f":x: {error}"
                embed.color = config.ERROR_COLOR
                embed.title = None
        return embed

    async def build_hypixel_player_embed(self, username: str) -> nextcord.Embed:
        client = hypixel.Client(config.HYPIXEL_API_KEY)
        embed = nextcord.Embed(color=config.EMBED_COLOR)
        async with client:
            try:
                player = await client.player(username)

                last_login = None
                if player.last_logout:
                    last_login = str(int(player.last_logout.timestamp()))
                first_join = str(int(player.first_login.timestamp()))
                bedwars = player.bedwars
                skywars = player.skywars
                duels = player.duels
                social_sites = {
                    "twitter": "https://x.com/{}",
                    "instagram": "https://instagram.com/{}",
                    "youtube": "https://youtube.com/@{}",
                    "twitch": "https://twitch.tv/{}",
                    "hypixel_forums": "https://hypixel.net/members/{}",
                }

                socials = [f"[{name}]({url.format(value)})" for name, url in social_sites.items() if (value := getattr(player.socials, name))]

                if player.socials.discord:
                    socials.append(f"Discord: {player.socials.discord}")

                socials_string = ", ".join(socials)

                self.sanitise_stats(player)
                self.sanitise_stats(bedwars)
                self.sanitise_stats(skywars)
                self.sanitise_stats(duels)

                embed.title = await oclib.fetch_random_emoji() + player.name
                embed.description = f"-# Last seen <t:{last_login}:R>\n\n" if last_login else ""

                lines = []
                lines.append(f"> **First joined**: <t:{first_join}:D> (<t:{first_join}:R>)")
                lines.append(f"> **Level**: {player.level:,}, with {player.network_exp:,} network EXP and {player.karma:,} karma")
                if player.rank:
                    lines.append(f"> **Rank**: {player.rank}")
                if player.most_recent_game:
                    lines.append(f"> **Last played**: {player.most_recent_game.clean_name}")
                if socials_string:
                    lines.append(f"> **Socials**: {socials_string}")
                if len(player.achievements) > 0:
                    lines.append(f"> **Achievements**: {len(player.achievements):,} ({player.achievement_points:,} achievement points)")
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
                        f"> **Duels**: {duels.title if duels.title != 0 else 'No Title'}, with {duels.kills:,} kills, {duels.deaths:,} deaths, {duels.wins:,} wins, {duels.losses:,} losses, and a WLR of {duels.wlr}"
                    )

                embed.description += "\n".join(lines)
                embed.set_footer(text="Hypixel User ID: " + player.id)

            except hypixel.HypixelException as error:
                embed.description = f":x: {error}"
                embed.color = config.ERROR_COLOR
                embed.title = None
        return embed

    async def build_hypixel_bedwars_embed(self, username: str) -> nextcord.Embed:
        client = hypixel.Client(config.HYPIXEL_API_KEY)
        embed = nextcord.Embed(color=config.EMBED_COLOR)

        async with client:
            try:
                player = await client.player(username)

                last_login = None
                if player.last_logout:
                    last_login = str(int(player.last_logout.timestamp()))
                bedwars = player.bedwars

                self.sanitise_stats(bedwars)

                embed.title = await oclib.fetch_random_emoji() + f"{player.name}'s Bedwars Statistics"
                embed.description = f"-# Last seen <t:{last_login}:R>\n\n" if last_login else ""

                lines = []
                lines.append(f"> **Level**: {bedwars.level:,} ({bedwars.exp:,} EXP)")
                lines.append(f"> **Coins**: {bedwars.coins:,}")
                lines.append(f"> **Games played**: {bedwars.games:,}")
                lines.append(f"> **Kills**: {bedwars.kills:,} ({bedwars.final_kills:,} final)")
                lines.append(f"> **Deaths**: {bedwars.deaths:,} ({bedwars.final_deaths:,} final)")
                lines.append(f"> **Void deaths**: {bedwars.void_deaths:,} ({bedwars.void_final_deaths:,} final)")
                lines.append(f"> **Fall deaths**: {bedwars.fall_deaths:,} ({bedwars.fall_final_deaths:,} final)")
                lines.append(f"> **KDR**: {bedwars.kdr}")
                lines.append(f"> **FKDR**: {bedwars.fkdr}")
                lines.append(f"> **Beds broken**: {bedwars.beds_broken:,}")
                lines.append(f"> **Beds lost**: {bedwars.beds_lost:,}")
                lines.append(f"> **BBLR**: {bedwars.bblr}")
                lines.append(f"> **Wins**: {bedwars.wins:,}")
                lines.append(f"> **Losses**: {bedwars.losses:,}")
                lines.append(f"> **WLR**: {bedwars.wlr}")

                if bedwars.winstreak > 0:
                    lines.append(f"> **Current winstreak**: {bedwars.winstreak:,}")

                embed.description += "\n".join(lines)
                embed.set_footer(text=f"Hypixel User ID: {player.id}")

            except hypixel.HypixelException as error:
                embed.description = f":x: {error}"
                embed.color = config.ERROR_COLOR
                embed.title = None

        return embed

    async def build_hypixel_blitz_embed(self, username: str) -> nextcord.Embed:
        client = hypixel.Client(config.HYPIXEL_API_KEY)
        embed = nextcord.Embed(color=config.EMBED_COLOR)

        async with client:
            try:
                player = await client.player(username)

                last_login = None
                if player.last_logout:
                    last_login = str(int(player.last_logout.timestamp()))
                blitz = player.blitz

                self.sanitise_stats(blitz)

                embed.title = await oclib.fetch_random_emoji() + f"{player.name}'s Blitz Statistics"
                embed.description = f"-# Last seen <t:{last_login}:R>\n\n" if last_login else ""

                lines = []
                lines.append(f"> **Coins**: {blitz.coins:,}")
                lines.append(f"> **Games played**: {blitz.games:,}")
                lines.append(f"> **Kills**: {blitz.kills:,}")
                lines.append(f"> **Deaths**: {blitz.deaths:,}")
                lines.append(f"> **KDR**: {blitz.kdr}")
                lines.append(f"> **Wins**: {blitz.wins:,} ({blitz.wins_solo:,} solo, {blitz.wins_team:,} team)")
                lines.append(f"> **WLR**: {blitz.wlr}")
                lines.append(f"> **Chests opened**: {blitz.chests_opened:,}")

                if blitz.arrows_shot > 0:
                    lines.append(f"> **Archery**: {blitz.arrows_hit:,} hits, {blitz.arrows_shot:,} shots ({blitz.ar:.2%} accuracy)")

                embed.description += "\n".join(lines)
                embed.set_footer(text=f"Hypixel User ID: {player.id}")

            except hypixel.HypixelException as error:
                embed.description = f":x: {error}"
                embed.color = config.ERROR_COLOR
                embed.title = None

        return embed

    async def build_hypixel_duels_embed(self, username: str) -> nextcord.Embed:
        client = hypixel.Client(config.HYPIXEL_API_KEY)
        embed = nextcord.Embed(color=config.EMBED_COLOR)

        async with client:
            try:
                player = await client.player(username)

                last_login = None
                if player.last_logout:
                    last_login = str(int(player.last_logout.timestamp()))
                duels = player.duels

                self.sanitise_stats(duels)

                embed.title = await oclib.fetch_random_emoji() + f"{player.name}'s Duels Statistics"
                embed.description = f"-# Last seen <t:{last_login}:R>\n\n" if last_login else ""

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
                    lines.append(f"> **Melee**: {duels.melee_hits:,} hits, {duels.melee_swings:,} swings ({duels.mr:.2%} accuracy)")

                if duels.arrows_shot > 0:
                    lines.append(f"> **Archery**: {duels.arrows_hit:,} hits, {duels.arrows_shot:,} shots ({duels.ar:.2%} accuracy)")

                embed.description += "\n".join(lines)
                embed.set_footer(text=f"Hypixel User ID: {player.id}")

            except hypixel.HypixelException as error:
                embed.description = f":x: {error}"
                embed.color = config.ERROR_COLOR
                embed.title = None

        return embed

    async def build_hypixel_murder_mystery_embed(self, username: str) -> nextcord.Embed:
        client = hypixel.Client(config.HYPIXEL_API_KEY)
        embed = nextcord.Embed(color=config.EMBED_COLOR)

        async with client:
            try:
                player = await client.player(username)

                last_login = None
                if player.last_logout:
                    last_login = str(int(player.last_logout.timestamp()))
                murder = player.murder_mystery

                self.sanitise_stats(murder)

                embed.title = await oclib.fetch_random_emoji() + f"{player.name}'s Murder Mystery Statistics"
                embed.description = f"-# Last seen <t:{last_login}:R>\n\n" if last_login else ""

                lines = []
                lines.append(f"> **Coins**: {murder.coins:,}")
                lines.append(f"> **Games played**: {murder.games:,}")
                lines.append(f"> **Wins**: {murder.wins:,} ({murder.murderer_wins:,} murderer, {murder.detective_wins:,} detective)")
                lines.append(f"> **Kills**: {murder.kills:,}")
                lines.append(f"> **Deaths**: {murder.deaths:,}")
                lines.append(f"> **KDR**: {murder.kdr}")
                lines.append(
                    f"> **Weapon kills**: {murder.knife_kills:,} knife, {murder.thrown_knife_kills:,} thrown knife, {murder.bow_kills:,} bow"
                )

                embed.description += "\n".join(lines)
                embed.set_footer(text=f"Hypixel User ID: {player.id}")

            except hypixel.HypixelException as error:
                embed.description = f":x: {error}"
                embed.color = config.ERROR_COLOR
                embed.title = None

        return embed

    async def build_hypixel_paintball_embed(self, username: str) -> nextcord.Embed:
        client = hypixel.Client(config.HYPIXEL_API_KEY)
        embed = nextcord.Embed(color=config.EMBED_COLOR)

        async with client:
            try:
                player = await client.player(username)

                last_login = None
                if player.last_logout:
                    last_login = str(int(player.last_logout.timestamp()))
                paintball = player.paintball

                self.sanitise_stats(paintball)

                embed.title = await oclib.fetch_random_emoji() + f"{player.name}'s Paintball Statistics"
                embed.description = f"-# Last seen <t:{last_login}:R>\n\n" if last_login else ""

                lines = []
                lines.append(f"> **Coins**: {paintball.coins:,}")
                lines.append(f"> **Wins**: {paintball.wins:,}")
                lines.append(f"> **Kills**: {paintball.kills:,}")
                lines.append(f"> **Deaths**: {paintball.deaths:,}")
                lines.append(f"> **KDR**: {paintball.kdr}")
                lines.append(f"> **Killstreaks**: {paintball.killstreaks:,}")
                lines.append(f"> **SKR**: {paintball.skr}")
                lines.append(f"> **Shots fired**: {paintball.shots_fired:,}")

                embed.description += "\n".join(lines)
                embed.set_footer(text=f"Hypixel User ID: {player.id}")

            except hypixel.HypixelException as error:
                embed.description = f":x: {error}"
                embed.color = config.ERROR_COLOR
                embed.title = None

        return embed

    async def build_hypixel_skywars_embed(self, username: str) -> nextcord.Embed:
        client = hypixel.Client(config.HYPIXEL_API_KEY)
        embed = nextcord.Embed(color=config.EMBED_COLOR)

        async with client:
            try:
                player = await client.player(username)

                last_login = None
                if player.last_logout:
                    last_login = str(int(player.last_logout.timestamp()))
                skywars = player.skywars

                self.sanitise_stats(skywars)

                embed.title = await oclib.fetch_random_emoji() + f"{player.name}'s Skywars Statistics"
                embed.description = f"-# Last seen <t:{last_login}:R>\n\n" if last_login else ""

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

                if skywars.winstreak > 0:
                    lines.append(f"> **Current winstreak**: {skywars.winstreak:,}")

                if skywars.arrows_shot > 0:
                    lines.append(f"> **Archery**: {skywars.arrows_hit:,} hits, {skywars.arrows_shot:,} shots ({skywars.ar:.2%} accuracy)")

                embed.description += "\n".join(lines)
                embed.set_footer(text=f"Hypixel User ID: {player.id}")

            except hypixel.HypixelException as error:
                embed.description = f":x: {error}"
                embed.color = config.ERROR_COLOR
                embed.title = None

        return embed

    async def build_hypixel_uhc_embed(self, username: str) -> nextcord.Embed:
        client = hypixel.Client(config.HYPIXEL_API_KEY)
        embed = nextcord.Embed(color=config.EMBED_COLOR)

        async with client:
            try:
                player = await client.player(username)

                last_login = None
                if player.last_logout:
                    last_login = str(int(player.last_logout.timestamp()))
                uhc = player.uhc

                self.sanitise_stats(uhc)

                embed.title = await oclib.fetch_random_emoji() + f"{player.name}'s UHC Statistics"
                embed.description = f"-# Last seen <t:{last_login}:R>\n\n" if last_login else ""

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

                embed.description += "\n".join(lines)
                embed.set_footer(text=f"Hypixel User ID: {player.id}")

            except hypixel.HypixelException as error:
                embed.description = f":x: {error}"
                embed.color = config.ERROR_COLOR
                embed.title = None

        return embed

    @commands.group(
        name="hypixel",
        aliases=["hypickle", "hy"],
        description="Base hypixel command, if no subcommand is passed.",
        invoke_without_command=True,
        help="Hypixel statistics lookup. Use subcommands `status`, `player`, `guild`, `bedwars`, `blitz`, `duels`, `murdermystery`, `paintball`, `skywars`, or `uhc`.",
    )
    async def hypixel(self, ctx: commands.Context):
        embed = nextcord.Embed(
            description="Please specify a subcommand: `status`, `player`, `guild`, `bedwars`, `blitz`, `duels`, `murdermystery`, `paintball`, `skywars`, or `uhc`.",
            color=config.EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel.command(name="status", help="Display Hypixel's status.")
    async def hypixel_status(self, ctx: commands.Context):
        embed = await self.build_hypixel_status_embed()
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel.command(name="guild", aliases=["clan", "team", "club", "gang"], help="Display information on a Hypixel guild.")
    async def hypixel_guild(self, ctx: commands.Context, *, guild_name: str):
        embed = await self.build_hypixel_guild_embed(guild_name)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel.command(name="player", aliases=["member", "user", "profile"], help="Display information on a Hypixel member.")
    async def hypixel_player(self, ctx: commands.Context, username: str):
        embed = await self.build_hypixel_player_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel.command(name="bedwars", aliases=["bwars", "bed", "bw"], help="Display information on a Hypixel member's bedwars statistics.")
    async def hypixel_bedwars(self, ctx: commands.Context, username: str):
        embed = await self.build_hypixel_bedwars_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel.command(name="blitz", help="Display information on a Hypixel member's blitz statistics.")
    async def hypixel_blitz(self, ctx: commands.Context, username: str):
        embed = await self.build_hypixel_blitz_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel.command(name="duels", aliases=["duel"], help="Display information on a Hypixel member's duels statistics.")
    async def hypixel_duels(self, ctx: commands.Context, username: str):
        embed = await self.build_hypixel_duels_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel.command(
        name="murdermystery",
        aliases=["mmystery", "murder_mystery", "mystery", "murder"],
        help="Display information on a Hypixel member's murder mystery statistics.",
    )
    async def hypixel_murder_mystery(self, ctx: commands.Context, username: str):
        embed = await self.build_hypixel_murder_mystery_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel.command(name="paintball", aliases=["pb", "paint", "pball"], help="Display information on a Hypixel member's paintball statistics.")
    async def hypixel_paintball(self, ctx: commands.Context, username: str):
        embed = await self.build_hypixel_paintball_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel.command(name="skywars", aliases=["swars", "sky", "sw"], help="Display information on a Hypixel member's skywars statistics.")
    async def hypixel_skywars(self, ctx: commands.Context, username: str):
        embed = await self.build_hypixel_skywars_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    @hypixel.command(name="uhc", help="Display information on a Hypixel member's UhC statistics.")
    async def hypixel_uhc(self, ctx: commands.Context, username: str):
        embed = await self.build_hypixel_uhc_embed(username)
        await ctx.reply(embed=embed, mention_author=False)

    # slash
    @nextcord.slash_command(name="hypixel", description="Hypixel information commands.")
    async def slash_hypixel(self, interaction: nextcord.Interaction):
        pass

    @slash_hypixel.subcommand(name="status", description="Check Hypixel's status.")
    async def slash_hypixel_status(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        embed = await self.build_hypixel_status_embed()
        await interaction.send(embed=embed)

    @slash_hypixel.subcommand(name="guild", description="Display information on a Hypixel guild.")
    async def slash_hypixel_guild(
        self, interaction: nextcord.Interaction, guild_name: str = nextcord.SlashOption(description="The Hypixel guild to look up", required=True)
    ):
        await interaction.response.defer()
        embed = await self.build_hypixel_guild_embed(guild_name)
        await interaction.send(embed=embed)

    @slash_hypixel.subcommand(name="player", description="Display information on a Hypixel player.")
    async def slash_hypixel_player(
        self, interaction: nextcord.Interaction, username: str = nextcord.SlashOption(description="The Hypixel player to look up", required=True)
    ):
        await interaction.response.defer()
        embed = await self.build_hypixel_player_embed(username)
        await interaction.send(embed=embed)

    @slash_hypixel.subcommand(name="bedwars", description="Display Bedwars statistics.")
    async def slash_hypixel_bedwars(
        self, interaction: nextcord.Interaction, username: str = nextcord.SlashOption(description="The Hypixel player to look up", required=True)
    ):
        await interaction.response.defer()
        embed = await self.build_hypixel_bedwars_embed(username)
        await interaction.send(embed=embed)

    @slash_hypixel.subcommand(name="blitz", description="Display Blitz statistics.")
    async def slash_hypixel_blitz(
        self, interaction: nextcord.Interaction, username: str = nextcord.SlashOption(description="The Hypixel player to look up", required=True)
    ):
        await interaction.response.defer()
        embed = await self.build_hypixel_blitz_embed(username)
        await interaction.send(embed=embed)

    @slash_hypixel.subcommand(name="duels", description="Display Duels statistics.")
    async def slash_hypixel_duels(
        self, interaction: nextcord.Interaction, username: str = nextcord.SlashOption(description="The Hypixel player to look up", required=True)
    ):
        await interaction.response.defer()
        embed = await self.build_hypixel_duels_embed(username)
        await interaction.send(embed=embed)

    @slash_hypixel.subcommand(name="murdermystery", description="Display Murder Mystery statistics.")
    async def slash_hypixel_murder_mystery(
        self, interaction: nextcord.Interaction, username: str = nextcord.SlashOption(description="The Hypixel player to look up", required=True)
    ):
        await interaction.response.defer()
        embed = await self.build_hypixel_murder_mystery_embed(username)
        await interaction.send(embed=embed)

    @slash_hypixel.subcommand(name="paintball", description="Display Paintball statistics.")
    async def slash_hypixel_paintball(
        self, interaction: nextcord.Interaction, username: str = nextcord.SlashOption(description="The Hypixel player to look up", required=True)
    ):
        await interaction.response.defer()
        embed = await self.build_hypixel_paintball_embed(username)
        await interaction.send(embed=embed)

    @slash_hypixel.subcommand(name="skywars", description="Display SkyWars statistics.")
    async def slash_hypixel_skywars(
        self, interaction: nextcord.Interaction, username: str = nextcord.SlashOption(description="The Hypixel player to look up", required=True)
    ):
        await interaction.response.defer()
        embed = await self.build_hypixel_skywars_embed(username)
        await interaction.send(embed=embed)

    @slash_hypixel.subcommand(name="uhc", description="Display UHC statistics.")
    async def slash_hypixel_uhc(
        self, interaction: nextcord.Interaction, username: str = nextcord.SlashOption(description="The Hypixel player to look up", required=True)
    ):
        await interaction.response.defer()
        embed = await self.build_hypixel_uhc_embed(username)
        await interaction.send(embed=embed)


def setup(bot):
    if config.HYPIXEL_API_KEY:
        bot.add_cog(Hypixel(bot))
    else:
        print(
            "Skipping loading of the minecraft.hypixel cog: you must set the HYPIXEL_API_KEY environment variable for htis cog to work! Visit https://developer.hypixel.net for an API key."
        )
