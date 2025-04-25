{pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
  buildInputs = with pkgs; [
    python313
    uv
  ];

  shellHook = ''
    if [ ! -d "venv" ]; then
      uv venv venv
      source venv/bin/activate
      uv pip install -r requirements.txt
    else
      source venv/bin/activate
    fi

    python3 takina
  '';
}
