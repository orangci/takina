from dotenv import load_dotenv
from os import getenv

load_dotenv()

BOT_NAME = getenv("BOT_NAME")
DB_NAME = getenv("DB_NAME").lower()
MONGO_URI = getenv("MONGO")
GITHUB_AUTH_TOKEN = getenv("GITHUB_AUTH_TOKEN")
ERROR_COLOR = 0xFF0037

EMBED_COLOR_STR = getenv("EMBED_COLOR", "#2B2D31")
if EMBED_COLOR_STR.startswith("#"):
    EMBED_COLOR = int(EMBED_COLOR_STR[1:], 16)  # Remove "#" and convert hex to int
elif EMBED_COLOR_STR.startswith("0x"):
    EMBED_COLOR = int(EMBED_COLOR_STR, 16)  # Directly convert hex to int
else:
    EMBED_COLOR = int(EMBED_COLOR_STR)  # Handle cases where it might be directly an int
