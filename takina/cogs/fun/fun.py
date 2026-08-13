# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from takina.libs.fate_responses import fates
from discord.ext import commands
from takina import config
from urllib import parse
import discord
import random


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    async def fetch_user_image(
        self,
        ctx: commands.Context,
        user: discord.Member | discord.User | None = None,
        image_type: str = "display_avatar",
    ) -> discord.Embed:
        image_type_str = image_type.replace("_", " ").title()

        if not user:
            if not isinstance(ctx.author, discord.Member | discord.User):
                raise lyerrors.TakinaError("This command can only be used in a server.")
            user = ctx.author

        if "banner" in image_type:
            # why are we refetching the user?
            # well, you cannot get User.banner
            # if you do not specifically do Client.fetch_user
            # https://discordpy.readthedocs.io/en/stable/api.html#discord.User.banner
            user = await self._bot.fetch_user(user.id)

        image = getattr(user, image_type)
        if not image:
            raise lyerrors.TakinaError(f"This user does not have a {image_type_str.lower()} set.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = f"{user}'s {image_type_str}"
        embed.set_image(url=image.url)

        return embed

    @commands.hybrid_command(name="fact", description="Fetch a random fact.")
    @lychecks.is_user_app()
    async def fact(self, ctx: commands.Context) -> None:
        data = await lyhelpers.request("https://uselessfacts.jsph.pl/api/v2/facts/random")
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{data.get('text')} {await lyhelpers.fetch_random_emoji()}"
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="joke", aliases=["dadjoke"], description="Fetch a random joke.")
    @lychecks.is_user_app()
    async def joke(self, ctx: commands.Context) -> None:
        joke_type = random.choice(["dadjoke", "regular"])

        if joke_type == "dadjoke":
            headers = {"Accept": "application/json"}
            data = await lyhelpers.request("https://icanhazdadjoke.com/", headers=headers)
            joke = data.get("joke")

        else:
            data = await lyhelpers.request("https://v2.jokeapi.dev/joke/Any?safe-mode")
            while data.get("category") == "Christmas":
                data = await lyhelpers.request("https://v2.jokeapi.dev/joke/Any?safe-mode")

            joke = data.get("joke")
            if not joke:
                setup = data.get("setup")
                delivery = data.get("delivery")
                joke = f"{setup}\n{delivery}"

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{joke} {await lyhelpers.fetch_random_emoji()}"
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="commit", description=f"Order {config.BOT_NAME.title()} to do anything.", usage="arson"
    )
    @lychecks.is_user_app()
    async def commit(self, ctx: commands.Context, *, action: str) -> None:
        possible_responses = [
            "Yes, sir!",
            "I don't particularly feel like it.",
            "Why would I do that?",
            "Of course!",
            "Right away.",
            "As your majesty orders.",
            "No, I refuse.",
            "I don't want to, so get lost.",
        ]

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{lyhelpers.randint_from_seed(action, possible_responses)} {await lyhelpers.fetch_random_emoji()}"

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="avatar",
        aliases=["av", "pfp"],
        description="Fetch the Discord display avatar of any member including yourself.",
        usage="@user",
    )
    @lychecks.is_user_app()
    async def avatar(
        self, ctx: commands.Context, *, member: discord.Member | discord.User | None = None
    ) -> None:
        embed = await self.fetch_user_image(ctx, member, "display_avatar")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="server_avatar",
        aliases=["sav", "spfp", "gav", "gpfp"],
        description="Fetch the Discord server avatar of any member including yourself.",
        usage="@user",
    )
    @lychecks.guild_only()
    async def server_avatar(
        self, ctx: commands.Context, *, member: discord.Member | None = None
    ) -> None:
        embed = await self.fetch_user_image(ctx, member, "guild_avatar")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="banner",
        description="Fetch the Discord banner of any member including yourself.",
        usage="@user",
    )
    @lychecks.is_user_app()
    async def banner(
        self, ctx: commands.Context, *, member: discord.Member | discord.User | None = None
    ) -> None:
        embed = await self.fetch_user_image(ctx, member, "banner")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="server_banner",
        aliases=["sbanner", "gbanner"],
        description="Fetch the Discord server banner of any member including yourself.",
        usage="@user",
    )
    @lychecks.guild_only()
    async def server_banner(
        self, ctx: commands.Context, *, member: discord.Member | None = None
    ) -> None:
        embed = await self.fetch_user_image(ctx, member, "guild_banner")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="google", description="Google anything!", usage="shawarma restaurants near me"
    )
    @lychecks.is_user_app()
    async def google(self, ctx: commands.Context, *, query: str) -> None:
        query_before_conversion = query
        query = parse.quote_plus(query)

        emoji = await lyhelpers.fetch_random_emoji()
        lmgtfy_url = f"https://letmegooglethat.com/?q={query}"

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = f"{emoji}Let Me Google That For You!"
        embed.description = f"Here is your search result for: **{query_before_conversion}**"
        embed.url = lmgtfy_url
        embed.add_field(name="Click here:", value=lmgtfy_url, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="roll", description="Roll a random number from 1—100.")
    @lychecks.is_user_app()
    async def roll(self, ctx: commands.Context) -> None:
        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = (
            f"{await lyhelpers.fetch_random_emoji()} You rolled {random.randint(1, 100)}!"
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="8ball",
        aliases=["42ball"],
        description="Ask the 8ball anything.",
        usage="are you sentient",
    )
    @lychecks.is_user_app()
    async def eight_ball(self, ctx: commands.Context, *, question: str | None = None) -> None:
        responses = [
            # positive
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes, definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "All Signs point to yes.",
            # negative
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
            "Absolutely not.",
            "The answer is no.",
            "Highly unlikely.",
            "The odds are against it.",
            "All signs point to no.",
        ]

        if not question:
            raise lyerrors.TakinaUserInputError(
                "You need to ask a question to the 8ball for this command to work!"
            )

        response = lyhelpers.randint_from_seed(question, responses)

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = "🎱 The 8ball"
        embed.description = f"**Question:** {question}"
        embed.description += f"\n**Answer:** {response}"

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="fate",
        aliases=["relationship"],
        description="Check your fate with another user.",
        usage="@user",
    )
    @lychecks.is_user_app()
    async def fate(self, ctx: commands.Context, user: discord.User) -> None:
        emoji = await lyhelpers.fetch_random_emoji()

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.description = f"{emoji} {lyhelpers.randint_from_seed(ctx.author.id + user.id, fates).format(target=user.mention)}"
        embed.set_footer(text="In another universe...")

        if ctx.author.id == user.id:
            embed.description = f"{emoji} You and {user.mention} are the same person!"
            embed.remove_footer()

        if user.id in {self._bot.application_id, 1287074090783604797}:
            if ctx.author.id == 961063229168164864:
                embed.description = f"{emoji} I'm your daughter! How could you forget..?"
            elif ctx.author.id == 716306888492318790:
                embed.description = f"{emoji} I'm your niece! How could you forget..?"
            else:
                embed.description = f"{emoji} I won't tell you! Hmph, mind your own business!"

            embed.remove_footer()

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))
