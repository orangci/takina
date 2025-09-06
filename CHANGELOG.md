# Changelog
This project follows the [Semantic Versioning 2.0.0](https://semver.org/) specification as of 14.04.2025. This changelog was initiated at the same date.

## 1.0.0
The initiating version. I used 1.0.0 instead of 0.1.0 as this project has already been in production for almost a year, and is stable.

#### 1.0.1
Patched users being able to enter location names above 300 characters in util.time.

### 1.1.0
Added the util.weather cog.

### 1.2.0
Added the util.social cog with the github command.

#### 1.2.1
Fixed the bot's name being hardcoded in some places as "Takina" instead of using the BOT_NAME environment variable.

### 1.3.0
Added the reddit command to the util.socials cog.

### 1.4.0
Added the fun.roasts cog.

#### 1.4.1
Patched fun.roasts slash commmand not calling interaction.user instead of ctx.author, and a typo in the classname. Additionally removed command cooldowns as that breaks the bot for now.

#### 1.4.2
Fix the embed command being broken (see #16.)

#### 1.4.3
Fix the longstanding error in weebism.character `'NoneType' object is not subscriptable` returned when attempting to fetch some characters (see #13).

#### 1.4.4
Fix the pagination buttons in weebism.seasonals (see #17).

#### 1.4.5
Update sesp.isadev.subdomains to use the new API schema (`record` was changed to `records`).

#### 1.4.6
Update sesp.isadev.subdomains to use the new API for reserved subdomains ~ now the `internal` key is used for staff subdomains instead of `reserved`.

#### 1.4.7
Fix the message used for internal subdomains as opposed to reserved subdomains in sesp.isadev.subdomains, and fix a bug introduced in v1.4.6.

#### 1.5.0
Added the VERSION variable in the config and updated listeners.ping_response to use it. Additionally added the version command in util.utils.

#### 1.5.1
Made the maintainer only command reload_exts reload the config.

### 1.6.0
As I started using ruff and uv here, I also formatted everything and addressed the hundreds and hundreds of errors ruff so joyfully raised.

#### 1.6.1
Fixes various bugs introduced in 1.6.0, and also see #24.

#### 1.6.2
Time and weather commands were broken because of some importing issues.

#### 1.6.3
Fix the staff subdomains command in sesp.isadev.subdomains being broken due to filtering out the wrong domains.

#### 1.6.4
Once again update sesp.isadev.subdomains staff subdomains filtering logic.

### 1.7.0
Added weebism.mal_updates — a command for fetching a MyAnimeList user's latest anime/manga list updates.

#### 1.7.1
Fixed checking for an incorrect status in weebism.mal_updates: the function should check for `on-hold`, not `on hold`.

#### 1.7.2
In sesp.isadev.subdomains, a bug was found where commands didn't support queries that ended with `.is-a.dev`. This was patched in this update.

#### 1.7.3
The embeds in the util.socials cog were missing the quote border which all other embeds of this type in Takina have. This was fixed in this update.

### 1.8.0
Ceased using `nextcord-ext-help-commands` and created my own in cogs.help, along with improving the documentation for every command's help description. Additionally stopped using Onami.

#### 1.8.1
Fixed incorrect formatting in lib.oclib's get_ordinal function.

#### 1.8.2
Added a guild count to the info command.

#### 1.9.0
Removed sesp.isadev.subdomains, sesp.isadev.pr_channel, sesp.isadev.suggestions, sesp.theanimeflow, and sesp.isadev.ping_iostpa.

Also removed sesp.isadev.booster_perks and sesp.isadev.counting. There are now no sesp cogs whatsoever.

#### 1.9.1
Fixed server info command bugging out if the server doesn't have an icon.

### 1.10.0
Add server avatar command as well as banner/server banner commands in fun.fun. Closed #32.

#### 1.10.1
A typo caused the base banner command (fun.fun) to be broken.

### 1.11.0
Added the `eval` command to owner-utils.

### 1.12.0
Added whois command for WHOIS domain lookup in util.dns.

#### 1.12.1
Fixed typo in mod.kick where the DM message said "you were banned" instead of "you were kicked".

#### 1.12.2
Minor refactoring of util.dns.

#### 1.12.3
Fix a typo in mod.reports.

#### 1.12.4
Change the info, ping response, and version command embeds to link to the correct changelog.

### 1.13
Switch to version 3.1.1 of Nextcord away from the development (git) version.

### 1.14
Added the server specific cog for AWCC, which adds the hof command.