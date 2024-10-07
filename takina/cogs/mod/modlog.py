import os
import nextcord
from nextcord.ext import commands, application_checks
from nextcord import ui
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
from __main__ import DB_NAME, EMBED_COLOR

class CaseListButtonView(ui.View):
    def __init__(self, cases, per_page=10):
        super().__init__(timeout=30)
        self.cases = cases
        self.per_page = per_page
        self.current_page = 0
        self.max_pages = len(self.cases) // per_page + (1 if len(self.cases) % per_page > 0 else 0)

    def get_page_embed(self):
        embed = nextcord.Embed(title=f"Cases - Page {self.current_page + 1}/{self.max_pages}", color=EMBED_COLOR)
        start = self.current_page * self.per_page
        end = start + self.per_page
        page_cases = self.cases[start:end]
        embed.description = "\n".join(
            [f"<:note:1289880498541297685> `{case['case_id']}`: **{case['action'].capitalize()}** <t:{int(case['timestamp'].timestamp())}:R>" for case in page_cases]
        )
        return embed

    @ui.button(label="«", style=nextcord.ButtonStyle.grey)
    async def first_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.current_page = 0
        self.next_button.disabled = False
        self.previous_button.disabled = True
        await interaction.response.edit_message(embed=self.get_page_embed(), view=self)

    @ui.button(label="<", style=nextcord.ButtonStyle.grey, disabled=True)
    async def previous_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.current_page -= 1
        if self.current_page == 0:
            button.disabled = True
        self.next_button.disabled = False
        await interaction.response.edit_message(embed=self.get_page_embed(), view=self)

    @ui.button(label=">", style=nextcord.ButtonStyle.grey)
    async def next_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.current_page += 1
        if self.current_page == self.max_pages - 1:
            button.disabled = True
        self.previous_button.disabled = False
        await interaction.response.edit_message(embed=self.get_page_embed(), view=self)

    @ui.button(label="»", style=nextcord.ButtonStyle.grey)
    async def last_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.current_page = self.max_pages - 1
        self.next_button.disabled = True 
        self.previous_button.disabled = False
        await interaction.response.edit_message(embed=self.get_page_embed(), view=self)


class ModLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = AsyncIOMotorClient(os.getenv("MONGO")).get_database(DB_NAME)

    @nextcord.slash_command(description="Manage the modlog settings")
    async def modlog(self, interaction: nextcord.Interaction):
        pass

    @modlog.subcommand(description="Set the modlog channel")
    @application_checks.has_permissions(manage_guild=True)
    async def channel(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel):
        guild_id = interaction.guild_id

        guild_data = await self.db.modlog_settings.find_one({"guild_id": guild_id})
        if not guild_data:
            guild_data = {"guild_id": guild_id, "modlog_channel_id": None}

        guild_data["modlog_channel_id"] = channel.id

        await self.db.modlog_settings.update_one({"guild_id": guild_id}, {"$set": guild_data}, upsert=True)

        await interaction.response.send_message(f"Modlog channel has been set to {channel.mention}.", ephemeral=True)

    async def log_action(self, type: str, member: nextcord.Member, reason: str, moderator: nextcord.Member, duration: str = None):
        guild_id = member.guild.id
        guild_data = await self.db.modlog_settings.find_one({"guild_id": guild_id})
        if not guild_data:
            return

        modlog_channel_id = guild_data.get("modlog_channel_id")
        if not modlog_channel_id:
            return

        modlog_channel = self.bot.get_channel(modlog_channel_id)
        if not modlog_channel:
            return

        case_id = (await self.db.modlog_cases.count_documents({"guild_id": guild_id})) + 1
        timestamp = datetime.datetime.utcnow()

        case_data = {
            "guild_id": guild_id,
            "case_id": case_id,
            "action": type,
            "member_id": member.id,
            "member_name": str(member),
            "moderator_id": moderator.id,
            "moderator_name": str(moderator),
            "reason": reason,
            "duration": duration,
            "timestamp": timestamp,
        }

        await self.db.modlog_cases.insert_one(case_data)

        embed = nextcord.Embed(color=EMBED_COLOR, timestamp=timestamp)
        action = f"{type.capitalize()} ({duration})" if duration else type.capitalize()
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="Case", value=f"#{case_id}", inline=True)
        embed.add_field(name="Moderator", value=moderator.mention, inline=True)
        embed.add_field(name="Target", value=member.mention, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_thumbnail(url=member.avatar.url)
        await modlog_channel.send(embed=embed)

    @commands.command(name="case")
    async def get_case(self, ctx, case_id: int):
        case = await self.db.modlog_cases.find_one({"guild_id": ctx.guild.id, "case_id": case_id})
        if not case:
            await ctx.reply("Case not found.", mention_author=False)
            return

        embed = nextcord.Embed(color=EMBED_COLOR, timestamp=case["timestamp"])
        action = f"{case['action'].capitalize()} ({case['duration']})" if case["duration"] else case["action"].capitalize()
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="Case", value=f"#{case['case_id']}", inline=True)
        embed.add_field(name="Moderator", value=f"<@{case['moderator_id']}>", inline=True)
        embed.add_field(name="Target", value=f"<@{case['member_id']}>", inline=False)
        embed.add_field(name="Reason", value=case["reason"], inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="case_edit", aliases=["caseedit", "editc"])
    async def edit_case(self, ctx, case_id: int, *, new_reason: str):
        result = await self.db.modlog_cases.update_one(
            {"guild_id": ctx.guild.id, "case_id": case_id},
            {"$set": {"reason": new_reason}}
        )
        if result.modified_count == 0:
            await ctx.reply("Case not found or could not be updated.", mention_author=False)
        else:
            await ctx.reply(f"Case #{case_id} reason has been updated.", mention_author=False)

    @commands.command(name="cases")
    async def get_cases(self, ctx, user: nextcord.Member = None):
        query = {"guild_id": ctx.guild.id}
        if user:
            query["member_id"] = user.id

        cases = await self.db.modlog_cases.find(query).to_list(length=None)
        if not cases:
            await ctx.reply("No cases found.", mention_author=False)
            return

        view = CaseListButtonView(cases)
        await ctx.send(embed=view.get_page_embed(), view=view)

    @commands.command(name="modstats", aliases=["ms"])
    async def get_mod_stats(self, ctx, user: nextcord.Member = None):
        if not user:
            user = ctx.author
        cases = await self.db.modlog_cases.find({"guild_id": ctx.guild.id, "moderator_id": user.id}).to_list(length=None)
        if not cases:
            await ctx.reply(f"{user} has no moderation actions.")
            return

        view = CaseListButtonView(cases)
        await ctx.send(embed=view.get_page_embed(), view=view)


def setup(bot: commands.Bot):
    bot.add_cog(ModLog(bot))
