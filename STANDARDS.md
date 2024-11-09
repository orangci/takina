# Takina Code Standards
Takina does not currently follow *all* these, but as of now does follow the vast majority most of the time. These standards exist because I have a terrible memory and want everything to be uniform.

### Embeds
- all embeds must use the EMBED_COLOR env var as it's color, with the exception of it being an error embed; in which case it should be red
- all mentions of a user should generally be user.mention, not user.name or anything else
- generally field names should be prefixed with an emoji, preferrably a cute one

### Formatting
- `black **/*.py` should be run in the takina folder before every commit.
- Each commit should follow the Conventional Commits standard, for example: `fix(mod): mute command did not check for perms`. The scope should be the subfolder affected in the cogs dir, and if there is none, use (core) as a scope.
- Every command should have a description and help information.

### Categorization
- the `fun` folder is for fun related commands and cogs
- the `libs` folder is for libraries; all functions that might be used over and over again should be put in here, generally placed in libs/oclib.py
- the `listeners` folder is for listener cogs; ones that are not commands but instead listen for events and respond, like the github or starboard modules
- the `mod` folder is for moderation related commands and cogs
- the `util` folder is for utility related commands and cogs
- the `weebism` folder is for anime/manga related commands and cogs
- if a cog is not palced in a subfolder, it can be considered a core cog, vital to the functionality of bot

### Responses
For base commands, `ctx.reply(mention_author=False)` should always be used, save for special scenarios.
For slash commands, generally `interaction.send(ephemeral=True)` should be used, except for some places where ephemeral messages shouldn't be ephemeral (e.g. moderation commands.)

### Cooldowns
Generally commands should have at least a one second cooldown.
`@commands.cooldown(1, 1, commands.BucketType.user)`

### Documentation
Every command must have sufficient documentation for help commands.