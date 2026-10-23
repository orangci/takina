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
    concatMapStrings
    ;

  # the peer map tying system users to the database user
  identMapName = "takina-${cfg.database.name}";
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

      peerUsers = mkOption {
        type = types.listOf types.str;
        default = [ ];
        example = [ "reimu" ];
        description = ''
          Extra system users allowed to connect as the database user over the local socket,
          without a password, e.g. for `psql -U takina takina`.
        '';
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

      # peer over the socket only, so no other local user or process can pose as the bot
      authentication = ''
        local ${cfg.database.name} ${cfg.database.user} peer map=${identMapName}
      '';

      identMap = ''
        ${identMapName} ${cfg.user} ${cfg.database.user}
      ''
      + concatMapStrings (user: "${identMapName} ${user} ${cfg.database.user}\n") cfg.database.peerUsers;
    };

    systemd.services.takina = {
      description = "Takina Discord bot";
      wantedBy = [ "multi-user.target" ];
      wants = [ "network-online.target" ];
      after = [ "network-online.target" ] ++ optional cfg.database.createLocally "postgresql.service";
      requires = optional cfg.database.createLocally "postgresql.service";

      environment =
        cfg.config
        // optionalAttrs cfg.database.createLocally {
          POSTGRESQL_URI = "postgresql://${cfg.database.user}@/${cfg.database.name}?host=/run/postgresql";
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

        # the bot evaluates user input (owner eval, qalc), so it gets as little as it can work with.
        # it writes no files, and ping3 uses unprivileged icmp sockets, so no capabilities either
        NoNewPrivileges = true;
        CapabilityBoundingSet = "";
        ProtectSystem = "strict";
        ProtectHome = true;
        PrivateTmp = true;
        PrivateDevices = true;
        ProtectKernelTunables = true;
        ProtectKernelModules = true;
        ProtectKernelLogs = true;
        ProtectControlGroups = true;
        ProtectClock = true;
        ProtectHostname = true;
        ProtectProc = "invisible";
        RestrictAddressFamilies = [
          "AF_UNIX"
          "AF_INET"
          "AF_INET6"
        ];
        RestrictNamespaces = true;
        RestrictRealtime = true;
        RestrictSUIDSGID = true;
        LockPersonality = true;
        SystemCallArchitectures = "native";
        UMask = "0077";
      };
    };
  };
}
