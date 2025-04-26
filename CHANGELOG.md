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