"""Load KEY=VALUE lines from the project's .env into os.environ (real environment variables win)."""
import os
from pathlib import Path


def load() -> None:
    root = Path(__file__).resolve().parents[3]
    for path in (root / ".env", root / "backend" / ".env"):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            if value:
                os.environ.setdefault(key.strip(), value)
