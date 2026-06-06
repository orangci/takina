# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from pymongo import AsyncMongoClient
from nextcord.ext import commands
from ..libs import oclib
import nextcord
import config
import re

IMG_RE = re.compile(
    r"^https://(i\.imgur\.com/.*\.(png|jpe?g|gif|webp|bmp|tiff?)|cdn\.imgchest\.com/files/.*\.(png|jpe?g|gif|webp|bmp|tiff?))$"
)


class Mudae(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncMongoClient(host=config.MONGO_URI).get_database("mudae")
        self.col = self.db.mudae

    async def get_user_doc(self, user_id: int):
        doc = await self.col.find_one({"_id": user_id})
        if not doc:
            doc = {"_id": user_id, "imgsets": {}}
            await self.col.insert_one(doc)
        return doc

    async def save_user_doc(self, doc):
        await self.col.update_one(
            {"_id": doc["_id"]},
            {"$set": doc},
            upsert=True
        )

    def validate_links(self, links: list[str]) -> list[str]:
        out = []
        for l in links:
            l = l.strip()
            if IMG_RE.match(l):
                out.append(l)
        return out

    def split_discord(self, text: str, limit: int = 1900):
        chunks = []
        while len(text) > limit:
            cut = text.rfind(" ", 0, limit)
            if cut == -1:
                cut = limit
            chunks.append(text[:cut])
            text = text[cut:].lstrip()
        chunks.append(text)
        return chunks

    async def send_long(self, interaction: nextcord.Interaction, text: str):
        for chunk in self.split_discord(text):
            await interaction.followup.send(chunk)


    @nextcord.slash_command(name="mudae", description="mudae utilities")
    async def mudae(self, interaction: nextcord.Interaction):
        pass


    @mudae.subcommand(name="imgset", description="imgset utilities")
    async def imgset(self, interaction: nextcord.Interaction):
        await interaction.response.send_message(
            "subcommands: add, list, print",
            ephemeral=True
        )


    @imgset.subcommand(name="add", description="add links to an imgset")
    async def imgset_add(
        self,
        interaction: nextcord.Interaction,
        name: str,
        raw: str
    ):
        await interaction.response.defer()

        doc = await self.get_user_doc(interaction.user.id)

        parts = [p for p in re.split(r"\$+", raw) if p.strip()] if "$" in raw else raw.split()

        links = self.validate_links(parts)

        if not links:
            return await interaction.followup.send("no valid links provided")

        doc["sets"].setdefault(name, [])
        doc["sets"][name].extend(links)

        if len(doc["sets"][name]) > 1000:
            doc["sets"][name] = doc["sets"][name][:1000]

        await self.save_user_doc(doc)

        await interaction.followup.send(f"added {len(links)} links to {name}")


    @imgset.subcommand(name="list", description="list imgsets or contents")
    async def imgset_list(
        self,
        interaction: nextcord.Interaction,
        name: str = None
    ):
        await interaction.response.defer()

        doc = await self.get_user_doc(interaction.user.id)

        if name:
            if name not in doc["sets"]:
                return await interaction.followup.send("imgset not found")

            data = doc["sets"][name]
            text = f"{name}:\n" + "\n".join(data)
            return await self.send_long(interaction, text)

        names = list(doc["sets"].keys())
        if not names:
            return await interaction.followup.send("no imgsets")

        text = "imgsets:\n" + "\n".join(names)
        await self.send_long(interaction, text)


    @imgset.subcommand(name="print", description="print mudae command for imgset")
    async def imgset_print(
        self,
        interaction: nextcord.Interaction,
        name: str
    ):
        await interaction.response.defer()

        doc = await self.get_user_doc(interaction.user.id)

        if name not in doc["sets"]:
            return await interaction.followup.send("imgset not found")

        data = doc["sets"][name]
        if not data:
            return await interaction.followup.send("empty imgset")

        msg = "$ai " + name + " " + " ".join(f"$ {x}" for x in data)

        await self.send_long(interaction, msg)


def setup(bot: commands.Bot):
    bot.add_cog(Mudae(bot))
