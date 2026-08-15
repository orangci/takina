self:
{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.services.takina;
  inherit (pkgs.stdenv.hostPlatform) system;

  inherit (lib)
    mkIf
    mkOption
    mkEnableOption
    types
    getExe
    singleton
    optional
    optionalAttrs
    ;
in
{
  options.services.takina = {
    enable = mkEnableOption "Takina Discord bot";

    package = mkOption {
      type = types.package;
      default = self.packages.${system}.default;
      description = "The Takina package to use.";
    };

    user = mkOption {
      type = types.str;
      default = "takina";
      description = "User account under which Takina runs.";
    };

    group = mkOption {
      type = types.str;
      default = "takina";
      description = "Group under which Takina runs.";
    };

    environmentFile = mkOption {
      type = types.nullOr types.path;
      default = null;
      description = "Environment file for Takina. Useful for passing secrets.";
    };

    config = mkOption {
      type = types.attrsOf types.str;
      default = {
        PREFIX = ".";
        BOT_NAME = "Takina";
        EMBED_COLOUR = "#2B2D31";
        LIBRETRANSLATE_API_URL = "";
      };
      description = "Environment variables passed to Takina.";
    };

    database = {
      createLocally = mkOption {
        type = types.bool;
        default = true;
        description = "Create the PostgreSQL database and user locally.";
      };

      hostname = mkOption {
        type = types.str;
        default = "localhost";
        description = "Database hostname.";
      };

      port = mkOption {
        type = types.port;
        default = 5432;
        description = "Database port.";
      };

      name = mkOption {
        type = types.str;
        default = "takina";
        description = "Database name.";
      };

      user = mkOption {
        type = types.str;
        default = "takina";
        description = "PostgreSQL user.";
      };
    };
  };

  config = mkIf cfg.enable {
    users.users.${cfg.user} = {
      isSystemUser = true;
      inherit (cfg) group;
    };

    users.groups.${cfg.group} = { };

    services.postgresql = mkIf cfg.database.createLocally {
      enable = true;
      ensureDatabases = singleton cfg.database.name;
      ensureUsers = singleton {
        name = cfg.database.user;
        ensureDBOwnership = true;
      };
    };

    systemd.services.takina = {
      description = "Takina Discord bot";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ] ++ optional cfg.database.createLocally "postgresql.service";

      environment =
        cfg.config
        // {
          NIXOS_INSTANCE = "yes";
          DB_NAME = cfg.database.name;
          DB_USER = cfg.database.user;
          POSTGRESQL_URI = "postgresql://${cfg.database.user}@${cfg.database.hostname}:${toString cfg.database.port}/${cfg.database.name}";
        }
        // optionalAttrs cfg.database.createLocally {
          HASDB = "yes";
        };

      serviceConfig = {
        User = cfg.user;
        Group = cfg.group;
        ExecStart = getExe cfg.package;
        Restart = "always";
        RestartSec = 5;
        DynamicUser = false;
        StandardOutput = "inherit";
        StandardError = "inherit";
        EnvironmentFile = mkIf (cfg.environmentFile != null) cfg.environmentFile;
      };
    };
  };
}
