# Takina
A simple multipurpose bot for Discord. Also the very cutest Discord bot. Sakanaaa <3

For a list of features and other information please visit: https://takina.is-a.bot.

> [!TIP]
> Don't want to selfhost Takina? Our public instance is always up-to-date, and usually has excellent uptime.
> Invite link: https://takina.is-a.bot/invite

Note: Our documentation is WIP, and our website is also WIP, since it is severely outdated.

## Selfhosting

#### On NixOS

We will assume that you have flakes enabled.

Add Takina to your inputs like so:

```nix
inputs.takina = {
    url = "git+https://git.orangc.net/c/takina";
    # optionally make takina follow your nixpkgs input (recommended)
    inputs.nixpkgs.follows = "nixpkgs";
};
```

You may now use our NixOS module:

```nix
services.takina = {
    enable = true;
    config = {
        PREFIX = "?";
        EMBED_COLOUR = "0x2B2D31";
        # you may also set TOKEN here, but we ***highly*** advise you not to
        # as that would make your bot token publicly readable in the Nix store
        # you can instead set it via services.takina.environmentFile
        # which you set with a a path to a file
        # containing TOKEN=abc
        # we recommend using sops-nix/agenix for this
    };
};
```

> [!NOTE]
> The above snippet does not show off all configurable options in Takina.
> Please see [the .env.example file](.env.example) for all options.
> Click [here](https://git.orangc.net/c/dots/src/branch/master/modules/services/misc/takina.nix) for an example configuration with the NixOS module.

Or even install the Takina package directly:

```
environment.systemPackages = [ inputs.takina."x86_64-linux".default ];
```

Happy nixxing!

#### With Docker
Before proceeding, I am assuming that you have a running PostgreSQL database. The majority of Takina's functionality depends on a PostgreSQL instance being available. You can selfhost PostgreSQL with Docker yourself or or use the PostgreSQL server made in the docker compose file. 

##### Manually

*Assuming you have `git` and `docker` installed.*

- `git clone https://git.orangc.net/c/takina && cd takina`
- Set all the required environment variables in the `.env` file. You can find a list of what those are in the `.env.example` file. You can leave most of them as their defaults, but you at a minimum must set the `TOKEN` (Discord bot token) and  `POSTGRESQL_URI` (your PostgreSQL database URI).
- `docker build --tag 'takina' .`
- `docker run 'takina'`

##### Docker Compose

*Assuming you have `git` and `docker` installed.*

- `git clone https://git.orangc.net/c/takina && cd takina`
- Set all the required environment variables in the `docker-compose.yml` file. You can find a list of what those are in the `docker-compose.yml` file, don't forget to make a `.env` file for the passwords or tokens as well! You can find out which enviroment variables need to go to the `.env` file if its for example `${TOKEN}`.
- `docker compose up -d`

## Contributing
Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## Maintainers
Takina is currently maintained by [orangc](https://orang.ci) and [iostpa](https://iostpa.com).

## License
- [License: GNU AGPLv3](./LICENSE)
- [Terms of Service](https://takina.orangc.net/tos.html)
- [Privacy Policy](https://takina.orangc.net/privacy.html)

## Specifications
- This project follows the [Semantic Versioning 2.0.0](https://semver.org/) specification as of 2025-04-14. You may see the current version and changelog [here](./CHANGELOG.md).
