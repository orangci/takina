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

    dataDir = lib.mkOption {
      type = lib.types.str;
      default = "/var/lib/takina";
      description = "The directory where takina stores its data files.";
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
      description = "Path to a environment file, usually used for passing sensitive environment variables to Takina such as the Discord bot token.";
    };

    config = mkOption {
      type = types.attrsOf types.str;
      default = {
        BOT_NAME = "Takina";
        PREFIX = ".";
        EMBED_COLOR = "0xFAB387";
      };
      description = "Configuration options for Takina passed as environment variables.";
    };

    database = {
      createLocally = mkOption {
        type = types.bool;
        default = true;
        description = "Create the database and database user locally.";
      };

      user = mkOption {
        type = types.str;
        default = "takina";
        description = "Database user";
      };

      hostname = mkOption {
        type = types.str;
        default = "localhost";
        description = "Database hostname";
      };

      port = mkOption {
        type = types.port;
        default = 27017;
        description = "Database port";
      };

      name = mkOption {
        type = types.str;
        default = "takina";
        description = "Database name";
      };
    };
  };

  config = mkIf cfg.enable {
    users.users.${cfg.user} = {
      isSystemUser = true;
      group = cfg.group;
    };

    users.groups.${cfg.group} = { };
    services.mongodb.enable = mkIf cfg.database.createLocally true;
    systemd.tmpfiles.settings."10-takina".${cfg.dataDir}.d = {
      inherit (cfg) user group;
      mode = "0744";
    };

    systemd.services.takina = {
      description = "Takina Discord bot";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];
      environment = cfg.config // {
        HASDB = mkIf cfg.database.createLocally "yes";
        DB_NAME = mkIf cfg.database.createLocally cfg.database.name;
        MONGO = mkIf cfg.database.createLocally "mongodb://${cfg.database.user}@${cfg.database.hostname}:${cfg.database.port}/${cfg.database.name}";
      };
      serviceConfig = {
        User = cfg.user;
        Group = cfg.group;
        WorkingDirectory = cfg.dataDir;
        ExecStart = getExe cfg.package;
        Restart = "always";
        RestartSec = 5;
        DynamicUser = false;
        EnvironmentFile = mkIf (cfg.environmentFile != null) cfg.environmentFile;
      };
    };
  };
}
