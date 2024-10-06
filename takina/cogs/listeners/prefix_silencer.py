import nextcord
from nextcord.ext import commands
import os

class PrefixSilencer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.prefix = os.getenv("PREFIX", "?")
        
        self.silencer_aliases = [self.prefix * i for i in range(1, 15)]

        self._add_prefix_silencer_command()

    def _add_prefix_silencer_command(self):
        """Dynamically add the prefix_silencer command with aliases."""
        @commands.command(name="prefix_silencer", aliases=self.silencer_aliases)
        async def prefix_silencer(ctx: commands.Context):
            pass
        
        self.bot.add_command(prefix_silencer)

def setup(bot: commands.Bot):
    bot.add_cog(PrefixSilencer(bot))
