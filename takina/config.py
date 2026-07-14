# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from dotenv import load_dotenv
from pathlib import Path
from os import getenv
import tomllib

load_dotenv()

BOT_NAME = getenv("BOT_NAME")
DB_NAME = getenv("DB_NAME").lower()
MONGO_URI = getenv("MONGO")
GITHUB_AUTH_TOKEN = getenv("GITHUB_AUTH_TOKEN")
REDDIT_CLIENT_ID = getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = getenv("REDDIT_CLIENT_SECRET")
LIBRETRANSLATE_API_KEY = getenv("LIBRETRANSLATE_API_KEY")
LIBRETRANSLATE_API_URL = getenv("LIBRETRANSLATE_API_URL").removesuffix("/")
HYPIXEL_API_KEY = getenv("HYPIXEL_API_KEY")
STEAM_REGION = getenv("STEAM_REGION") or "US"
ERROR_COLOR = 0xFF0037
NIXOS_INSTANCE = getenv("NIXOS_INSTANCE")
# how many commands can be used in five seconds
COMMANDS_COOLDOWN = getenv("COMMANDS_COOLDOWN") or 5

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
