# SPDX-License-Identifier: AGPL-3.0-or-later
from nextcord.ext import commands
import nextcord
from .libs.lib import *
from config import *
from motor.motor_asyncio import AsyncIOMotorClient

PARTICIPANT_ROLE_ID = 1344735937627689023
ART_CONTEST_CHANNEL_ID = 1344733527006118010
ART_CONTEST_LOG_THREAD_ID = 1344915843640725524


class ArtContest(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(MONGO_URI).get_database(DB_NAME)

    async def get_next_submission_number(self) -> int:
        """Retrieve the next submission number from the database."""
        result = await self.db.submissions.find_one_and_update(
            {"_id": "submission_counter"},
            {"$inc": {"count": 1}},
            upsert=True,
            return_document=True,
        )
        return result["count"]

    @nextcord.slash_command(
        name="art_contest",
        description="Submit your entry to the art contest!",
        guild_ids=[SERVER_ID],
    )
    async def art_contest(
        self,
        interaction: nextcord.Interaction,
        submission: nextcord.Attachment = nextcord.SlashOption(
            name="submission",
            description="Upload your art submission (image file only).",
            required=True,
        ),
        ship_title: str = nextcord.SlashOption(
            name="ship_title",
            description="Enter the title of your ship.",
            required=True,
        ),
    ) -> None:
        guild = interaction.guild
        participant_role = guild.get_role(PARTICIPANT_ROLE_ID)

        # Check if the user already has the participant role
        if participant_role in interaction.user.roles:
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = (
                ":x: You have already submitted an entry to the art contest!"
            )
            await interaction.send(embed=embed, ephemeral=True)
            return

        # Check if the submission is an image
        if not submission.content_type.startswith("image/"):
            embed = nextcord.Embed(color=ERROR_COLOR)
            embed.description = ":x: Please upload a valid image file."
            await interaction.send(embed=embed, ephemeral=True)
            return

        # Generate a unique submission number
        submission_number = await self.get_next_submission_number()

        embed = nextcord.Embed(color=EMBED_COLOR)
        embed.description = f"✅ Your submission has been received! Good luck in the contest! (Submission #{submission_number})."

        await interaction.send(embed=embed, ephemeral=True)

        # Add the participant role to the user
        await interaction.user.add_roles(
            participant_role, reason="Art contest submission"
        )

        # Send the submission to the art contest channel
        art_contest_channel = guild.get_channel(ART_CONTEST_CHANNEL_ID)
        if art_contest_channel:
            embed = nextcord.Embed(
                title=f"Submission #{submission_number}: {ship_title}",
                color=EMBED_COLOR,
            )
            embed.set_image(url=submission.url)
            await art_contest_channel.send(embed=embed)
        else:
            staff_channel = guild.get_channel(1261226647517003777)
            await staff_channel.send(
                "<@961063229168164864> the art contest module is broken: the art contest logging thread couldn't be found."
            )

        # Log the user's submission in the log thread
        log_thread = guild.get_thread(ART_CONTEST_LOG_THREAD_ID)
        if log_thread:
            await log_thread.send(
                f"**Submission #{submission_number}**\n**Username:** {interaction.user.name}\n**User ID:** {interaction.user.id}"
            )
        else:
            staff_channel = guild.get_channel(1261226647517003777)
            await staff_channel.send(
                "<@961063229168164864> the art contest module is broken: the art contest logging thread couldn't be found."
            )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ArtContest(bot))
