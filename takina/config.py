from os import getenv, environ
from dotenv import load_dotenv
from pathlib import Path
import tomllib
import random

load_dotenv()

BOT_NAME = getenv("BOT_NAME")
DB_NAME = environ["DB_NAME"].lower()
POSTGRESQL_URI = environ["POSTGRESQL_URI"].replace("postgresql://", "postgresql+asyncpg://")
GITHUB_AUTH_TOKEN = getenv("GITHUB_AUTH_TOKEN")
REDDIT_CLIENT_ID = getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = getenv("REDDIT_CLIENT_SECRET")
LIBRETRANSLATE_API_KEY = getenv("LIBRETRANSLATE_API_KEY")
LIBRETRANSLATE_API_URL = environ["LIBRETRANSLATE_API_URL"].removesuffix("/")
HYPIXEL_API_KEY = getenv("HYPIXEL_API_KEY")
GOOGLE_API_KEY = getenv("GOOGLE_API_KEY")
STEAM_REGION = getenv("STEAM_REGION") or "US"
ERROR_COLOR = 0xFF0037
NIXOS_INSTANCE = getenv("NIXOS_INSTANCE")
# how many commands can be used in five seconds
COMMANDS_COOLDOWN = int(getenv("COMMANDS_COOLDOWN") or 5)
# timeout for libqalculate in seconds
QALC_TIMEOUT = int(getenv("QALC_TIMEOUT") or 3)

# the nixos package sets the bot version as an environment variable
# as should other packaging for takina
# except docker
BOT_VERSION = getenv("BOT_VERSION")

# if it's docker, or running it directly
if BOT_VERSION is None:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    # get the version from pyproject.toml
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as f:
        BOT_VERSION = tomllib.load(f)["project"]["version"]

EMBED_COLOR_STR = getenv("EMBED_COLOR", "#2B2D31").strip().strip('"').strip("'")
if EMBED_COLOR_STR.startswith("#"):
    EMBED_COLOR = int(EMBED_COLOR_STR[1:], 16)  # Remove "#" and convert hex to int
elif EMBED_COLOR_STR.startswith("0x"):
    EMBED_COLOR = int(EMBED_COLOR_STR, 16)  # Directly convert hex to int
else:
    EMBED_COLOR = int(EMBED_COLOR_STR)  # Handle cases where it might be directly an int


class _Emojis:
    def __init__(self):
        self._success = self._parse("EMOJIS_SUCCESS", ":white_check_mark:")
        self._error = self._parse("EMOJIS_ERROR", ":x:")

    @staticmethod
    def _parse(env_var: str, default: str) -> list[str]:
        value = getenv(env_var, default)

        return [emoji.strip() for emoji in value.split(",") if emoji.strip()]

    @property
    def SUCCESS(self) -> str:
        return random.choice(self._success)

    @property
    def ERROR(self) -> str:
        return random.choice(self._error)


emojis = _Emojis()
