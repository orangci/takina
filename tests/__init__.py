# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
"""The test suite. Importing it pins the environment, before anything imports takina."""

import os

# takina reads these at import time, and pytest imports this package before any test or
# conftest. every variable a local .env could set is pinned here, as load_dotenv never
# overrides one that exists
os.environ.update(
    TOKEN="reimu",
    POSTGRESQL_URI="postgresql://smoke@/smoke?host=/nonexistent",
    ENABLE_SESP_COGS="yes",
    HYPIXEL_API_KEY="marisa",
    LIBRETRANSLATE_API_URL="http://libretranslate.test",
    LIBRETRANSLATE_API_KEY="",
    GOOGLE_API_KEY="cirno",
    GITHUB_AUTH_TOKEN="",
    BOT_NAME="Takina",
    BOT_STATUS="",
    PREFIX="",
    EMBED_COLOUR="#2B2D31",
    EMOJIS_SUCCESS="✅",
    EMOJIS_ERROR="❌",
    EMOJIS_NOTE="📝",
    EMOJIS_MODERATOR="👤",
    COGS_BLACKLIST="",
    COGS_CATEGORY_BLACKLIST="",
    STEAM_REGION="US",
    COMMANDS_COOLDOWN="5",
    TAKINA_DEBUG="",
)
