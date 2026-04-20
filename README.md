# Takina
A simple multipurpose bot for Discord. Also the very cutest Discord bot. Sakanaaa <3

For a list of features and other information please visit: https://takina.orangc.net.

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
        EMBED_COLOR = "0x2B2D31";
        # you may also set TOKEN here, but we ***highly*** advise you not to
        # as that would make your bot token publicly readable in the Nix store
        # you can instead set it via services.takina.environmentFile
        # which you set with a a path to a file
        # containing TOKEN=abc
        # we recommend using sops-nix/agenix for this
    };
};
```

Or even install the Takina package directly:

```
environment.systemPackages = [ inputs.takina."x86_64-linux".default ];
```

Happy nixxing!

#### With Docker
Before proceeding, I am assuming that you have a running MongoDB database. The majority of Takina's functionality depends on a MongoDB instance being available. A guide on selfhosting MongoDB with Docker is available [here](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-community-with-docker/), you can also consider using [MongoDB Atlas](https://www.mongodb.com/products/platform/atlas-database) or use the MongoDB server made in the docker compose file. 

##### Manually

*Assuming you have `git` and `docker` installed.*

- `git clone https://github.com/orangci/takina && cd takina`
- Set all the required environment variables in the `.env` file. You can find a list of what those are in the `.env.example` file. You can leave most of them as their defaults, but you at a minimum must set the `TOKEN` (Discord bot token), `HASDB=yes`, and  `MONGO` (your MongoDB URI.)
- `docker build --tag 'takina' .`
- `docker run 'takina'`

##### Docker Compose

*Assuming you have `git` and `docker` installed.*

- `git clone https://github.com/orangci/takina && cd takina`
- Set all the required environment variables in the `docker-compose.yml` file. You can find a list of what those are in the `docker-compose.yml` file, don't forget to make a `.env` file for the passwords or tokens as well! You can find out which enviroment variables need to go to the `.env` file if its for example `${TOKEN}`.
- `docker compose up -d`

## Contributing
Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## License
- [License: GNU AGPLv3](./LICENSE)
- [Terms of Service](https://takina.orangc.net/tos.html)
- [Privacy Policy](https://takina.orangc.net/privacy.html)

## Specifications
- This project follows the [Semantic Versioning 2.0.0](https://semver.org/) specification as of 14.04.2025. You may see the current version and changelog [here](./CHANGELOG.md).
- This project follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification as of 01.10.2024.
<!-- note to self: count takina loc with: `git ls-files | grep '\.py$' | xargs wc -l | tail -n 1`, 7,687 as of 2025.09.06 -->
