import nextcord
from nextcord.ext import commands
import re
from collections import defaultdict

class SwearCounter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.swear_counts = defaultdict(int)
        self.swear_words = [
            "damn", "hell", "shit", "fuck", "bitch", "bastard", "asshole",
            "dick", "piss", "cunt", "crap", "prick", "motherfucker", "wanker",
            "bollocks", "bloody", "bugger", "arse", "slut", "whore", "twat",
            "nigger", "nigga", "retard", "faggot", "douche", "jackass",
            "pussy", "cock", "shithead", "scumbag", "piss off", "dickhead",
            "cum", "wank", "fucker", "dildo", "cocksucker", "asshat",
            "goddamn", "bollock", "tosser", "wankstain", "bint",
            "gash", "jerk", "knob", "minger", "minge", "pikey", "plonker",
            "arsehole", "fuckwit", "knobhead", "nonce", "wazzock", "cocks",
            "dicks", "flaps", "gobshite", "munt", "damnation", "bollocking",
            "clunge", "cocknose", "knobjockey", "twatwaffle", "arsewipe",
            "fucktard", "cunter", "shitstorm", "twathead", "fanny", "shag",
            "rimjob", "smegma", "wang", "willy", "pissflaps", "bellend",
            "doggy style", "mofos", "clusterfuck", "bastards", "buggered",
            "buttfuck", "skank", "numbnuts", "sexist", "bigot", "gringo",
            "honky", "tranny", "boner", "bimbo", "pecker", "dickwad",
            "cumslut", "cocknugget", "thot", "cumdumpster", "skeet", "nutsack",
            "meatspin", "titties", "spunk", "choad", "cooch", "nutjob", "beaner",
            "a\*\*hole", "f\*\*k", "b\*\*ch", "sh\*t", "d\*mn", "c\*nt", "pr\*ck",
            "m\*r\*\*f\*cker", "b\*\*tch", "wtf", "lmfao", "af", "c**nt", "f*ck",
            "a55hole", "fucking", "b1tch", "b33tch", "5lut", "p0rn", "b00bs", 
            "ne1gger", "dik", "c0ck", "pus55y", "fap", "skeet", "pwn", "sei",
            "r3tard3d", "h0m0", "arsebiscuits", "buttnugget", "fuc", "knobend",
            "cuk", "tw4t", "niggaro", "f4g", "coitus", "wanker", "mingebag",
        ]
        self.swear_regex = re.compile(r'\b(' + '|'.join(re.escape(word) for word in self.swear_words) + r')\b', re.IGNORECASE)

    async def update_swear_count(self, message):
        if message.author.bot:
            return
        
        matches = self.swear_regex.findall(message.content)
        self.swear_counts[message.author.id] += len(matches)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        await self.update_swear_count(message)

    @commands.command(name="scount", help="Check user's swear word usage.")
    async def swearcount(self, ctx: commands.Context, member: nextcord.Member = None):
        member = member or ctx.author
        count = self.swear_counts.get(member.id, 0)
        await ctx.send(f"{member.display_name} has used {count} swear words.")

def setup(bot):
    bot.add_cog(scount(bot))
