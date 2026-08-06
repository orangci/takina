# Takina Contributing Guidelines
These guidelines exist to make contributing to Takina easier for both the contributor and maintainer. I _**highly**_ recommend — no, I insist — that you at a minimum glance over these guidelines before considering contributing.

## Before Contributing
Please ensure that anything you contribute complies with Discord's Terms of Service.

If you're planning a new feature, please open an issue first or contact orangc directly before spending time implementing it. It's much better to know whether a feature will be accepted before writing hundreds of lines of code.

Features that will **not** be accepted include:
- Music-related functionality
- NSFW functionality
- Anything that violates Discord's Terms of Service

## AI Contributions
The door is that way. Leave.

## Formatting, Linting & Commits
Before committing, always run:

```sh
ruff format
ruff check
ty check
uv lock
```

Any `ruff check` and `ty check` diagnostics must be resolved before submitting.

> [!IMPORTANT]
> Takina has [pre-commit](https://pre-commit.com) hooks. Simply run `pre-commit install` inside the repository to avoid having to run these commands repeatedly.

Each commit should follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard, for example: `fix(mod.mute): mute command did not check for perms`. The scope should be the cog path; `util.qalc`, `fun.dictionary`, et cetera. Please use [atomic commits](https://en.wikipedia.org/wiki/Atomic_commit#Atomic_commit_convention).


## General Style
- Be descriptive with naming. Instead of `for i in x`, do `for user in members`
- Comment your code and keep it readable
- Although it shouldn't be excessive, use emojis, especially from `await lyhelpers.fetch_random_emoji()`
- Use type hints whenever practical, for example:
```py
async def build_profile_embed(ctx: commands.Context, member: discord.Member) -> discord.Embed:
```
- Use async wherever practical.
- Use `with` instead of `try`/`except`/`finally` blocks.
- Shared helper functions belong in `takina.libs.lyhelpers`. If a helper is useful in more than one cog, it probably belongs here.
- Commands should have a useful description, understandable parameter names, and concise docstrings where appropriate. Future contributors should be able to understand the code without too much difficulty
- Imports should be ordered by length, from longest to shortest at the top of the file.

## Cogs Layout
Helper functions et cetera belong in `takina/libs`. Cogs go into `takina/cogs/category-name`.
Two special cogs categories are:
- `takina/cogs/core` which is for core cogs vital to the bot's functionality, such as error handling.
- `takina/cogs/sesp` which is for server specific cogs; e.g. `takina/cogs/sesp/server-name/welcome-message.py`.
- `takina/cogs/listeners` which is for cogs that don't usually register commands, but instead consist of cog listeners that respond to events.

## Embeds
Prefer embed responses over plain text responses.

Success embeds:

```py
embed = discord.Embed(color=config.EMBED_COLOR)
embed.description = "Lorem ipsum dolor..."
```

Generally:
- We try not to use `embed.title` where practical; this is a stylistic choice
- Mention users with `.mention`, not `.name`
- Prefix descriptions with an emoji, often from `await lyhelpers.fetch_random_emoji()`

Example:

```py
embed.description = f"{config.emojis.SUCCESS} Done!"
# or perhaps
from takina.libs import lyhelpers
embed.description = f"{await lyhelpers.fetch_random_emoji()} Your random number is 42!"
```

## Error Handling
Takina uses a centralised error system; do **not** manually build error embeds inside commands.

Instead, raise one of the custom exceptions from `takina.libs.lyerrors` like so:

```py
from takina.libs import lyerrors
raise lyerrors.TakinaUserInputError("Please specify a user.")
```

The error cog automatically converts these into error embeds and sends them.

Current error classes include:
- `TakinaError`
- `TakinaUserInputError`
- `TakinaPermissionError`
- `TakinaBotPermissionError`
- `TakinaNotFoundError`
- `TakinaDisabledError`
- `TakinaMaintainerOnlyError`

You can also raise normal discord.py errors; these will be handled by the error cog automatically as well. However, you will not be able to specify the embed description this way; instead of `raise lyerrors.TakinaUserInputError("Please specify a user.")`, it will be `raise commands.UserInputError`.

## Checks
Takina provides a few helper decorators for commands in `takina.libs.lychecks`; use these where you can. For example:

```py
from takina.libs import lychecks
@lychecks.has_permissions(manage_messages=True)
```

The `lychecks` lib includes the following decorators:
- `@lychecks.has_permissions()`
- `@lychecks.is_user_app()`
- `@lychecks.dms_only()`
- `@lychecks.is_guild_app()`
- `@lychecks.is_user_and_guild_app()`

## Database
Takina uses PostgreSQL and SQLModel. Cogs should never create database sessions directly. Instead, use the helper functions provided by `takina.database`, which automatically open a session, perform the operation, and close the session.

### Reading data
Use `database.get()` to retrieve a single row by one or more column values.

```py
from takina import database

prefix = await database.get(
    PrefixModel,
    guild_id=ctx.guild.id,
)
```

This returns the matching model instance, or `None` if no row exists.

### Saving data
After creating a new model or modifying an existing one, save it with:

```py
await database.save(model)
```

This inserts or updates the row as appropriate.

### Deleting data

To remove a row from the database:

```py
await database.delete(model)
```

### Defining models

Each cog that owns persistent data should define its own SQLModel class rather than placing every model in a single file. Keeping models alongside the code that uses them makes the project easier to navigate and maintain.

```py
from sqlmodel import Field, SQLModel
from sqlalchemy import BigInteger

class PrefixModel(SQLModel, table=True):
    __tablename__ = "prefixes"

    # Discord snowflakes do not fit in a normal SQL INTEGER.
    guild_id: int = Field(
        sa_type=BigInteger,
        primary_key=True,
    )

    # The custom prefix for this guild.
    prefix: str
```

As a general rule:
- One table should correspond to one model class
- Define the model in the cog that owns the data.
- Use `BigInteger` for Discord IDs (`guild_id`, `user_id`, `channel_id`, etc.)

## Example Cog
I recommend looking at [the prefix command cog](./takina/cogs/prefix_command.py), as it is short, uses the database, and is a great example cog to get started with.

## Submitting Contributions
You have two options. Firstly, you can request that I create an account for you on my Git instance; email orangc at c@orangc.net, and then fork the repository and make a pull request.

Secondly, you may also email us a patch directly if you don't want to go through the hassle of waiting for orangc to make you an account. To create a patch file:
```sh
git format-patch -1 HEAD
ls *.patch # the file you see is the patch file
```
This creates a patch file in the current directory containing the latest commit. Replace -1 with -2 for the latest *two* commits, ad infinitum. If you have `git send-email` configured, then I will assume you already know how to use it. If you do not, then manually email takina@orangc.net the patch file.
