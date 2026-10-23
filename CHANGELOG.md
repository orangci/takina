# Changelog
This project follows the [Semantic Versioning 2.0.0](https://semver.org/) specification as of 2025-04-14. This changelog was initiated at the same date.


## 2.0.0
For a good scope of what changed in this major release, see the relevant [pull request](https://git.orangc.net/c/takina/pulls/131) and [milestone](https://git.orangc.net/c/takina/milestone/1).

The biggest changes, in short:
- Migrated the Discord API wrapper/commands framework from nextcord to [discord.py](https://github.com/Rapptz/discord.py), and rewrote every cog in the process. Commands are hybrid now, working both as slash and prefix commands, and many are available as a user app in DMs and other servers.
- Migrated the database from MongoDB to PostgreSQL, with the schema managed by Alembic.
- Gathered server configuration under `settings guild`.
- Reviewed every cog line by line and fixed what turned up, which was rather a lot.

**Upgrading.** Nothing from MongoDB is carried over, so settings, cases, reminders and the like start afresh. Point `POSTGRESQL_URI` at an empty database and the bot creates the schema on its first start. A database made by a pre-release build of the rewrite, before Alembic arrived, must be backed up and stamped at the baseline first (`alembic stamp b26edad3bb48`). `MONGO`, `DB_NAME` and `HASDB` are gone, and `EMBED_COLOR` is now `EMBED_COLOUR`. The new variables are:
- `BOT_STATUS`, for the bot's status;
- `COGS_BLACKLIST` and `COGS_CATEGORY_BLACKLIST`, to skip cogs;
- `ENABLE_SESP_COGS`, for the server-specific cogs;
- `GOOGLE_API_KEY`, which books needs;
- `EMOJIS_SUCCESS`, `EMOJIS_ERROR`, `EMOJIS_NOTE` and `EMOJIS_MODERATOR`, for custom status emojis.

Cogs moved, so blacklist entries need the new names:
- the core cogs now live in `core` (errors, help, owner utilities, prefix, settings);
- `util.channels`, `util.embed_builder` and `util.roles` are now in `management`;
- `util.giveaways` is now in `fun`;
- `fun.dictionary` is now in `util`;
- the 8ball and fate moved to `fun.mysteries`;
- the minecraft server cog is now `minecraft.mcserver`;
- the triggers listener is now `listeners.triggers`.

**Removed.** Sniping, the haiku listener, the reddit command, `join-position` (which needs the members intent the bot no longer asks for), and the MyAnimeList profile, stats, updates and seasonals commands. `admin_report` became `settings guild reports`, and the long-deprecated `remindme` alias is finally gone.

**Security.** `util.qalc` could run programs and read or write files through libqalculate's `command()`, `load()` and `export()`. These and the functions that can assemble them are now refused, and qalc runs with an empty `PATH` and a minimal environment. `/role add` and `/role remove` let anyone with Manage Roles hand out roles above their own; they now compare against the invoker's top role. The starboard's slash subcommands, `/embed` and the giveaway commands had permission checks that never ran, and `/ping <host>` would happily probe the network the bot runs on. All four are closed. The bot also asks only for the intents it uses.

**Settings.** Server configuration now lives under `settings guild`: the modlog, honeypot, reports and starboard channels, GitHub previews (new, and on by default), and `settings guild disable` to turn any of them off again, the reports ping included. The old per-feature commands (`modlog channel`, `honeypot set`, `report channel`, `starboard settings` and so on) still work as aliases for now. Every server setting needs Manage Server. Custom prefixes are offered longest first, so a prefix of `takina` no longer swallows `takina ` (#138), and setting `PREFIX` no longer drops the `takina ` prefix.

**Moderation.** Ban, kick, mute and warn, singly and en masse, share one flow: confirm, act, DM, report and log. Bans and kicks DM first, as the target can't be reached afterwards, and delete that DM if the action fails. Mass actions refuse duplicates and more than ten targets. `/hackban` and `/unban` take user IDs as text, since slash integers can't hold a snowflake, and hackban checks members the cache doesn't know about. Case IDs can no longer collide, cases are listed newest first, `/edit_case` updates the logged message, `/modstats` counts kicks, and `/cases`, `/modcases` and `/modstats` accept users who have left or been banned. `/nick` resets nicknames properly and lets you change your own, `/purge` deletes the amount asked for, and reports stay private with narrower pings.

**Listeners.** Triggers match whole words only, cool down per channel, never ping, and allow responses of up to 500 characters. The starboard keeps private and NSFW messages off a public board, no longer posts the same message twice, and uses cached messages rather than fetching on every reaction. The honeypot skips members it can't touch and clears messages from the cache instead of every channel's history. GitHub previews authenticate, cache, link to the actual repository and stop matching inside URLs. AFK answers when toggled off, stops clearing itself straight away, and caps statuses at 200 characters. The Qur'ān listener survives network errors, and spells Qur'ān correctly.

**Utilities.** Reminders fetch only those that are due, can be at most a year away, accept `1h 30m` and warn that they arrive by DM. Translations check language codes against the instance, so `zh-Hans` and `pt-BR` work. DNS lookups resolve asynchronously through public resolvers, and WHOIS makes at most three lookups. Weather describes the conditions in words, time and weather share one politely rate-limited geocoder, Wikipedia no longer crashes on empty pages, and books, the dictionary, Steam, socials, info and avatars all received fixes for escaping, embed limits and missing data. `/role info` works again.

**Fun and the rest.** Gary, Goober, topics and roasts moved into `fun.fun`, and Urban Dictionary joined the dictionary in `util.dictionary`. Giveaways end atomically, are saved before they are announced, draw winners in voice and stage chats too, and reroll a full set of fresh winners. The 8ball needs a question, neko checks its categories and `kitsune` asks for kitsunes, and jokes no longer arrive as `None`. Hypixel, Wynncraft, Minecraft server status and skins handle missing data; Wynncraft talks to the API directly rather than through a wrapper. The anime, manga and character commands moved from Jikan to tenrai, ask for safe-for-work results only, and share one MyAnimeList library. Pagination gained first and last buttons. Prefix group commands no longer post their help before every answer, and slash commands that fail a check now say so rather than leaving Discord to report that the application did not respond.

**Under the hood.** The database helpers gained `get_or_create`, `insert`, query options, a real upsert, an in-memory cache for the rows read on every message, and idempotent deletes. Every request goes through one shared HTTP session with a proper User-Agent and a timeout. Logging goes through `logging` rather than `print`. Every file carries an SPDX licence identifier, and the line length is 100, as 88 was simply too short. The Docker image runs without root and keeps secrets out of its layers, the NixOS module talks to PostgreSQL rather than MongoDB, authenticates by peer over the socket and runs hardened, and the flake builds for aarch64 too. Unused dependencies are gone. CI now lints every push and pull request and runs a smoke test that loads every cog and validates the slash command tree.

### 1.28.0
Fixed a bug where the bot didn't check the env file for the prefix, added links to the stars and forks fields in the GitHub repository embed in `listeners.github`, and added a Codeberg command in `util.socials`.

#### 1.27.7
The odds were biased for a positive response for the 8ball command in `fun.fun`, since there were 10 positive responses and 5 negative. This has been fixed by adding 5 more negative responses.

#### 1.27.6
Do not ping the target when the roast command in `fun.roast` fails.

#### 1.27.5
Add a link to the queried game in `util.steam` in the embed title.

#### 1.27.4
Add timeout for `util.qalc` commands so that huge factorisations don't freeze the bot.

#### 1.27.3
Removed all Slash classes in cogs, such as the channel management cog having SlashChannelManagement. There is zero need to keep them in separate classes and thus cogs.

#### 1.27.2
Made the role commands in `util.roles` consistent with other commands in regards to target-action syntax; target first, role second.

#### 1.27.1
Fixed `util.wiki` to list disambiguation pages by name instead of simply showing the first page it found.

### 1.27.0
Added `listeners.quran`, which listens for patterns in the form of `Quran xxx:xxx` (e.g. `Quran 1:1`) and responds with the relevant verse from the Qur'an and its English translation. Closes #41.

#### 1.26.1
Fixed an issue with the modstats command in `mod.modlog` where the command would fail do to a function not being awaited properly. Closes #111.

### 1.26.0
Added the hackban command in `mod.ban`. Closes #14.

### 1.25.0
Added `minecraft.hypixel` with various Hypixel statistics et cetera commands. Closes #109.

#### 1.24.1
Defer interaction in `util.wiki` and add a warning for capitalisation.

### 1.24.0
Added `util.wiki`, resolving #39. This adds the `wiki` and `randomwiki` commands for fetching articles from Wikipedia.
This cog was contributed by @okcoder1 in the form of a patch file. Thank you!

#### 1.23.6
Fix broken error handling in `minecraft.wynncraft` when a non-existent username is queried. Closes #73.

#### 1.23.5
Address issue #79; in `util.dns`, throw a correct error response when the user queries a TLD that does not support WHOIS lookups.

#### 1.23.4
To comply with the new requirements by the nekos.best API, use a User-Agent header in API requests in fun.neko.

#### 1.23.3
Hardcoded the bot account's fate with orangc and iostpa and made it refuse to work for anybody else. Closes #102.

#### 1.23.2
Added a global cooldown/ratelimit for commands; one per second being the default.

#### 1.23.1
Made the config.BOT_VERSION variable extract its value from pyproject.toml as opposed to hardcoding.

### 1.23.0
Added `util.steam`, which has the `steam` command for looking up video games on Steam via the Steam API.

#### 1.22.1
Removed unclear responses for the 8ball command in `fun.fun`.

### 1.22.0
Added `util.qalc`, adding the `qalc` command for evaluating mathematical expressions with libqalculate. Resolves issue #88.

### 1.21.0
Added the `fate` command in `fun.fun`. Also changed the 8ball and commit commands to be seed-based, using the new randint_from_seed function in `libs.oclib`.

#### 1.20.6
Skip loading `util.translate` if the LibreTranslate API variables are unset. 

#### 1.20.5
Fixed `util.socials`'s GitHub command being broken due to outdated auth code. This patch was submitted by https://github.com/doughmination; thank you.

#### 1.20.4
Fixed `listeners.haikus` accidentally recognising GIF links as haikus, as well as blocking messages that are too short from being recognised (prevents spamming the letter "a" 17 times over, for example). Also block the user from spamming the same word repeatedly; if more than half the words are the same word, the message is skipped over.

#### 1.20.3
Fixed `listeners.honeypot` spamming logs with an AttributeError if the honeypot channel has not been set. Closes #80.

#### 1.20.2
Fixed `listeners.haikus` being broken on NixOS specifically due to `/nix/store` being read-only and therefore impossible to download ntlk data into.

#### 1.20.1
Fixed `listeners.haikus` being broken in production due to insufficient permissions to download the nltk dict.

### 1.20.0
Added `listeners.haikus`, a cog that watches for haikus in Discord messages and then alerts the user if their message contains a haiku, similar to Reddit's [u/haikusbot](https://reddit.com/u/haikusbot).

#### 1.19.1
Fixed a bug in util.translate that didn't allow passing languages in this format: `en-de`, or `ar-en`, et cetera as "unsupported translations".

### 1.19.0
Added `util.translate` for translating text from one language to another.

### 1.18.0
Refactored fun.neko to support all nekos.best endpoints dynamically.
Usage is now `takina neko category`.

#### 1.17.1
Fixed Nix packaging requiring you git clone the repo and remove the need for a `/var/lib/takina`. Added a shellHook for the devShell to load .env variables in.

### 1.17.0
Added a NixOS flake, with packaging and a NixOS module.Migrated from AsyncIOMotorClient to AsyncMongoClient (from Motor to pymongo).

### 1.16.0
Added `listeners.honeypot` and make Docker and the repository itself use uv.

#### 1.15.2
Added `myanimelist` alias for `mal` command.

#### 1.15.1
Added `2hu` alias for the `touhou` command and `umamusume` alias for the `uma` command.

### 1.15.0
Add fun.ias with `uma` and `touhou` commands, fixed some issues ruff caught with sesp.awcc.hoff and util.dns while also updating the dependencies.

#### 1.14.1
Fixed bug where the random emoji function crashed the bot due to the bot not having any emojis registered.

### 1.14.0
Added the server specific cog for AWCC, which adds the hof command.

### 1.13.0
Switch to version 3.1.1 of Nextcord away from the development (git) version.

#### 1.12.4
Change the info, ping response, and version command embeds to link to the correct changelog.

#### 1.12.3
Fix a typo in mod.reports.

#### 1.12.2
Minor refactoring of util.dns.

#### 1.12.1
Fixed typo in mod.kick where the DM message said "you were banned" instead of "you were kicked".

### 1.12.0
Added whois command for WHOIS domain lookup in util.dns.

### 1.11.0
Added the `eval` command to owner-utils.

#### 1.10.1
A typo caused the base banner command (fun.fun) to be broken.

### 1.10.0
Add server avatar command as well as banner/server banner commands in fun.fun. Closed #32.

#### 1.9.1
Fixed server info command bugging out if the server doesn't have an icon.

### 1.9.0
Removed sesp.isadev.subdomains, sesp.isadev.pr_channel, sesp.isadev.suggestions, sesp.theanimeflow, and sesp.isadev.ping_iostpa.

Also removed sesp.isadev.booster_perks and sesp.isadev.counting. There are now no sesp cogs whatsoever.

#### 1.8.2
Added a guild count to the info command.

#### 1.8.1
Fixed incorrect formatting in lib.oclib's get_ordinal function.

### 1.8.0
Ceased using `nextcord-ext-help-commands` and created my own in cogs.help, along with improving the documentation for every command's help description. Additionally stopped using Onami.

#### 1.7.3
The embeds in the util.socials cog were missing the quote border which all other embeds of this type in Takina have. This was fixed in this update.

#### 1.7.2
In sesp.isadev.subdomains, a bug was found where commands didn't support queries that ended with `.is-a.dev`. This was patched in this update.

#### 1.7.1
Fixed checking for an incorrect status in weebism.mal_updates: the function should check for `on-hold`, not `on hold`.

### 1.7.0
Added weebism.mal_updates — a command for fetching a MyAnimeList user's latest anime/manga list updates.

#### 1.6.4
Once again update sesp.isadev.subdomains staff subdomains filtering logic.

#### 1.6.3
Fix the staff subdomains command in sesp.isadev.subdomains being broken due to filtering out the wrong domains.

#### 1.6.2
Time and weather commands were broken because of some importing issues.

#### 1.6.1
Fixes various bugs introduced in 1.6.0, and also see #24.

### 1.6.0
As I started using ruff and uv here, I also formatted everything and addressed the hundreds and hundreds of errors ruff so joyfully raised.

#### 1.5.1
Made the maintainer only command reload_exts reload the config.

### 1.5.0
Added the VERSION variable in the config and updated listeners.ping_response to use it. Additionally added the version command in util.utils.

#### 1.4.7
Fix the message used for internal subdomains as opposed to reserved subdomains in sesp.isadev.subdomains, and fix a bug introduced in v1.4.6.

#### 1.4.6
Update sesp.isadev.subdomains to use the new API for reserved subdomains ~ now the `internal` key is used for staff subdomains instead of `reserved`.

#### 1.4.5
Update sesp.isadev.subdomains to use the new API schema (`record` was changed to `records`).

#### 1.4.4
Fix the pagination buttons in weebism.seasonals (see #17).

#### 1.4.3
Fix the longstanding error in weebism.character `'NoneType' object is not subscriptable` returned when attempting to fetch some characters (see #13).

#### 1.4.2
Fix the embed command being broken (see #16.)

#### 1.4.1
Patched fun.roasts slash commmand not calling interaction.user instead of ctx.author, and a typo in the classname. Additionally removed command cooldowns as that breaks the bot for now.

### 1.4.0
Added the fun.roasts cog.

### 1.3.0
Added the reddit command to the util.socials cog.

#### 1.2.1
Fixed the bot's name being hardcoded in some places as "Takina" instead of using the BOT_NAME environment variable.

### 1.2.0
Added the util.social cog with the github command.

### 1.1.0
Added the util.weather cog.

#### 1.0.1
Patched users being able to enter location names above 300 characters in util.time.

## 1.0.0
The initiating version. I used 1.0.0 instead of 0.1.0 as this project has already been in production for almost a year, and is stable.

