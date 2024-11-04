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
            "attachments": message.attachments,
        }

    @commands.command(
        name="snipe",
        help="Snipe the last deleted message in a channel. \nUsage: `snipe`.",
    )
    @commands.has_permissions(manage_messages=True)
    async def snipe(self, ctx: commands.Context):
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

        # Check if there are attachments (e.g. images)
        if sniped_message["attachments"]:
            for attachment in sniped_message["attachments"]:
                if attachment.filename.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif")
                ):
                    # Set image in embed
                    embed.set_image(url=attachment.url)
                else:
                    # Add non-image attachment as a clickable link
                    attachments_list += f"\n [{attachment.filename}]({attachment.url})"
                embed.add_field(
                    name="Attachments", value=attachments_list, inline=False
                )

        await ctx.reply(embed=embed, mention_author=False)


def setup(bot):
    bot.add_cog(Snipe(bot))
