import nextcord
from nextcord.ext import commands
from __main__ import EMBED_COLOR


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
        }

    @commands.command(name="snipe")
    @commands.has_permissions(manage_messages=True)
    async def snipe(self, ctx: commands.Context):
        """Snipes and displays the last deleted message in an embed."""
        sniped_message = self.sniped_messages.get(ctx.channel.id)

        if not sniped_message:
            await ctx.reply("There's nothing to snipe!", mention_author=False)
            return

        embed = nextcord.Embed(
            description=sniped_message["content"],
            color=EMBED_COLOR,
            timestamp=sniped_message["time"],
        )
        embed.set_author(
            name=f"{sniped_message['author'].display_name}",
            icon_url=sniped_message["author"].avatar.url,
        )
        embed.set_footer(text=f"Deleted in #{ctx.channel.name}")

        await ctx.reply(embed=embed, mention_author=False)


def setup(bot):
    bot.add_cog(Snipe(bot))
