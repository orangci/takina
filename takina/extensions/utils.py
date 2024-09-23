import re
from nextcord.ext import commands
import nextcord
from nextcord import SlashOption

def extract_user_id(mention: str) -> str:
    match = re.match(r'<@!?(\d+)>', mention)
    if match:
        return match.group(1)
    return None


class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot: commands.Bot = bot
    
    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Ping the bot."""
        latency = round(self._bot.latency * 1000)
        await ctx.reply(f"Success! Takina is awake. Ping: {latency}ms", mention_author=False)

    @commands.command()
    @commands.has_permissions(moderate_members=True,manage_messages=True)
    async def send(
        self,
        ctx: commands.Context,
        channel: nextcord.TextChannel = None,
        *,
        message: str,
    ):
        """Send a message as Takina."""
        if channel and message:
            await channel.send(message)
        elif message:
            await ctx.reply(message, mention_author=False)
        else:
            await ctx.reply("Please provide a message and channel to use this command.", mention_author=False)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int):
        """Purges a specified number of messages."""

        # Ensure the number is a positive integer
        if amount <= 0:
            await ctx.reply("Please specify a positive number of messages to purge.", mention_author=False)
            return

        deleted = await ctx.channel.purge(limit=amount)
        await ctx.reply(f"Successfully purged {len(deleted)} messages.", delete_after=3, mention_author=False)

    @commands.command(aliases=["setnick"])
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx: commands.Context, member: str = None, *, nickname: str = None):
        if member is None:
            member = ctx.author
        else:
            user_id = extract_user_id(member)
            if user_id:
                member = ctx.guild.get_member(int(user_id))
            else:
                member = nextcord.utils.get(ctx.guild.members, name=member) or nextcord.utils.get(ctx.guild.members, display_name=member)

        if member is None:
            await ctx.reply("Member not found. Please provide a valid username or display name.", mention_author=False)
            return
        if not member:
            await ctx.reply("Please mention a member to change their nickname. Usage: `nick @member [nickname]`", mention_author=False)
            return

        if member == ctx.author:
            await ctx.reply("You can't change your own nickname using this command.", mention_author=False)
            return

        if member == ctx.guild.owner:
            await ctx.reply("You can't change the server owner's nickname.", mention_author=False)
            return

        if member.top_role >= ctx.author.top_role:
            await ctx.reply("You can't change the nickname of someone with a higher or equal role than yours.", mention_author=False)
            return

        if member.top_role >= ctx.guild.me.top_role:
            await ctx.reply("I can't change the nickname of someone with a higher or equal role than mine.", mention_author=False)
            return

        if not nickname:
            nickname = member.name

        try:
            await member.edit(nick=nickname)
            await ctx.reply(f"**{member.name}**'s nickname has been changed to **{nickname}**.", mention_author=False)
        except nextcord.Forbidden:
            await ctx.reply("I don't have permission to change this member's nickname.", mention_author=False)
        except nextcord.HTTPException:
            await ctx.reply("An error occurred while trying to change the nickname.", mention_author=False)

class UtilsSlash(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot: commands.Bot = bot

    @nextcord.slash_command(name="ping", description="Ping the bot.")
    async def ping(self, interaction: nextcord.Interaction):
        """Ping the bot."""
        latency = round(self._bot.latency * 1000)
        await interaction.response.send_message(f"Success! Takina is awake. Ping: {latency}ms")

    @nextcord.slash_command(name="send", description="Send a message as Takina.")
    @commands.has_permissions(moderate_members=True,manage_messages=True)
    async def send(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = SlashOption(description="Channel to send the message", required=True),
        message: str = SlashOption(description="Message to send", required=True),
    ):
        """Send a message as Takina."""
        if channel and message:
            await channel.send(message)
            await interaction.response.send_message("Message sent!", ephemeral=True)
        elif message:
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.response.send_message("Please provide a message and channel to use this command.", ephemeral=True)

    @nextcord.slash_command(name="purge", description="Purges a specified number of messages.")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, interaction: nextcord.Interaction, amount: int = SlashOption(description="Number of messages to purge", required=True)):
        """Purges a specified number of messages."""
        if amount <= 0:
            await interaction.response.send_message("Please specify a positive number of messages to purge.", ephemeral=True)
            return

        deleted = await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"Successfully purged {len(deleted)} messages.", ephemeral=True)

    @nextcord.slash_command(name="nick", description="Change a member's nickname.")
    @commands.has_permissions(manage_nicknames=True)
    async def nick(
        self,
        interaction: nextcord.Interaction,
        member: str = SlashOption(description="Member to change the nickname for", required=True),
        nickname: str = SlashOption(description="New nickname"),
    ):
        """Change a member's nickname."""
        if member is None:
            member = interaction.user
        else:
            user_id = extract_user_id(member)
            if user_id:
                member = interaction.guild.get_member(int(user_id))
            else:
                member = nextcord.utils.get(interaction.guild.members, name=member) or nextcord.utils.get(interaction.guild.members, display_name=member)

        if member is None:
            await interaction.response.send_message("Member not found. Please provide a valid username or display name.", ephemeral=True)
            return

        if member == interaction.user:
            await interaction.response.send_message("You can't change your own nickname using this command.", ephemeral=True)
            return

        if member == interaction.guild.owner:
            await interaction.response.send_message("You can't change the server owner's nickname.", ephemeral=True)
            return

        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You can't change the nickname of someone with a higher or equal role than yours.", ephemeral=True)
            return

        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I can't change the nickname of someone with a higher or equal role than mine.", ephemeral=True)
            return

        if not nickname:
            nickname = member.name

        try:
            await member.edit(nick=nickname)
            await interaction.response.send_message(f"**{member.name}**'s nickname has been changed to **{nickname}**.", ephemeral=True)
        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to change this member's nickname.", ephemeral=True)
        except nextcord.HTTPException:
            await interaction.response.send_message("An error occurred while trying to change the nickname.", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(Utils(bot))
    bot.add_cog(UtilsSlash(bot))
