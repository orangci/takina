# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lyerrors, lyhelpers, lyviews
from discord.ext import commands
from typing import Literal
from takina import config
import discord

# shared by the weebism cogs, which all read myanimelist data through tenrai

API_URL = "https://api.tenrai.org/v1"
PAGE_LENGTH = 500

type Kind = Literal["anime", "manga", "characters"]

NOT_FOUND: dict[Kind, str] = {
    "anime": "Anime not found.",
    "manga": "Manga not found.",
    "characters": "Character not found.",
}


async def search(kind: Kind, query: str) -> dict:
    data = await lyhelpers.request(
        f"{API_URL}/{kind}",
        params={"q": query, "limit": 1, "sfw": "true"},
        not_found=NOT_FOUND[kind],
    )

    if not data or not data.get("data"):
        raise lyerrors.TakinaNotFoundError(NOT_FOUND[kind])

    return data["data"][0]


def shown(value: object) -> str:
    # tenrai sends null for unknowns, such as episodes of a show still airing
    return "Unknown" if value in (None, "") else str(value)


def names(entries: list[dict] | None) -> str:
    return ", ".join(entry["name"] for entry in entries or [] if entry.get("name")) or "Unknown"


def entry_embed(entry: dict, title: str) -> discord.Embed:
    embed = discord.Embed(
        title=lyhelpers.truncate(title, 256), url=entry.get("url"), colour=config.EMBED_COLOUR
    )

    if cover_image := ((entry.get("images") or {}).get("jpg") or {}).get("image_url"):
        embed.set_thumbnail(url=cover_image)

    if mal_id := entry.get("mal_id"):
        embed.set_footer(text=f"MAL ID: {mal_id}")

    return embed


def word_pages(text: str, limit: int = PAGE_LENGTH) -> list[str]:
    # split between words, so a page never ends halfway through one
    pages: list[str] = []
    current = ""

    for word in text.split(" "):
        if current and len(current) + 1 + len(word) > limit:
            pages.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word

    if current:
        pages.append(current)

    return [lyhelpers.truncate(page, 4096) for page in pages]


async def send_synopsis(ctx: commands.Context, entry: dict) -> None:
    title = entry.get("title") or "Unknown"
    synopsis = entry.get("synopsis") or "No synopsis available."

    if (english_title := entry.get("title_english")) and english_title != title:
        synopsis = f"-# {english_title}\n\n{synopsis}"

    embeds = []
    for page in word_pages(synopsis):
        embed = entry_embed(entry, title)
        embed.description = page
        embeds.append(embed)

    if len(embeds) == 1:
        await ctx.reply(embed=embeds[0], mention_author=False)
        return

    await lyviews.PaginatorView.send(ctx, embeds)
