# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors
from discord.ext import commands
from takina import config
import discord


class Avatars(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    async def fetch_user_image(
        self,
        ctx: commands.Context,
        user: discord.Member | discord.User | None = None,
        image_type: str = "display_avatar",
    ) -> discord.Embed:
        image_type_str = image_type.replace("_", " ").title()

        if not user:
            if not isinstance(ctx.author, discord.Member | discord.User):
                raise lyerrors.TakinaError("This command can only be used in a server.")
            user = ctx.author

        if "banner" in image_type:
            # why are we refetching the user?
            # well, you cannot get User.banner
            # if you do not specifically do Client.fetch_user
            # https://discordpy.readthedocs.io/en/stable/api.html#discord.User.banner
            user = await self._bot.fetch_user(user.id)

        image = getattr(user, image_type)
        if not image:
            raise lyerrors.TakinaError(f"This user does not have a {image_type_str.lower()} set.")

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = f"{user}'s {image_type_str}"
        embed.set_image(url=image.url)

        return embed

    @commands.hybrid_command(
        name="avatar",
        aliases=["av", "pfp"],
        description="Fetch the Discord display avatar of any member including yourself.",
        usage="@user",
    )
    @lychecks.is_user_app()
    async def avatar(
        self, ctx: commands.Context, *, member: discord.Member | discord.User | None = None
    ) -> None:
        embed = await self.fetch_user_image(ctx, member, "display_avatar")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="server_avatar",
        aliases=["sav", "spfp", "gav", "gpfp"],
        description="Fetch the Discord server avatar of any member including yourself.",
        usage="@user",
    )
    @lychecks.guild_only()
    async def server_avatar(
        self, ctx: commands.Context, *, member: discord.Member | None = None
    ) -> None:
        embed = await self.fetch_user_image(ctx, member, "guild_avatar")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="banner",
        description="Fetch the Discord banner of any member including yourself.",
        usage="@user",
    )
    @lychecks.is_user_app()
    async def banner(
        self, ctx: commands.Context, *, member: discord.Member | discord.User | None = None
    ) -> None:
        embed = await self.fetch_user_image(ctx, member, "banner")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        name="server_banner",
        aliases=["sbanner", "gbanner"],
        description="Fetch the Discord server banner of any member including yourself.",
        usage="@user",
    )
    @lychecks.guild_only()
    async def server_banner(
        self, ctx: commands.Context, *, member: discord.Member | None = None
    ) -> None:
        embed = await self.fetch_user_image(ctx, member, "guild_banner")
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Avatars(bot))
