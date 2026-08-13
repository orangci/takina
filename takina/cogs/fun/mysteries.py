# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors, lyhelpers
from takina.libs.fate_responses import fates
from discord.ext import commands
from takina import config
import discord


class Mysteries(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

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
        aliases=["relationship"], description="Check your fate with another user.", usage="@user"
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
    await bot.add_cog(Mysteries(bot))
