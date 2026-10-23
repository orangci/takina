# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: orangc
"""
Check that module-level imports follow the house order: `from` imports above plain ones,
each group longest line first. Ruff's isort cannot express this, hence a script.

Usage: python scripts/check_imports.py [files...]  (defaults to every file under takina/)
"""

from pathlib import Path
import ast
import sys

# alembic writes these, and they are not worth reordering by hand
EXCLUDED = ("takina/migrations/", "takina/venv/")


def misordered(path: Path) -> list[str] | None:
    source = path.read_text().splitlines()
    tree = ast.parse("\n".join(source))

    lines = [
        source[node.lineno - 1]
        for node in tree.body
        if isinstance(node, ast.Import | ast.ImportFrom)
        and not (isinstance(node, ast.ImportFrom) and node.module == "__future__")
    ]

    froms = [line for line in lines if line.startswith("from ")]
    plain = [line for line in lines if line.startswith("import ")]
    expected = sorted(froms, key=len, reverse=True) + sorted(plain, key=len, reverse=True)

    # lines of equal length may sit in either order
    if [len(line) for line in lines] != [len(line) for line in expected]:
        return expected

    return None


def main(arguments: list[str]) -> int:
    paths = [Path(argument) for argument in arguments] or sorted(Path("takina").rglob("*.py"))
    failed = False

    for path in paths:
        if path.suffix != ".py" or path.as_posix().startswith(EXCLUDED):
            continue

        if (expected := misordered(path)) is not None:
            failed = True
            print(f"{path}: imports should read")
            print("\n".join(f"    {line}" for line in expected))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
