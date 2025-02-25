from __future__ import annotations
from ..libs.oclib import *
import nextcord
from nextcord.ext import commands
from config import *


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

    @commands.command(
        name="neko",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def neko(self, ctx: commands.Context):
        embed = await request_neko("png", "neko")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="kitsune",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kitsune(self, ctx: commands.Context):
        embed = await request_neko("png", "kitsune")
        await ctx.reply(embed=embed, mention_author=False)


class NekoInteractions(commands.Cog):
    def __init__(self, bot):
        self._bot = bot

    @commands.command(
        name="lurk",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def lurk(self, ctx: commands.Context):
        embed = await request_neko("gif", "lurk")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="shoot",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def shoot(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{target.mention}, you've been shot by {ctx.author.mention}! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "shoot")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="sleep",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def sleep(self, ctx: commands.Context):
        embed = await request_neko("gif", "sleep")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="shrug",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def shrug(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{ctx.author.mention} shrugs at {target.mention}. {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "shrug")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="stare",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def stare(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{ctx.author.mention} stares at {target.mention}. {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "stare")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="wave",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def wave(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{target.mention}, you've been waved at by {ctx.author.mention}! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "wave")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="poke",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def poke(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{target.mention}, you've been poked by {ctx.author.mention}! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "poke")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="smile",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def smile(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{ctx.author.mention} smiles at {target.mention}. {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "smile")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="wink",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def wink(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{ctx.author.mention} winks at {target.mention}. {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "wink")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="blush",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def blush(self, ctx: commands.Context):
        embed = await request_neko("gif", "blush")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="smug",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def smug(self, ctx: commands.Context):
        embed = await request_neko("gif", "smug")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="yeet",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def yeet(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{target.mention}, you've been yeeted by {ctx.author.mention}! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "yeet")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="think",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def think(self, ctx: commands.Context):
        embed = await request_neko("gif", "think")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="yawn",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def yawn(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{ctx.author.mention} yawns at {target.mention}. {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "yawn")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="facepalm",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def facepalm(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{ctx.author.mention} facepalms at {target.mention}. {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "facepalm")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="cuddle",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cuddle(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{target.mention}, you've been cuddled by {ctx.author.mention}! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "cuddle")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="nom",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def nom(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{target.mention}, you've been consoomed by {ctx.author.mention}! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "nom")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="feed",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def feed(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{target.mention}, you've been fed by {ctx.author.mention}! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "feed")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="bored",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def bored(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{ctx.author.mention} is bored by {target.mention}. {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "bored")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="bonk",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kick(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{target.mention}, you've been bonked by {ctx.author.mention}! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "kick")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="happy",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def happy(self, ctx: commands.Context):
        embed = await request_neko("gif", "happy")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="hug",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def hug(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{target.mention}, you've been hugged by {ctx.author.mention}! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "hug")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="baka",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def baka(self, ctx: commands.Context, *, target=None):
        embed = await request_neko("gif", "baka")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="pat",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pat(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{ctx.author.mention} pats {target.mention}. {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "pat")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="nod",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def nod(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{ctx.author.mention} nods at {target.mention}. {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "nod")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="nope",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def nope(self, ctx: commands.Context):
        embed = await request_neko("gif", "nope")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="kiss",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def kiss(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{target.mention}, you've been kissed by {ctx.author.mention}! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "kiss")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="dance",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dance(self, ctx: commands.Context):
        embed = await request_neko("gif", "dance")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="punch",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def punch(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{target.mention}, you've been punched by {ctx.author.mention}! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "punch")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="handshake",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def handshake(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{target.mention}, you're given a handshake by {ctx.author.mention}! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "handshake")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="slap",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def slap(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{target.mention}, you've been slapped by {ctx.author.mention}! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "slap")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="cry",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cry(self, ctx: commands.Context):
        embed = await request_neko("gif", "cry")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="pout",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pout(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{ctx.author.mention} pouts at {target.mention}. {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "pout")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="handhold",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
        aliases=["lewd"],
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def handhold(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{ctx.author.mention} holds{target.mention}'s hands. How lewd! {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "handhold")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="thumbsup",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
        aliases=["ok", "okay", "yes"],
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def thumbsup(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{ctx.author.mention} gives {target.mention} a thumbsup. {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "thumbsup")
        await ctx.reply(target, embed=embed, mention_author=False)

    @commands.command(
        name="laugh",
        help="GIF interaction command that utilizes the [nekos.best](https://nekos.best) API.",
    )
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def laugh(self, ctx: commands.Context, *, target=None):
        if target:
            if not isinstance(target, nextcord.Member):
                target = extract_user_id(target, ctx)
                if isinstance(target, nextcord.Embed):
                    await ctx.reply(embed=target, mention_author=False)
            target = f"{ctx.author.mention} laughs at {target.mention}. {await fetch_random_emoji()}"
        else:
            target = ""
        embed = await request_neko("gif", "laugh")
        await ctx.reply(target, embed=embed, mention_author=False)


def setup(bot):
    bot.add_cog(Neko(bot))
