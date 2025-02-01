import nextcord
from nextcord.ext import commands
from config import *


class Snipe(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sniped_messages = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        self.sniped_messages[message.channel.id] = {
            "content": message.content,
            "author": message.author,
            "time": message.created_at,
            "attachments": message.attachments,
        }

    @commands.command(
        name="snipe",
        help="Snipe the last deleted message in a channel. \nUsage: `snipe`.\nRequires the Moderator role or higher."
    )
    async def snipe(self, ctx: commands.Context):
        nolifer_role_id = 1235232374862643301  
        nolifer_role = ctx.author.guild.get_role(nolifer_role_id)

        if nolifer_role is None:
            await ctx.send("The No Lifer role does not exist in this server.")
            return

        has_moderator_role = nolifer_role in ctx.author.roles
        if not has_moderator_role:
            if ctx.author.top_role.position >= nolifer_role.position:
                pass 
            else:
                await ctx.send("You need the Moderator role or higher to use this command.")
                return
            
        sniped_message = self.sniped_messages.get(ctx.channel.id)

        # Handle if there's neither text nor attachments
        if not sniped_message or (
            not sniped_message["content"] and not sniped_message["attachments"]
        ):
            embed = nextcord.Embed(
                description="There's nothing to snipe!",
                color=EMBED_COLOR,
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Create embed for sniped message
        embed = nextcord.Embed(
            description=sniped_message["content"] or "*No text content*",
            color=EMBED_COLOR,
            timestamp=sniped_message["time"],
        )
        embed.set_author(
            name=f"{sniped_message['author'].display_name}",
            icon_url=sniped_message["author"].avatar.url,
        )
        embed.set_footer(text=f"Deleted in #{ctx.channel.name}")

        embed_list = [embed]

        # Check if there are attachments (e.g. images)
        if sniped_message["attachments"]:
            embed.url = "https://orangc.xyz"
            for attachment in sniped_message["attachments"]:
                if "image" in str(attachment.content_type):
                    if not embed.image:
                        embed.set_image(url=attachment.url)
                    else:
                        new_embed = nextcord.Embed(color=EMBED_COLOR)
                        new_embed.set_image(url=attachment.url)
                        new_embed.url = embed.url
                        embed_list.append(new_embed)

        await ctx.reply(embeds=embed_list, mention_author=False)


def setup(bot):
    bot.add_cog(Snipe(bot))
