# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
from takina.libs import lychecks, lyerrors
from discord.ext import commands
from typing import Literal
from takina import config
import discord


ImageType = Literal["display_avatar", "guild_avatar", "banner", "guild_banner"]

IMAGE_NAMES: dict[ImageType, str] = {
    "display_avatar": "Avatar",
    "guild_avatar": "Server Avatar",
    "banner": "Banner",
    "guild_banner": "Server Banner",
}


class Avatars(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot = bot

    async def fetch_user_image(
        self,
        ctx: commands.Context,
        user: discord.Member | discord.User | None,
        image_type: ImageType,
    ) -> discord.Embed:
        user = user or ctx.author

        # banners only arrive when the user or member is fetched, never from the cache
        # https://discordpy.readthedocs.io/en/stable/api.html#discord.User.banner
        match image_type:
            case "display_avatar":
                image = user.display_avatar
            case "guild_avatar":
                image = user.guild_avatar if isinstance(user, discord.Member) else None
            case "banner":
                image = (await self._bot.fetch_user(user.id)).banner
            case "guild_banner":
                assert ctx.guild is not None
                try:
                    image = (await ctx.guild.fetch_member(user.id)).guild_banner
                except discord.NotFound:
                    raise lyerrors.TakinaNotFoundError("That user is not in this server.")

        if not image:
            raise lyerrors.TakinaError(
                f"This user does not have a {IMAGE_NAMES[image_type].lower()} set."
            )

        embed = discord.Embed(colour=config.EMBED_COLOUR)
        embed.title = f"{user}'s {IMAGE_NAMES[image_type]}"
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
