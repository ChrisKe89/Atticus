"""Atticus core utilities."""

from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PATH_ENTRIES = os.environ.get("PATH", "").split(os.pathsep) if os.environ.get("PATH") else []
if str(_REPO_ROOT) not in _PATH_ENTRIES:
    os.environ["PATH"] = (
        f"{_REPO_ROOT}{os.pathsep}{os.environ['PATH']}" if _PATH_ENTRIES else str(_REPO_ROOT)
    )

from core.config import AppSettings

__all__ = ["AppSettings"]
