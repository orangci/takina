import nextcord
from nextcord.ext import commands
import re
from __main__ import EMBED_COLOR

class LinkPreview(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message_url_pattern = re.compile(r"https://discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)")

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        # Ignore messages from bots
        if message.author.bot:
            return

        # Search for the first linked message URL in the message content
        match = self.message_url_pattern.search(message.content)
        if not match:
            return

        guild_id, channel_id, message_id = match.groups()

        # Ensure the link is within the same guild
        if int(guild_id) != message.guild.id:
            return

        # Retrieve the channel and message objects
        channel = message.guild.get_channel(int(channel_id))
        if not channel:
            return

        try:
            linked_message = await channel.fetch_message(int(message_id))
        except nextcord.NotFound:
            return

        # Check for Manage Webhooks permission
        if channel.permissions_for(message.guild.me).manage_webhooks:
            # Set up a webhook with the linked message author's name and avatar
            webhook = await channel.create_webhook(name=linked_message.author.display_name)

            # Send the linked message content through the webhook
            await webhook.send(
                content=linked_message.content,
                username=linked_message.author.display_name,
                avatar_url=linked_message.author.avatar.url if linked_message.author.avatar else None
            )

            # Clean up: delete the webhook after sending the message
            await webhook.delete()
        else:
            # If no Manage Webhooks permission, send the linked message in an embed
            embed = nextcord.Embed(
                description=linked_message.content or "*No text content*",
                color=EMBED_COLOR,
                timestamp=linked_message.created_at,
            )
            embed.set_author(
                name=linked_message.author.display_name,
                icon_url=linked_message.author.avatar.url if linked_message.author.avatar else None
            )
            embed.set_footer(text=f"Linked from #{linked_message.channel.name}")
            
            if embed.description == "*No text content*":
                return
            await message.channel.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(LinkPreview(bot))
