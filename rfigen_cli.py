"""Repository-local CLI launcher.

This lets users run the project before installing the package:

    python rfigen_cli.py generate --config configs/example.yaml
"""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rfigen.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
