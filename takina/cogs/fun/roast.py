from __future__ import annotations
from ..libs.oclib import *
import nextcord
from nextcord.ext import commands
from config import *


class Roast(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.command(
        name="roast",
        help="Get roasted by the bot. \nUsage: `roast`.",
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def roast(self, ctx: commands.Context):
        roasts = [
            "You're so slow, Internet Explorer feels bad for you.",
            "I'd roast you, but my mom said I shouldn't burn trash.",
            "You're the reason why shampoo has instructions.",
            "If I had a dollar for every brain cell you have, I'd be in debt.",
            "You're not the dumbest person on Earth, but you better hope they don't die.",
            "I'd explain it to you, but I don't have any crayons.",
            "You bring everyone so much joy... when you leave the room.",
            "Light travels faster than sound, which is why you seemed bright until you spoke.",
            "Hold still, I'm trying to imagine you with a personality.",
            "Your secrets are safe with me, I wasn't even listening.",
            "You're like a cloud - when you disappear, it's a beautiful day.",
            "You're like Python's GIL - always blocking progress.",
            "Your code is so bad, even Stack Overflow won't help you.",
            "You're like CSS - always causing problems that didn't exist before.",
            "You're so basic, you make HTML look complex.",
            "Your debugging skills are like Windows Vista - fundamentally broken.",
            "You're like a semicolon in Python - completely unnecessary.",
            "Your code comments are like your life choices - questionable and confusing.",
            "You're so outdated, you make COBOL look cutting-edge.",
            "You're like a DNS error - impossible to look up and hard to resolve.",
            "Your code has more bugs than a roach motel during a heat wave.",
            "You're like PHP - nobody likes you, but somehow you're still around.",
            "Your brain runs on Internet Explorer 6 - slow, buggy, and desperately needs an update.",
            "You're so dense, black holes are taking notes.",
            "Your pull requests are like your dating life - always rejected.",
            "You're like a null pointer - pointless and causes everything to crash.",
            "Your code is so spaghetti, Italy wants to hire you as a chef.",
            "You're like a legacy codebase - full of issues and nobody wants to deal with you.",
            "You're so basic, you make Assembly language look user-friendly.",
            "Your existence is like a race condition - a complete mistake that should've been prevented."
        ]
        embed = nextcord.Embed(
            title=f"🔥 Roast Time!",
            description=f"{ctx.author.mention} {random.choice(roasts)} {await fetch_random_emoji()}",
            color=EMBED_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)


class SlashRoast(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @nextcord.slash_command(
        name="roast",
        description="Get roasted by the bot.",
    )
    async def roast(self, interaction: nextcord.Interaction):
        roasts = [
            "You're so slow, Internet Explorer feels bad for you.",
            "I'd roast you, but my mom said I shouldn't burn trash.",
            "You're the reason why shampoo has instructions.",
            "If I had a dollar for every brain cell you have, I'd be in debt.",
            "You're not the dumbest person on Earth, but you better hope they don't die.",
            "I'd explain it to you, but I don't have any crayons.",
            "You bring everyone so much joy... when you leave the room.",
            "Light travels faster than sound, which is why you seemed bright until you spoke.",
            "Hold still, I'm trying to imagine you with a personality.",
            "Your secrets are safe with me, I wasn't even listening.",
            "You're like a cloud - when you disappear, it's a beautiful day.",
            "You're like Python's GIL - always blocking progress.",
            "Your code is so bad, even Stack Overflow won't help you.",
            "You're like CSS - always causing problems that didn't exist before.",
            "You're so basic, you make HTML look complex.",
            "Your debugging skills are like Windows Vista - fundamentally broken.",
            "You're like a semicolon in Python - completely unnecessary.",
            "Your code comments are like your life choices - questionable and confusing.",
            "You're so outdated, you make COBOL look cutting-edge.",
            "You're like a DNS error - impossible to look up and hard to resolve.",
            "Your code has more bugs than a roach motel during a heat wave.",
            "You're like PHP - nobody likes you, but somehow you're still around.",
            "Your brain runs on Internet Explorer 6 - slow, buggy, and desperately needs an update.",
            "You're so dense, black holes are taking notes.",
            "Your pull requests are like your dating life - always rejected.",
            "You're like a null pointer - pointless and causes everything to crash.",
            "Your code is so spaghetti, Italy wants to hire you as a chef.",
            "You're like a legacy codebase - full of issues and nobody wants to deal with you.",
            "You're so basic, you make Assembly language look user-friendly.",
            "Your existence is like a race condition - a complete mistake that should've been prevented."
        ]
        embed = nextcord.Embed(
            title=f"Hey {interaction.user.name}!",
            description=f"{interaction.user.mention} {random.choice(roasts)} {await fetch_random_emoji()}",
            color=EMBED_COLOR,
        )
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Roast(bot))
    bot.add_cog(SlashRoast(bot))