"""Load API keys from keys.env (visible) and/or .env (hidden).

Run from the project root so relative paths resolve correctly.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


def _parse_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_env(project_root: str | Path | None = None) -> None:
    root = Path(project_root or os.getcwd())
    for name in ("keys.env", ".env"):
        _parse_env_file(root / name)


def missing_vars(names: Iterable[str]) -> list[str]:
    return [n for n in names if not os.getenv(n, "").strip()]
