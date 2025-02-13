# Takina
A simple multipurpose bot for Discord. Also the very cutest Discord bot. I can prove it!

For a list of features and other information please visit: https://orangc.net/takina.

## TODO
- (long term) document all code with comments
- add time limits to giveaway command and other improvements
- add server avatar support to the avatar command
- refactor reports command
- fix a neko commands error
- pull request embed footer, the time
- make it throw a proper error when the env vars are not set

## Selfhosting
Before proceeding, I am assuming that you have a running MongoDB database. The majority of Takina's functionality depends on a MongoDB instance being available. A guide on selfhosting MongoDB with Docker is available [here](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-community-with-docker/).

#### On NixOS

*Assuming that you have `git` installed.*

- `git clone https://github.com/orangci/takina && cd takina`
- Set all the required environment variables in the `.env` file. You can find a list of what those are in the `.env.example` file. You can leave most of them as their defaults, but you at a minimum must set the `TOKEN` (Discord bot token), `HASDB=yes`, and  `MONGO` (your MongoDB URI.)
- Run `nix-shell`; You may need to run `nix-shell` twice if the first time doesn't start the bot up.

In the future, this will be managed with a proper flake.

#### With Docker

*Assuming you have `git` and `docker` installed.*

- `git clone https://github.com/orangci/takina && cd takina`
- Set all the required environment variables in the `.env` file. You can find a list of what those are in the `.env.example` file. You can leave most of them as their defaults, but you at a minimum must set the `TOKEN` (Discord bot token), `HASDB=yes`, and  `MONGO` (your MongoDB URI.)
- `docker build --tag 'takina' .`
- `docker run 'takina'`


## Legalese
- [License: BSD 3-Clause License](./LICENSE)
- [Terms of Service](https://orangc.net/takina/tos.html)
- [Privacy Policy](https://orangc.net/takina/privacy.html)