# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
import os

# takina.__main__ reads these at import time, and pytest imports this file before any test
os.environ.update(
    TOKEN="reimu",
    POSTGRESQL_URI="postgresql://smoke@/smoke?host=/nonexistent",
    ENABLE_SESP_COGS="yes",
    HYPIXEL_API_KEY="marisa",
    LIBRETRANSLATE_API_URL="http://localhost",
)
