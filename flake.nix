# IMPORTANT: some code in this flake.nix was taken from
# https://medium.com/@daniel.garcia_57638/nix-nirvana-packaging-python-apps-with-uv2nix-c44e79ae4bc9
{
  description = "Takina, the cutest multipurpose Discord bot.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      uv2nix,
      pyproject-nix,
      pyproject-build-systems,
      ...
    }:
    let
      inherit (nixpkgs) lib;
      inherit (lib) singleton composeManyExtensions genAttrs;

      # every system with a wheel for each dependency. riscv64 and powerpc64le would build
      # orjson, tzfpy, asyncpg and others from source, which needs overrides nobody has
      # written; nixpkgs refuses uv on i686 and 32-bit arm and gnuplot on freebsd, and has
      # dropped x86_64-darwin
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
      uvLockedOverlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };

      # everything below is built once per system
      forAllSystems =
        f:
        genAttrs systems (
          system:
          let
            pkgs = import nixpkgs { inherit system; };
            pythonSet =
              (pkgs.callPackage pyproject-nix.build.packages { python = pkgs.python313; }).overrideScope
                (composeManyExtensions [
                  pyproject-build-systems.overlays.default
                  uvLockedOverlay
                ]);
            takina = pythonSet."takina";
          in
          f {
            inherit system pkgs takina;
            appPythonEnv = pythonSet.mkVirtualEnv (takina.pname + "-env") workspace.deps.default;
          }
        );
    in
    {
      nixosModules = {
        default = import ./nix/module.nix self;
        takina = import ./nix/module.nix self;
      };

      devShells = forAllSystems (
        { pkgs, appPythonEnv, ... }:
        {
          default = pkgs.mkShell {
            packages = [
              appPythonEnv
              pkgs.ruff
              pkgs.uv
              pkgs.gcc.cc.lib
            ];

            shellHook = ''
              export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [ pkgs.gcc.cc.lib ]}:$LD_LIBRARY_PATH"

              if [ -f .env ]; then
                set -a
                . .env
                set +a
              fi
            '';
          };
        }
      );

      packages = forAllSystems (
        {
          pkgs,
          takina,
          appPythonEnv,
          ...
        }:
        {
          default = pkgs.stdenv.mkDerivation {
            inherit (takina) pname;
            inherit (takina) version;
            meta.mainProgram = "takina";
            src = ./.;

            nativeBuildInputs = singleton pkgs.makeWrapper;
            buildInputs = singleton appPythonEnv;
            # --chdir puts the app on python's path for -m, so no PYTHONPATH is needed
            installPhase = ''
              mkdir -p $out/app
              cp -r ./* $out/app/

              mkdir -p $out/bin
              makeWrapper ${appPythonEnv}/bin/python $out/bin/takina \
                --chdir $out/app \
                --set QALC ${pkgs.libqalculate}/bin/qalc \
                --set BOT_VERSION ${takina.version} \
                --add-flags "-m takina"
            '';
          };
        }
      );

      apps = forAllSystems (
        { system, takina, ... }:
        {
          default = {
            type = "app";
            program = "${self.packages.${system}.default}/bin/${takina.pname}";
          };
        }
      );
    };
}
