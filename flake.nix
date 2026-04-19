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
    inputs@{
      self,
      nixpkgs,
      uv2nix,
      pyproject-nix,
      pyproject-build-systems,
      ...
    }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      lib = pkgs.lib;
      inherit (lib) singleton composeManyExtensions;
      python = pkgs.python313;
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
      uvLockedOverlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };
      pythonSet =
        (pkgs.callPackage pyproject-nix.build.packages { inherit python; }).overrideScope
          (composeManyExtensions [
            pyproject-build-systems.overlays.default
            uvLockedOverlay
          ]);

      takina = pythonSet."takina";
      appPythonEnv = pythonSet.mkVirtualEnv (takina.pname + "-env") workspace.deps.default;
    in
    {
      nixosModules = {
        default = import ./nix/module.nix inputs;
        takina = import ./nix/module.nix inputs;
      };

      devShells.${system}.default = pkgs.mkShell {
        packages = [
          appPythonEnv
          pkgs.ruff
          pkgs.uv
        ];
      };

      packages.${system}.default = pkgs.stdenv.mkDerivation {
        pname = takina.pname;
        version = takina.version;
        src = ./.;

        nativeBuildInputs = with pkgs; [
          makeWrapper
          gcc
        ];
        buildInputs = singleton appPythonEnv;
        installPhase = ''
          makeWrapper ${appPythonEnv}/bin/python $out/bin/takina \
            --set PYTHONPATH ${./takina} \
            --add-flags "-m takina"
        '';
      };

      apps.${system}.default = {
        type = "app";
        program = "${self.packages.${system}.default}/bin/${takina.pname}";
      };
    };
}
