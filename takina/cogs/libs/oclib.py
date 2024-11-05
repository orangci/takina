import re
import nextcord
from nextcord.ext import commands
import aiohttp
import datetime
from nextcord.ui import View
import os
import random
from __main__ import EMBED_COLOR

start_time = datetime.datetime.utcnow()


# for those commands where you can mention a user either by mentioning them, using their ID, their username, or displayname
def extract_user_id(
    member_str: str, ctx: commands.Context | nextcord.Interaction
) -> nextcord.Member:
    match = re.match(r"<@!?(\d+)>", member_str)
    if match:
        user_id = int(match.group(1))
        return ctx.guild.get_member(user_id)

    if member_str.isdigit():
        user_id = int(member_str)
        return ctx.guild.get_member(user_id)

    member = nextcord.utils.get(
        ctx.guild.members,
        name=member_str,
    ) | nextcord.utils.get(ctx.guild.members, display_name=member_str)

    if not member:
        error_embed = nextcord.Embed(
            color=0xFF0037,
        )
        error_embed.description = ":x: Member not found. Please provide a valid username, display name, mention, or user ID."
        return error_embed


# for requesting data from APIs
async def request(url, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request("GET", url, *args, **kwargs) as response:
            return await response.json()


# for calculating durations, e.g. 1d, 2h, 5s, 34m
def duration_calculator(duration: str) -> int:
    pattern = r"(\d+)([s|m|h|d|w|y])"
    match = re.fullmatch(pattern, duration)
    error_embed = nextcord.Embed(
        description=":x: Invalid duration format. Use <number>[s|d|h|m|w|y].",
        color=0xFF0037,
    )
    if not match:
        return error_embed

    time_value, time_unit = match.groups()
    time_value = int(time_value)

    if time_unit == "s":
        return time_value * 1
    elif time_unit == "m":
        return time_value * 60
    elif time_unit == "h":
        return time_value * 3600
    elif time_unit == "d":
        return time_value * 86400
    elif time_unit == "w":
        return time_value * 604800
    elif time_unit == "y":
        return time_value * 31536000
    else:
        return error_embed


# for checking perms of a command
def perms_check(
    member: nextcord.Member = None,
    *,
    ctx: commands.Context | nextcord.Interaction,
    author_check: bool = True,
    owner_check: bool = False,
    role_check: bool = True,
):
    # Check if member is valid
    if not isinstance(member, nextcord.Member) or member is None:
        return False, nextcord.Embed(
            description=":x: Member not found.", color=0xFF0037
        )

    if isinstance(ctx, commands.Context):
        author = ctx.author
    elif isinstance(ctx, nextcord.Interaction):
        author = ctx.user
    else:
        return False, nextcord.Embed(description=":x: Invalid context.", color=0xFF0037)

    # Toggle for self-action check
    if author_check and member == author:
        return False, nextcord.Embed(
            description=":x: You cannot perform this action on yourself.",
            color=0xFF0037,
        )

    # Toggle for server owner check
    if owner_check and member == ctx.guild.owner:
        return False, nextcord.Embed(
            description=":x: You cannot perform this action on the server owner.",
            color=0xFF0037,
        )

    # Toggle for role hierarchy checks
    if role_check:
        if member.top_role >= author.top_role:
            return (
                False,
                nextcord.Embed(
                    description=":x: You cannot perform this action on someone with a higher or equal role than yours.",
                    color=0xFF0037,
                ),
            )

        if member.top_role >= ctx.guild.me.top_role:
            return (
                False,
                nextcord.Embed(
                    description=":x: I cannot perform this action on someone with a higher or equal role than mine.",
                    color=0xFF0037,
                ),
            )

    return True, None


# uptime checker
async def uptime_fetcher():
    global start_time
    current_time = datetime.datetime.utcnow()
    uptime_duration = current_time - start_time

    # Format the uptime duration
    days, seconds = uptime_duration.days, uptime_duration.seconds
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    return uptime_str


# confirmation embed for moderation things
class ConfirmationView(View):
    def __init__(
        self,
        ctx: commands.Context | nextcord.Interaction,
        member: nextcord.Member,
        action: str,
        reason: str,
        duration: str = None,
    ):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.member = member
        self.action = action
        self.reason = reason
        self.duration = duration
        self.result = None
        self.message = None

    # Confirm
    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green)
    async def confirm(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
        self.result = True
        await interaction.message.delete()
        self.stop()

    # Cancel
    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red)
    async def cancel(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
        self.result = False
        await self.disable_buttons(interaction)
        self.stop()

    async def disable_buttons(self, interaction: nextcord.Interaction):
        if self.result:
            new_embed = nextcord.Embed(
                description=f"{self.action.capitalize()} confirmed.", color=EMBED_COLOR
            )
        else:
            new_embed = nextcord.Embed(
                description=f"{self.action.capitalize()} cancelled.", color=EMBED_COLOR
            )

        await interaction.message.edit(embed=new_embed, view=None)

    async def prompt(self):
        embed = nextcord.Embed(
            title=f"Confirm {self.action.capitalize()}",
            description=f"Are you sure you want to {self.action} {self.member.mention}?",
            color=EMBED_COLOR,
        )
        if isinstance(self.ctx, commands.Context):
            self.message = await self.ctx.reply(
                embed=embed, view=self, mention_author=False
            )
        elif isinstance(self.ctx, nextcord.Interaction):
            self.message = await self.ctx.send(embed=embed, view=self)
        else:
            return False, ":x: Invalid context."

        await self.wait()

        if self.result is None:
            for child in self.children:
                child.disabled = True
            timeout_embed = nextcord.Embed(
                description=f"{self.action.capitalize()} cancelled; timed out.",
                color=EMBED_COLOR,
            )
            self.result = False
            await self.message.edit(embed=timeout_embed, view=None)

        return self.result


emoji_dict = {
    "love": "<:love:1293115234382512200>",
    "yes": "<:yes:1293115235896524833>",
    "skullsob": "<:skullsob:1293115237356277822>",
    "kekw": "<:kekw:1293115239524470794>",
    "smug": "<:smug:1293115243211391027>",
    "uwot": "<:uwot:1293115245698486272>",
    "blushge": "<:blushge:1293115249024700490>",
    "uwot2": "<:uwot2:1293115251432226829>",
    "gilthumbsup": "<:gilthumbsup:1293115253302759458>",
    "SMH": "<:SMH:1293115256331304961>",
    "wth": "<:wth:1293115258256232541>",
    "hmmsus": "<:hmmsus:1293115262316445748>",
    "sigh": "<:sigh:1293115265235554335>",
    "this": "<:this:1293115267550941246>",
    "harold": "<:harold:1293115269245440042>",
    "doubt": "<:doubt:1293115273163046913>",
    "nekoBlush": "<:nekoBlush:1293115274832384021>",
    "aquacry": "<:aquacry:1293115278372241469>",
    "wheeze": "<:wheeze:1293115279903293506>",
    "pikaeww": "<:pikaeww:1293115283657195531>",
    "pensivetrash": "<:pensivetrash:1293115285775192126>",
    "pog": "<:pog:1293115288082190402>",
    "point": "<:point:1293115290225344555>",
    "aniwave": "<:aniwave:1293115292578353195>",
    "FlushedW": "<:FlushedW:1293115294478237707>",
    "pepepunch": "<:pepepunch:1293115298022424680>",
    "pepehands": "<:pepehands:1293115300639932497>",
    "YEP": "<:YEP:1293115302326042654>",
    "success": "<:success:1293115304205090888>",
    "sadge": "<:sadge:1293115305802862706>",
    "evil": "<:evil:1293115307879305236>",
    "chill": "<:chill:1293115309800161332>",
    "copium": "<:copium:1293115311578677258>",
    "avert": "<:avert:1293115314627940352>",
    "salute": "<:salute:1293115316506722365>",
    "smh": "<:smh:1293115318566256744>",
    "sweats": "<:sweats:1293115320382390337>",
    "thonk": "<:thonk:1293115322672349315>",
    "pls": "<:pls:1293115325809950811>",
    "hesrightyouknow": "<:hesrightyouknow:1293115328800231470>",
    "notthis": "<:notthis:1293115337990209608>",
    "peeposip": "<:peeposip:1293115339894165515>",
    "sippy": "<:sippy:1293115342725451809>",
    "stare": "<:stare:1293115345212801086>",
    "fuyu": "<:fuyu:1293115346898780171>",
    "sip": "<:sip:1293115349385875517>",
    "konata": "<a:konata:1293115351701131275>",
    "weee": "<a:weee:1293115354553253939>",
    "note": "<:note:1293115357220831294>",
    "nod": "<a:nod:1293115359280496661>",
    "peek": "<a:peek:1293115361700483073>",
    "02skull": "<a:02skull:1293115363533258853>",
    "thinky": "<:thinky:1293115367610253312>",
    "shrugs": "<:shrugs:1293115370126839870>",
    "smuggest": "<:smuggest:1293151775746166794>",
    "ChinoSugoi": "<:ChinoSugoi:1293151777473957888>",
    "EmiWow": "<:EmiWow:1293151779055341569>",
    "pat": "<:pat:1293151781550952493>",
    "AMankowave": "<a:AMankowave:1293151785783132212>",
    "WOW": "<:WOW:1293151787783819296>",
    "hehe": "<:hehe:1293151791508095056>",
    "hmmm": "<:hmmm:1293151793357787167>",
    "wow": "<:wow:1293151795228577854>",
    "smooth": "<:smooth:1293151797388771449>",
    "hawawa": "<:hawawa:1293151800740024350>",
    "SHAME": "<:SHAME:1293151804024033281>",
    "dogekek": "<:dogekek:1293151809224970323>",
    "nenewat": "<:nenewat:1293151811342958612>",
    "nani": "<:nani:1293151815663357983>",
    "looking": "<:looking:1293151817710178324>",
    "woah": "<:woah:1293151819601543218>",
    "hugsss": "<:hugsss:1293151821333794827>",
    "paku": "<:paku:1293151827931693099>",
    "shruge": "<:shruge:1293151829567340607>",
    "yesthis": "<:yesthis:1293151831911825460>",
    "aniKittyLove": "<a:aniKittyLove:1293151834600505416>",
    "sugoi": "<:sugoi:1293151836802646089>",
    "lay": "<:lay:1293151843244970034>",
    "ayayaweird": "<:ayayaweird:1293151846592151727>",
    "hyperthonk": "<:hyperthonk:1293151849389490226>",
    "thinkies": "<:thinkies:1293151852531024007>",
    "nix": "<:nix:1293151854619922473>",
    "linux": "<:linux:1293151858835197952>",
    "kfc": "<:kfc:1293151860827492404>",
    "hyprland": "<:hyprland:1293151862899609674>",
    "trollface": "<:trollface:1293151865273323631>",
    "beanomg": "<:beanomg:1293151868863774771>",
    "heheBlue": "<:heheBlue:1293151873951338518>",
    "pout": "<:pout:1293151876166062111>",
    "youcalled": "<:youcalled:1293151877617418314>",
    "rokaGimme": "<:rokaGimme:1293151879861375076>",
    "ramHeh": "<:ramHeh:1293151883464282176>",
    "blushshy": "<:blushshy:1293151885544390708>",
    "snod": "<a:snod:1293151887599734794>",
    "emma": "<:emma:1293151891177472031>",
    "confusion": "<:confusion:1293151893077491744>",
    "KannaSpook": "<:KannaSpook:1293151895417782313>",
    "kannainspect": "<:kannainspect:1293151897829773342>",
    "cheeky": "<:cheeky:1293151901243801683>",
    "ayes": "<:ayes:1293151905156960306>",
    "angerystare": "<:angerystare:1293151908739153992>",
    "ano": "<:ano:1293151910618075197>",
    "AlexiaSmug": "<:AlexiaSmug:1293151912765685780>",
    "AlexiaTea": "<:AlexiaTea:1293151916540297287>",
    "AsuREEE": "<:AsuREEE:1293151918859878440>",
    "AsunaJoy": "<:AsunaJoy:1293151922093555743>",
    "AsunaWave": "<:AsunaWave:1293151924094238770>",
    "AtlaKawaii": "<:AtlaKawaii:1293151926023880797>",
    "BBSmile": "<:BBSmile:1293151929257426954>",
    "MahiruAYAYA": "<:MahiruAYAYA:1293151932793356349>",
    "MeguShake": "<a:MeguShake:1293151936106725399>",
    "GlassBored": "<:GlassBored:1293151938015395840>",
    "MionWait": "<:MionWait:1293151939978330193>",
    "Prayge": "<:Prayge:1293151941689475133>",
    "Think": "<:Think:1293151945879584770>",
    "02smilepeek": "<:02smilepeek:1293151950086344765>",
    "blushing": "<:blushing:1293151951420395592>",
    "dealwithit": "<:dealwithit:1293151953571811441>",
    "monkahmm": "<:monkahmm:1293151956046712864>",
    "monkas": "<:monkas:1293151958160638073>",
    "raidenShotgun": "<:raidenShotgun:1293151960052269107>",
    "ramfive": "<:ramfive:1293151962010751048>",
    "remfive": "<:remfive:1293151965924163715>",
    "surprisegif": "<a:surprisegif:1293151971405991947>",
    "wut": "<:wut:1293151974639927348>",
    "yaygif": "<a:yaygif:1293151978330783866>",
    "yay": "<:yay:1293151981963313162>",
    "yuisip": "<:yuisip:1293151985071165491>",
    "woke": "<:woke:1293151988971999282>",
    "AoiSlain": "<:AoiSlain:1293151992235163732>",
    "HappyBun": "<a:HappyBun:1293151996228010116>",
    "MenheraBonk": "<a:MenheraBonk:1293151998996123669>",
    "MenheraFlower": "<:MenheraFlower:1293152001860829228>",
    "MenheraFlowers": "<:MenheraFlowers:1293152005292036162>",
    "MenheraNod": "<a:MenheraNod:1293152009603645481>",
    "MenheraNya3": "<:MenheraNya3:1293152012808093738>",
    "MenheraPull": "<:MenheraPull:1293152015928524831>",
    "WatameNoNoNoNo": "<a:WatameNoNoNoNo:1293152022937468970>",
    "ShiggySad": "<:ShiggySad:1293152026498306150>",
    "neppy": "<a:neppy:1293152030105534465>",
    "vennieflower": "<:vennieflower:1293152033796259942>",
    "venniebwaah": "<:venniebwaah:1293152037688578069>",
    "vennieheart": "<:vennieheart:1293152040591163465>",
    "venniehehe": "<:venniehehe:1293152044110184460>",
    "venniehug": "<:venniehug:1293152047683866698>",
    "vennielove": "<:vennielove:1293152050305306704>",
    "venniepat": "<:venniepat:1293152053111160846>",
    "venniesad": "<:venniesad:1293152056919592962>",
    "worriedsakura": "<:worriedsakura:1293152060476358666>",
    "yesyesyes": "<a:yesyesyes:1293152064372867123>",
    "sawahyay": "<a:sawahyay:1293152067510079573>",
    "AnnaAngy": "<:AnnaAngy:1293152070651871253>",
    "AnnaBruh": "<:AnnaBruh:1293152073449209887>",
    "AnnaOop": "<:AnnaOop:1293152076569907211>",
    "AnnaMad": "<:AnnaMad:1293152079539470368>",
    "AnnaPartySmall": "<:AnnaPartySmall:1293152082714558475>",
    "AnnaCheer": "<:AnnaCheer:1293152085545844738>",
    "AnnaClueless": "<:AnnaClueless:1293152089115201597>",
    "AnnaSmirk2": "<:AnnaSmirk2:1293152092105736236>",
    "AnnaSmirkTheThirdComing": "<:AnnaSmirkTheThirdComing:1293152095263916132>",
    "AnnaCopium": "<:AnnaCopium:1293152098224963668>",
    "AnnaDisgust": "<:AnnaDisgust:1293152101316300842>",
    "AnnaFunny": "<:AnnaFunny:1293152105703407668>",
    "AnnaUpset": "<:AnnaUpset:1293152109465829386>",
    "AnnaWave": "<:AnnaWave:1293152112477343774>",
    "AnnaHuh": "<:AnnaHuh:1293152115484655680>",
    "KajuNod": "<a:KajuNod:1293152120446652501>",
    "KajuNervous": "<:KajuNervous:1293152123063898174>",
    "KajuKnife": "<:KajuKnife:1293152126423273522>",
    "KajuBlush": "<:KajuBlush:1293152129254555649>",
    "KajuWonder": "<:KajuWonder:1293152132337242163>",
    "KomariSip": "<:KomariSip:1293153117109616650>",
    "KomariYes": "<:KomariYes:1293153120066605067>",
    "KomariSkillIssue": "<a:KomariSkillIssue:1293153125208948791>",
    "KomariThat": "<:KomariThat:1293153128283377728>",
    "MobukoAwkward": "<:MobukoAwkward:1293153131361734696>",
    "NukkunAngry": "<:NukkunAngry:1293153134876557347>",
    "RikoDerp": "<:RikoDerp:1293153138366484490>",
    "Noted": "<a:Noted:1293153144619925554>",
    "Sad": "<:Sad:1293153148487340054>",
    "Roger": "<:Roger:1293153151389532171>",
    "cirpat": "<:cirpat:1293153155021930499>",
    "cirno_thinking": "<:cirno_thinking:1293153158444355608>",
    "gurawave": "<a:gurawave:1293153161187426325>",
    "shrug": "<a:shrug:1293153166468059179>",
    "xd": "<:xd:1293153169878286337>",
    "ChinoHuh": "<:ChinoHuh:1293153178358910997>",
    "ChinoStare": "<:ChinoStare:1293153181957754890>",
    "FuyuEvil": "<:FuyuEvil:1293153185514655826>",
    "FUYAYA": "<:FUYAYA:1293153189796909066>",
    "fear": "<:fear:1293153193295089718>",
    "AAAAA": "<a:AAAAA:1293153199863103518>",
    "AnzuKimoi": "<:AnzuKimoi:1293153203206094848>",
    "NadeDrool": "<:NadeDrool:1293153206876246026>",
    "RaphielOhMy": "<:RaphielOhMy:1293153209942278207>",
    "VignetteEhehe": "<:VignetteEhehe:1293153213381607454>",
    "bullied": "<:bullied:1293153217001033801>",
    "grr": "<a:grr:1293153222772391957>",
    "fingerguns": "<:fingerguns:1293153225477849140>",
    "fufufu": "<:fufufu:1293153228825034765>",
    "dead": "<:dead:1293153231639416883>",
    "blushy": "<:blushy:1293153234978078800>",
    "illyaStare": "<a:illyaStare:1293153238484254822>",
    "laffeythumb": "<a:laffeythumb:1293153245145071637>",
    "laugh": "<a:laugh:1293153249519734787>",
    "loser": "<:loser:1293153258855989269>",
    "kannasip": "<:kannasip:1293153261888602143>",
    "kannapog": "<:kannapog:1293153265323868160>",
    "heheXD": "<:heheXD:1293153268339445832>",
    "kimoi": "<:kimoi:1293153271732637788>",
    "megugun": "<:megugun:1293153275318894646>",
    "owoUwU": "<a:owoUwU:1293153281018695790>",
    "sataniaLaugh": "<a:sataniaLaugh:1293153284931977246>",
    "servalspooked": "<:servalspooked:1293153288400666665>",
    "wanwan": "<:wanwan:1293153291244671039>",
    "tunes": "<a:tunes:1293153294897647676>",
    "uMu": "<:uMu:1293153298068803604>",
    "yuipeace": "<a:yuipeace:1293153301767913502>",
    "weebSmash": "<a:weebSmash:1293153306566201367>",
    "smalldick": "<:smalldick:1293153308805959711>",
    "KomariHeh": "<a:KomariHeh:1293153313511964712>",
    "bonk": "<:bonk:1293153316880121907>",
    "AAABABABABA": "<a:AAABABABABA:1293154398012444724>",
    "EHEHE": "<:EHEHE:1293154401011241022>",
    "GearScare": "<:GearScare:1293154405083910227>",
    "LoliBonk": "<a:LoliBonk:1293154408695074856>",
    "LoliRub": "<a:LoliRub:1293154412331798628>",
    "NepConcerned": "<a:NepConcerned:1293154415884243009>",
    "NepCurious": "<:NepCurious:1293154419415711777>",
    "NepGah": "<:NepGah:1293154422888861777>",
    "NepGasm": "<:NepGasm:1293154426122539070>",
    "NepNap": "<:NepNap:1293154429360410677>",
    "NepRage": "<:NepRage:1293154433630343211>",
    "NepSnug": "<:NepSnug:1293154437224988684>",
    "NepStare": "<:NepStare:1293154440689483796>",
    "NepThink": "<:NepThink:1293154443776360530>",
    "NepYay": "<:NepYay:1293154447022755881>",
    "OhGearMe": "<:OhGearMe:1293154450197708883>",
    "PlutieStare": "<:PlutieStare:1293154453230321694>",
    "VanillaStareSide": "<:VanillaStareSide:1293154457173098537>",
    "WHAT": "<:WHAT:1293154460499050606>",
    "really": "<:really:1293154474361229332>",
    "lewd": "<:lewd:1293154481009201276>",
    "kissu": "<:kissu:1293154484129759234>",
    "hug": "<:hug:1293154487783129129>",
    "confused": "<:confused:1293154495873679453>",
    "XD": "<:XD:1293154499396894730>",
    "staryn": "<:staryn:1293154502702268519>",
    "AMAwoo": "<:AMAwoo:1293154508708511744>",
    "AMAquaSad": "<:AMAquaSad:1293154512093319223>",
    "AMHeadpat": "<:AMHeadpat:1293154515109023774>",
    "AMGiveMe": "<:AMGiveMe:1293154518347026463>",
    "AMGWagnwNatsukiBlush": "<:AMGWagnwNatsukiBlush:1293154521035571234>",
    "AMFingerGun": "<:AMFingerGun:1293154524348940358>",
    "AMChikaLove": "<:AMChikaLove:1293154527637278812>",
    "AMNoThanks": "<a:AMNoThanks:1293154530405646409>",
    "AMNo": "<a:AMNo:1293154534876512308>",
    "AMNyanPat": "<:AMNyanPat:1293154538093547543>",
    "AMbaka": "<:AMbaka:1293154542481047583>",
    "AMchikablush": "<:AMchikablush:1293154546075566113>",
    "AMchikastressed": "<a:AMchikastressed:1293154550559150091>",
    "AMchikaping": "<a:AMchikaping:1293154554808107058>",
    "AMevilsmirk": "<:AMevilsmirk:1293154558243110952>",
    "AMemilialaugh": "<:AMemilialaugh:1293154561371934741>",
    "AMkaguyapout": "<:AMkaguyapout:1293154564178186320>",
    "AMmeguhappy": "<:AMmeguhappy:1293154567332298802>",
    "AMmikafingerspin": "<a:AMmikafingerspin:1293154570486415390>",
    "AMloserblehh": "<:AMloserblehh:1293154573438943283>",
    "AMlove": "<:AMlove:1293154578157801513>",
    "AMhappu": "<:AMhappu:1293154581911703646>",
    "AMsenkouwu": "<:AMsenkouwu:1293154585766133772>",
    "AMsleepyrem": "<:AMsleepyrem:1293154589113188394>",
    "AMwhat": "<:AMwhat:1293154592280023181>",
    "AMyawn": "<:AMyawn:1293154595664826420>",
    "AMsmugsmirk": "<:AMsmugsmirk:1293154599120666645>",
    "AMsmugwatch": "<:AMsmugwatch:1293154602006351974>",
    "AMsmugstare": "<:AMsmugstare:1293154605965901906>",
    "AMshy": "<:AMshy:1293154610009341964>",
    "AMshinobulove2": "<:AMshinobulove2:1293154612966199308>",
    "AyakaPout": "<:AyakaPout:1293154616397271170>",
    "ANGREEEEPING": "<a:ANGREEEEPING:1293154619580743706>",
    "AYAYANO": "<:AYAYANO:1293154623904940103>",
    "KurumiThonk": "<:KurumiThonk:1293154625909821443>",
    "KyoukoLaugh": "<:KyoukoLaugh:1293154629869109248>",
    "JahyThink": "<:JahyThink:1293154633757491211>",
    "JahyCry": "<:JahyCry:1293154636173410326>",
    "CuteBlush": "<a:CuteBlush:1293154639146909748>",
    "WetChiyo": "<:WetChiyo:1293154642355814400>",
    "ThinkingIsHard": "<:ThinkingIsHard:1293154645123924010>",
    "TaigaYaaay": "<a:TaigaYaaay:1293154648462590005>",
    "NotLikeHaachama": "<a:NotLikeHaachama:1293154652556103711>",
    "NotLikeSagiri": "<:NotLikeSagiri:1293154655760547881>",
    "illyaHyperTilted": "<a:illyaHyperTilted:1293154660575739924>",
    "illyaTilted": "<a:illyaTilted:1293154663582924843>",
    "karenblush": "<a:karenblush:1293154672768712716>",
    "karenshock": "<:karenshock:1293154676539134057>",
    "karenwave": "<:karenwave:1293154678569173095>",
    "hugkon": "<a:hugkon:1293154681861705782>",
    "tenkaSmug": "<:tenkaSmug:1293154685368143923>",
    "tenkaLove": "<:tenkaLove:1293154688065081405>",
    "tenkaDab": "<:tenkaDab:1293154690174816318>",
    "tenkaAngry": "<:tenkaAngry:1293154693119217694>",
    "Koshi_Tired": "<:Koshi_Tired:1293154696214872105>",
    "Koshi_Teary": "<:Koshi_Teary:1293154700581142528>",
    "Koshi_Shy": "<:Koshi_Shy:1293154704104099901>",
    "Neko_Blush": "<:Neko_Blush:1293154707308810383>",
    "Neko_Shock2": "<:Neko_Shock2:1293154710798471258>",
    "Neko_Shock": "<:Neko_Shock:1293154713683890187>",
    "Neko_Scared2": "<:Neko_Scared2:1293154717127671818>",
    "Tanuki_Panic2": "<:Tanuki_Panic2:1293154720705417226>",
    "Tanuki_Panic": "<:Tanuki_Panic:1293154724266246225>",
    "IbarakiNom": "<a:IbarakiNom:1293154726912856146>",
    "CasGilShake": "<a:CasGilShake:1293154734240170015>",
    "HowdyKita": "<:HowdyKita:1293154741458829354>",
    "Kageteyebrows": "<a:Kageteyebrows:1293154745652871211>",
    "KagetoraScarilyCute": "<a:KagetoraScarilyCute:1293154751567101952>",
    "YAMERO": "<a:YAMERO:1293154755924721694>",
    "abbywow": "<:abbywow:1293154764628168757>",
    "LalterEyebrows": "<a:LalterEyebrows:1293154768591523881>",
    "disgust": "<:disgust:1293154771598970961>",
    "ereshwoah": "<:ereshwoah:1293154774493167668>",
    "danzoushhh": "<:danzoushhh:1293154777575985255>",
    "bbroll": "<:bbroll:1293154781254254614>",
    "helenalewd": "<:helenalewd:1293154790825529384>",
    "himebullycri": "<:himebullycri:1293154794256470048>",
    "illyaPanic": "<a:illyaPanic:1293154798530596874>",
    "ishtararguing": "<a:ishtararguing:1293154802024579092>",
    "ishtarew": "<a:ishtarew:1293154805480423424>",
    "jackhappy": "<:jackhappy:1293154809628852226>",
    "jeannethonk": "<:jeannethonk:1293154813454057542>",
    "kamacringe": "<:kamacringe:1293154816767557702>",
    "serenitywut": "<:serenitywut:1293154819766222909>",
    "neroheh": "<:neroheh:1293154827467100251>",
    "nerohappydance": "<a:nerohappydance:1293154832311652455>",
    "umudealwithit": "<:umudealwithit:1293154834987352077>",
    "AmeliaWhat": "<:AmeliaWhat:1293154965547909150>",
    "KoyoriStunned": "<:KoyoriStunned:1293154969171529749>",
    "ChisatoWink": "<:ChisatoWink:1293154972300611688>",
    "HazukiThumbsUp": "<:HazukiThumbsUp:1293154975089954900>",
    "HehHehHeh": "<:HehHehHeh:1293154978080227328>",
    "HikariPlease": "<:HikariPlease:1293154981553242176>",
    "HishiroSmile": "<:HishiroSmile:1293154985592360960>",
    "Kaguyahai": "<:Kaguyahai:1293154988759187509>",
    "Skuish": "<a:Skuish:1293154992714154044>",
    "TokiyukiPhew": "<:TokiyukiPhew:1293154995939577929>",
    "ShinoScared": "<:ShinoScared:1293154999211134976>",
    "Sagiridisgust": "<:Sagiridisgust:1293155002008866860>",
    "SaberCry": "<:SaberCry:1293155005104132128>",
    "YukiKyaa": "<:YukiKyaa:1293155008937721899>",
    "bocchihands": "<:bocchihands:1293155012251222051>",
    "ayayaya": "<:ayayaya:1293155016130957322>",
    "ehehehe": "<:ehehehe:1293155019948036156>",
    "excite": "<:excite:1293155024834396163>",
    "konatathink": "<:konatathink:1293155028294434837>",
    "illyapeace": "<:illyapeace:1293155031645814785>",
    "hutaohmm": "<:hutaohmm:1293155035412434976>",
    "holo": "<:holo:1293155038390386718>",
    "kotowave": "<:kotowave:1293155041636646986>",
    "kumikosmug": "<:kumikosmug:1293155045667377204>",
    "luluquizzical": "<a:luluquizzical:1293155052718129163>",
    "maomaodisgust": "<:maomaodisgust:1293155055360544769>",
    "meltheart": "<:meltheart:1293155058728566797>",
    "nanamiblush": "<:nanamiblush:1293155062943584337>",
    "mugistronk": "<:mugistronk:1293155066685034497>",
    "teehee": "<:teehee:1293155069646213130>",
    "minorismug": "<:minorismug:1293155072070520853>",
    "wawawhatAoi": "<:wawawhatAoi:1293155075619033130>",
    "yuishrug": "<:yuishrug:1293155078697517109>",
}


async def fetch_random_emoji() -> str:
    random_emoji = random.choice(list(emoji_dict.values()))
    if not os.getenv("NO_EMOJIS"):
        return str(random_emoji)
    else:
        return ""
