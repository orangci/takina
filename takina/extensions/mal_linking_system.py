import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View
from aiohttp import ClientSession
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
import secrets
import base64
import asyncio

class MAL_Linking_System(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client_id = os.getenv("MAL_CLIENT_ID")
        self.client_secret = os.getenv("MAL_CLIENT_SECRET")
        self.redirect_uri = os.getenv("MAL_REDIRECT_URI")
        self.code_verifier = None
        self.oauth_url = "https://myanimelist.net/v1/oauth2/authorize"

    def generate_pkce(self):
        """Generates the PKCE code_verifier and code_challenge"""
        # Generate code_verifier
        self.code_verifier = secrets.token_urlsafe(43)  # Minimum 43 chars
        # Base64 URL-safe encode the code_verifier (PKCE plain method used by MyAnimeList)
        code_challenge = base64.urlsafe_b64encode(self.code_verifier.encode()).decode().rstrip("=")
        return code_challenge

    @commands.command(name="admin_welcome")
    async def admin_welcome(self, ctx: commands.Context):
        """Sends a welcome message with a button to link MyAnimeList account"""
        button = Button(label="Link MyAnimeList", style=nextcord.ButtonStyle.primary)
        button.callback = self.link_myanimelist
        view = View()
        view.add_item(button)

        await ctx.send("Welcome! Link your MyAnimeList account below:", view=view)

    async def link_myanimelist(self, interaction: nextcord.Interaction):
        """Handle the button press and send the OAuth2 link to the user"""
        code_challenge = self.generate_pkce()

        oauth_url_with_state = (
            f"{self.oauth_url}?response_type=code&client_id={self.client_id}"
            f"&state={interaction.user.id}&redirect_uri={self.redirect_uri}"
            f"&code_challenge={code_challenge}&code_challenge_method=plain"
        )

        await interaction.response.send_message(
            f"Click the link to link your MyAnimeList account: {oauth_url_with_state}",
            ephemeral=True
        )

    async def handle_oauth2_callback(self, code: str, discord_id: int):
        """Handles the OAuth2 callback after user authorizes the app"""
        token_url = "https://myanimelist.net/v1/oauth2/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": self.code_verifier  # Send the code_verifier back as part of PKCE
        }

        try:
            async with ClientSession() as session:
                async with session.post(token_url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        access_token = token_data['access_token']
                        username = await self.get_mal_username(access_token)
                        
                        if username:
                            await self.store_mal_profile(discord_id, username)
                        else:
                            print(f"Failed to retrieve MAL username for Discord ID {discord_id}")
                    else:
                        error_msg = await response.text()
                        print(f"Failed to retrieve access token. Status: {response.status}. Error: {error_msg}")
        except Exception as e:
            print(f"Error during OAuth2 token exchange: {str(e)}")

    async def get_mal_username(self, access_token: str) -> str:
        """Retrieve the MyAnimeList username using the access token"""
        url = "https://api.myanimelist.net/v2/users/@me"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        return user_data["name"]
                    else:
                        print(f"Failed to retrieve user data. Status: {response.status}")
                        return None
        except Exception as e:
            print(f"Error retrieving MAL username: {str(e)}")
            return None

    async def store_mal_profile(self, discord_id: int, username: str):
        """Store the Discord ID and MyAnimeList username in MongoDB"""
        db: AsyncIOMotorDatabase = self.bot.db
        collection = db["mal_profiles"]

        # Insert or update the user profile in the database
        await collection.update_one(
            {"discord_id": discord_id},
            {"$set": {"mal_username": username}},
            upsert=True
        )

        print(f"Stored MyAnimeList profile for Discord ID {discord_id}")

# Add the cog to the bot
def setup(bot: commands.Bot):
    bot.add_cog(MAL_Linking_System(bot))
