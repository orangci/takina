from __future__ import annotations
from ..libs.oclib import *
import dotenv
import nextcord
from nextcord.ext import commands
from __main__ import EMBED_COLOR

dotenv.load_dotenv()

async def request_neko(format: str, type: str) -> nextcord.Embed:
    url = f"https://nekos.best/api/v2/{type}"
    data = await request(url)
    result = data.get("results", [])[0]
    image_url = result.get("url")
    
    embed = nextcord.Embed(color=EMBED_COLOR)
    embed.set_image(url=image_url)

    if format == "gif":
        anime_name = result.get("anime_name")
        embed.set_footer(text=f"Anime: {anime_name}")
    elif format == "png":
        artist = result.get("artist_name")
        artist_url = result.get("artist_href")
        embed.set_author(name=f"Artist: {artist}", url=artist_url)

    return embed

class Neko(commands.Cog):
    def __init__(self, bot):
        self._bot = bot
        latency = bot.latency
    
    @commands.command(name="neko")
    async def neko(self, ctx: commands.Context):
        embed = await request_neko("png", "neko")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="kitsune")
    async def kitsune(self, ctx: commands.Context):
        embed = await request_neko("png", "kitsune")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="lurk")
    async def lurk(self, ctx: commands.Context):
        embed = await request_neko("gif", "lurk")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="shoot")
    async def shoot(self, ctx: commands.Context):
        embed = await request_neko("gif", "shoot")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="sleep")
    async def sleep(self, ctx: commands.Context):
        embed = await request_neko("gif", "sleep")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="shrug")
    async def shrug(self, ctx: commands.Context):
        embed = await request_neko("gif", "shrug")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="stare")
    async def stare(self, ctx: commands.Context):
        embed = await request_neko("gif", "stare")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="wave")
    async def wave(self, ctx: commands.Context):
        embed = await request_neko("gif", "wave")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="poke")
    async def poke(self, ctx: commands.Context):
        embed = await request_neko("gif", "poke")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="smile")
    async def smile(self, ctx: commands.Context):
        embed = await request_neko("gif", "smile")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="wink")
    async def wink(self, ctx: commands.Context):
        embed = await request_neko("gif", "wink")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="blush")
    async def blush(self, ctx: commands.Context):
        embed = await request_neko("gif", "blush")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="smug")
    async def smug(self, ctx: commands.Context):
        embed = await request_neko("gif", "smug")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="yeet")
    async def yeet(self, ctx: commands.Context):
        embed = await request_neko("gif", "yeet")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="think")
    async def think(self, ctx: commands.Context):
        embed = await request_neko("gif", "think")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="yawn")
    async def yawn(self, ctx: commands.Context):
        embed = await request_neko("gif", "yawn")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="facepalm")
    async def facepalm(self, ctx: commands.Context):
        embed = await request_neko("gif", "facepalm")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="cuddle")
    async def cuddle(self, ctx: commands.Context):
        embed = await request_neko("gif", "cuddle")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="nom")
    async def nom(self, ctx: commands.Context):
        embed = await request_neko("gif", "nom")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="feed")
    async def feed(self, ctx: commands.Context):
        embed = await request_neko("gif", "feed")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="bored")
    async def bored(self, ctx: commands.Context):
        embed = await request_neko("gif", "bored")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="bonk")
    async def kick(self, ctx: commands.Context):
        embed = await request_neko("gif", "kick")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="happy")
    async def happy(self, ctx: commands.Context):
        embed = await request_neko("gif", "happy")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="hug")
    async def hug(self, ctx: commands.Context):
        embed = await request_neko("gif", "hug")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="baka")
    async def baka(self, ctx: commands.Context):
        embed = await request_neko("gif", "baka")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="pat")
    async def pat(self, ctx: commands.Context):
        embed = await request_neko("gif", "pat")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="nod")
    async def nod(self, ctx: commands.Context):
        embed = await request_neko("gif", "nod")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="nope")
    async def nope(self, ctx: commands.Context):
        embed = await request_neko("gif", "nope")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="kiss")
    async def kiss(self, ctx: commands.Context):
        embed = await request_neko("gif", "kiss")
        await ctx.reply(embed=embed, mention_author=False)
        
    @commands.command(name="dance")
    async def dance(self, ctx: commands.Context):
        embed = await request_neko("gif", "dance")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="punch")
    async def punch(self, ctx: commands.Context):
        embed = await request_neko("gif", "punch")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="handshake")
    async def handshake(self, ctx: commands.Context):
        embed = await request_neko("gif", "handshake")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="slap")
    async def slap(self, ctx: commands.Context):
        embed = await request_neko("gif", "slap")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="cry")
    async def cry(self, ctx: commands.Context):
        embed = await request_neko("gif", "cry")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="pout")
    async def pout(self, ctx: commands.Context):
        embed = await request_neko("gif", "pout")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="handhold", aliases=["lewd"])
    async def handhold(self, ctx: commands.Context):
        embed = await request_neko("gif", "handhold")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="thumbsup", aliases=["ok", "okay", "yes"])
    async def thumbsup(self, ctx: commands.Context):
        embed = await request_neko("gif", "thumbsup")
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="laugh")
    async def laugh(self, ctx: commands.Context):
        embed = await request_neko("gif", "laugh")
        await ctx.reply(embed=embed, mention_author=False)

def setup(bot):
    bot.add_cog(Neko(bot))
