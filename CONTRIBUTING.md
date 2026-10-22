# Takina contributing guidelines
These guidelines exist to make contributing to Takina easier for both the contributor and maintainer. I _**highly**_ recommend (no, I insist) that you at a minimum glance over them before contributing.

## Before contributing
Ensure that anything you contribute complies with Discord's Terms of Service.

If you're planning a new feature, open an issue first or contact orangc directly. It's far better to learn whether a feature will be accepted before sinking hours into hundreds of lines of code.

Features that will **not** be accepted include:
- Music-related functionality
- NSFW functionality
- Anything that violates Discord's Terms of Service

## AI contributions
The door is that way. Leave.

## Setup
Takina needs Python 3.13 or newer, [uv](https://docs.astral.sh/uv/), and a PostgreSQL database. A Nix flake with a dev shell is also provided.

```sh
uv sync
cp .env.example .env # at minimum, set TOKEN, POSTGRESQL_URI and LIBRETRANSLATE_API_URL
uv run python -m takina
```

`.env.example` documents every option. Use `COGS_BLACKLIST` and `COGS_CATEGORY_BLACKLIST` to skip cogs you're not working on. Cogs that need an API key (such as `minecraft.hypixel`) won't work without it.

## Formatting, linting and commits
Before committing, run:

```sh
ruff format
ruff check
ty check
uv lock
```

Resolve all `ruff check` and `ty check` diagnostics before submitting. The line length is 100.

> [!IMPORTANT]
> Takina has [pre-commit](https://pre-commit.com) hooks that run all of the above (plus `nixfmt`, `statix` and `deadnix` when installed). Run `pre-commit install` inside the repository to avoid running them by hand.

Commits follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard, for example `fix(mod.mute): mute command did not check for perms`. The scope is the cog path (`util.qalc`, `fun.giveaways`), the lib (`libs.lyviews`), or the area (`nix`, `deps`). Keep commits [atomic](https://en.wikipedia.org/wiki/Atomic_commit#Atomic_commit_convention).

## General style
- Prefer boring, readable code.
- Use descriptive names. Write `for user in members`, not `for i in x`.
- Use type hints wherever practical, for example:
```py
async def build_profile_embed(ctx: commands.Context, member: discord.Member) -> discord.Embed:
```
- Use async wherever practical. Never block the event loop, as that stalls the whole bot; use `aiohttp` (via `lyhelpers.request`) or `asyncio` subprocesses instead of `requests` or `subprocess.run`.
- Prefer context managers, such as `async with asyncio.timeout(...)`, over manual `try`/`finally` cleanup.
- Write lowercase comments where they help; skip ones that merely restate the code.
- Start every file with the SPDX header:
```py
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
```
- Order imports by line length, longest first, with `from` imports above plain `import` statements. Ruff does not enforce this, so check it yourself.
- Give commands a useful `description`, understandable parameter names, and a `usage` example where it helps.
- Use emojis in responses, but don't overdo it.
- Put helpers used by more than one cog in `takina/libs/lyhelpers.py`.

## Layout
Cogs go in `takina/cogs/<category>/<cog>.py` and are loaded automatically. Each cog defines a `commands.Cog` class and an `async def setup(bot)` function. Shared code lives in `takina/libs`, database models in `takina/models.py`, and configuration in `takina/config.py`.

Some categories are special:
- `core` is for cogs vital to the bot, such as error handling and settings.
- `listeners` is for cogs that mostly respond to events instead of registering commands.
- `sesp` is for server-specific cogs, in a per-server folder (`takina/cogs/sesp/awcc/hof.py`). They only load when `ENABLE_SESP_COGS` is set, and commands should be restricted with `@lychecks.sesp_guild_only(guild_id)`.

Commands should usually be hybrid commands (`@commands.hybrid_command`), so they work as both prefix and slash commands.

## Embeds
Prefer embed responses over plain text. Reply with `mention_author=False`.

```py
embed = discord.Embed(colour=config.EMBED_COLOUR)
embed.description = f"{config.emojis.SUCCESS} Done!"
await ctx.reply(embed=embed, mention_author=False)
```

- Avoid `embed.title` where practical; this is a stylistic choice.
- Mention users with `.mention`, not `.name`.
- Prefix descriptions with an emoji. Use `config.emojis.SUCCESS` (and friends) for status, or `await lyhelpers.fetch_random_emoji()` for a random one of the bot's application emojis.
- Use `lyviews.PaginatorView` for paginated embeds and `lyviews.AuthorView` for views only the invoker may use.

## Error handling
Takina uses a centralised error system. Do **not** build error embeds inside commands. Raise one of the exceptions from `takina.libs.lyerrors` instead:

```py
from takina.libs import lyerrors

raise lyerrors.TakinaNotFoundError("Cirno could not be found.")
```

The `core.errors` cog converts these into error embeds. The available classes are:
- `TakinaError`
- `TakinaUserInputError`
- `TakinaPermissionError`
- `TakinaBotPermissionError`
- `TakinaNotFoundError`
- `TakinaDisabledError`
- `TakinaMaintainerOnlyError`
- `TakinaMissingEnvironmentVariableError`

Plain discord.py errors (`commands.UserInputError`, `commands.MissingPermissions`, et cetera) are handled too, but you can't customise their message.

## Checks
Use the helpers in `takina.libs.lychecks` instead of rolling your own:

```py
from takina.libs import lychecks

@lychecks.has_permissions(manage_messages=True)
```

- `has_permissions()`: requires the given guild permissions. Bot owners bypass it.
- `guild_only()`: guild installs and guild contexts only.
- `dms_only()`: DMs and private channels only.
- `is_user_app()`: allow user installs, in guilds, DMs and private channels.
- `is_guild_app()`: guild installs only.
- `sesp_guild_only(guild_id)`: restrict a command to one server.

There's also a global per-user cooldown, set with `COMMANDS_COOLDOWN`.

## Database
Takina uses PostgreSQL through SQLModel and asyncpg. Cogs must never open sessions directly. Use the helpers in `takina.database`, which open a session, run the operation and close it.

```py
from takina import database, models

prefix = await database.get(models.PrefixModel, guild_id=ctx.guild.id)
prefixes = await database.get_all(models.ReminderModel, user_id=ctx.author.id)
await database.save(prefix)
await database.delete(prefix)
```

- `get()` returns the single matching row, or `None`. It raises if more than one row matches.
- `get_all()` returns a list of matching rows.
- `save()` inserts or updates.
- `delete()` removes the row.

Define models in `takina/models.py`, one class per table. Use `BigInteger` for Discord IDs, as snowflakes don't fit in a normal SQL integer.

```py
class PrefixModel(SQLModel, table=True):
    __tablename__ = "prefixes"

    guild_id: int = Field(sa_type=BigInteger, primary_key=True)
    prefix: str
```

Tables are created on startup with `create_all`, which doesn't alter existing tables. There are no migrations yet, so mention schema changes to existing models in your pull request.

## Example cog
Read [the prefix cog](./takina/cogs/core/prefix_command.py). It's short, uses the database, and is a jolly good starting point.

## Submitting contributions
You have two options. Firstly, email orangc at c@orangc.net to request an account on my Git instance, then fork the repository and open a pull request.

Secondly, email a patch to takina@orangc.net if you don't want to wait for an account:

```sh
git format-patch -1 HEAD
ls *.patch # the file you see is the patch file
```

This writes the latest commit to a patch file in the current directory. Replace `-1` with `-2` for the latest *two* commits, ad infinitum. If you have `git send-email` configured, I assume you already know how to use it.
