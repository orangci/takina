# Takina
A simple multipurpose bot for Discord. Takina is under heavy development; so far, we have the following features:

## weeb utilities
Takina utilizes the Jikan API for this module.

- anime searching — `?anime Lycoris Recoil`
- manga searching — `?manga Shikanoko`
- character searching — `?chr Takina Inoue`
- myanimelist user profiles — `?mal orangc`
- seasonal anime — `?season Summer 2022`

## fun
- user avatar fetching command
- google command
- roll command
- topic command; the topic prompts were taken from yagpdb
- urban dictionary searching command

## listeners
- antiphishing module
- github module; this sends embeds when a user sends a repository / pull request / issue link from Github, inspired by Monty Python
- starboard module — this will be improved

## moderation
- WIP reports system
- ban and unban commands
- mute and unmute commands
- a kick command
- a nickname changing command
- a message purging command
- a send command, which sends a message as Takina in the specified channel

## utilities
- role management commands; e.g. `role add weeb orangc`
- info commands — `userinfo`, `serverinfo`, `roleinfo`
- a snipe command
- commands to fetch the guild member count and user join position

## minecraft things
- `mcstatus play.mccisland.net` fetches the status of a minecraft server

More information/documentation may be available later at orangc.xyz/takina.

## installation
Using the Dockerfile or Nix.