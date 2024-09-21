import os
import asyncio
import nextcord
from nextcord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
from aiohttp import web
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants
VERIFIED_ROLE_ID = 1281898369236602910
MAL_OAUTH_URL = "https://myanimelist.net/v1/oauth2/authorize"
MAL_TOKEN_URL = "https://myanimelist.net/v1/oauth2/token"
MAL_API_USER_URL = "https://api.myanimelist.net/v2/users/@me"
REDIRECT_URI = "http://localhost:8080/callback"  # Replace with your actual redirect URI
CLIENT_ID = os.getenv("MAL_CLIENT_ID")
CLIENT_SECRET = os.getenv("MAL_CLIENT_SECRET")

intents = nextcord.Intents.default()
intents.members = True  # Required to manage roles
bot = commands.Bot(command_prefix="!", intents=intents)

# Database setup
class MALLinker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(os.getenv("MONGO")).get_database("anna")

    async def get_user_mal(self, discord_id):
        """Fetch the MAL username from the database."""
        return await self.db.linked_accounts.find_one({"discord_id": discord_id})

    async def set_user_mal(self, discord_id, mal_username):
        """Set the MAL username in the database."""
        await self.db.linked_accounts.update_one(
            {"discord_id": discord_id},
            {"$set": {"mal_username": mal_username}},
            upsert=True
        )

    async def unset_user_mal(self, discord_id):
        """Remove the MAL link from the database."""
        await self.db.linked_accounts.delete_one({"discord_id": discord_id})

# OAuth2 and API handling
async def exchange_code_for_token(code):
    """Exchange the authorization code for an access token."""
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(MAL_TOKEN_URL, data=data) as resp:
            if resp.status == 200:
                return await resp.json()  # This will include access_token
            else:
                logging.error(f"Failed to exchange code: {await resp.text()}")
                return None

async def fetch_mal_user(access_token):
    """Fetch the user's MyAnimeList profile using the access token."""
    headers = {"Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(MAL_API_USER_URL, headers=headers) as resp:
            if resp.status == 200:
                user_data = await resp.json()
                return user_data.get("name")  # Return MAL username
            else:
                logging.error(f"Error fetching MAL user: {await resp.text()}")
                return None

# HTTP server for handling OAuth2 redirect
async def handle_redirect(request):
    """Handle the OAuth2 redirect from MyAnimeList."""
    code = request.query.get('code')
    state = request.query.get('state')

    if not code:
        return web.Response(text="Error: No code provided", status=400)

    # Exchange code for token and fetch the MAL user
    token_data = await exchange_code_for_token(code)
    if token_data:
        access_token = token_data.get('access_token')
        mal_username = await fetch_mal_user(access_token)
        if mal_username:
            discord_id = int(state)
            # Save MAL username in the database for the discord user
            cog = bot.get_cog("MALLinker")
            await cog.set_user_mal(discord_id, mal_username)
            return web.Response(text=f"Successfully linked MyAnimeList account: {mal_username}")
        else:
            return web.Response(text="Error fetching MAL user", status=500)
    else:
        return web.Response(text="Error during token exchange", status=500)

app = web.Application()
app.add_routes([web.get('/callback', handle_redirect)])

class AdminWelcomeView(nextcord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @nextcord.ui.button(label="Link MyAnimeList", style=nextcord.ButtonStyle.green)
    async def link_mal_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        """Button handler for MAL linking."""
        modal = MALLinkModal(self.bot)
        await interaction.response.send_modal(modal)


class MALLinkModal(nextcord.ui.Modal):
    def __init__(self, bot):
        super().__init__("Link MyAnimeList")
        self.bot = bot

        self.url_input = nextcord.ui.TextInput(
            label="Click the link below to link your MAL account:",
            placeholder=MAL_OAUTH_URL + f"?response_type=code&client_id={CLIENT_ID}&state={bot.user.id}&redirect_uri={REDIRECT_URI}",
            required=False  # Only used for display
        )
        self.add_item(self.url_input)

    async def callback(self, interaction: nextcord.Interaction):
        user = interaction.user
        mal_username = await self.process_oauth(user)

        if mal_username:
            # Store the linked account in the database
            await self.bot.get_cog("MALLinker").set_user_mal(user.id, mal_username)

            # Grant verified role
            role = interaction.guild.get_role(VERIFIED_ROLE_ID)
            if role not in user.roles:
                await user.add_roles(role)

            await interaction.response.send_message(f"Your MyAnimeList account '{mal_username}' has been linked and verified.", ephemeral=True)
        else:
            await interaction.response.send_message("There was an error linking your MyAnimeList account.", ephemeral=True)

    async def process_oauth(self, user):
        """Simulate the OAuth2 process and return the MAL username."""
        # In reality, this function would handle the OAuth2 flow, exchanging the code for tokens and fetching the MAL username
        return "example_mal_username"

class LinkingSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(os.getenv("MONGO")).get_database("anna")

    @nextcord.slash_command(name="admin_welcome", description="Send the welcome message to allow users to link their MyAnimeList account.")
    @commands.has_permissions(administrator=True)
    async def admin_welcome(self, interaction: nextcord.Interaction):
        """Sends a welcome message with the button to link MAL account."""
        view = AdminWelcomeView(self.bot)
        await interaction.response.send_message("Welcome! Click the button below to link your MyAnimeList account.", view=view)

    @nextcord.slash_command(name="malset", description="Relink your MyAnimeList account.")
    async def malset(self, interaction: nextcord.Interaction):
        """Allows a user to relink their MAL account."""
        view = AdminWelcomeView(self.bot)
        await interaction.response.send_message("Click the button below to relink your MyAnimeList account.", view=view, ephemeral=True)

    @nextcord.slash_command(name="malunset", description="Unlink a user's MyAnimeList account.")
    @commands.has_permissions(manage_roles=True)  # Moderators only
    async def malunset(self, interaction: nextcord.Interaction, user: nextcord.Member):
        """Allows moderators to unlink a user's MyAnimeList account."""
        await self.bot.get_cog("MALLinker").unset_user_mal(user.id)

        # Remove verified role
        role = interaction.guild.get_role(VERIFIED_ROLE_ID)
        if role in user.roles:
            await user.remove_roles(role)

        await interaction.response.send_message(f"{user.mention}'s MyAnimeList account has been unlinked.", ephemeral=True)

def setup(bot):
    bot.add_cog(LinkingSystem(bot))