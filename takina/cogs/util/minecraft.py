import aiohttp
import nextcord
import base64
from nextcord.ext import commands
from datetime import datetime
from io import BytesIO
from __main__ import EMBED_COLOR

# Helper function for API requests
async def request(url, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.request("GET", url, *args, **kwargs) as response:
            return await response.json()

class MinecraftServerStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def fetch_server_info(self, server_name: str):
        url = f"https://api.mcstatus.io/v2/status/java/{server_name}"

        try:
            data = await request(url)
            if data:
                return data

        except Exception as e:
            raise e

    @commands.command(aliases=["mc"])
    async def mcstatus(self, ctx: commands.Context, *, server_name: str):
        """Command for displaying a Minecraft server's status. Usage: `mc mc.orangc.xyz`."""
        try:
            server = await self.fetch_server_info(server_name)
            if server:
                title = server.get("host")    
                embed = nextcord.Embed(title=title, color=EMBED_COLOR)

                if server.get("players"):
                    embed.add_field(name="Players", value=f"{server['players']['online']}/{server['players']['max']}")
                if server.get("version"):
                    embed.add_field(name="Version", value=server["version"]["name_clean"])
                if server.get("motd"):
                    embed.add_field(name="MOTD", value=server["motd"]["clean"], inline=False)

                if server.get("icon"):
                    icon_data = server["icon"].split(",")[1]
                    image_data = base64.b64decode(icon_data)
                    image = BytesIO(image_data)
                    file = nextcord.File(image, filename="server_icon.png")
                    embed.set_thumbnail(url="attachment://server_icon.png")
                    await ctx.send(file=file, embed=embed)
                else:
                    await ctx.send(embed=embed)
            else:
                embed = nextcord.Embed(
                    description="Server not found.",
                    color=nextcord.Color.red(),
                )
                await ctx.send(embed=embed)

        except Exception as e:
            embed = nextcord.Embed(title="Error", description=str(e), color=nextcord.Color.red())
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(MinecraftServerStatus(bot))
