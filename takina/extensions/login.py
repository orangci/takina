import nextcord
from nextcord.ext import commands
import uuid


class LoginButton(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        # Generate a dynamic UUID
        dynamic_uuid = str(uuid.uuid4())
        
        # Add the button as a URL button
        self.add_item(
            nextcord.ui.Button(
                label="Login",
                style=nextcord.ButtonStyle.link,  # Use link style for URL button
                url=f"https://anna-oauth.p2pb.dev/login?uuid={dynamic_uuid}"  # URL with dynamic UUID
            )
        )


class Login(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user}")

    @commands.command()
    async def login(self, ctx):
        view = LoginButton()
        await ctx.send("Click the button to login:", view=view)


def setup(bot):
    bot.add_cog(Login(bot))
