"""Core application utilities."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
    os.environ.setdefault(
        "PYTHONPATH",
        os.pathsep.join(
            [
                str(_REPO_ROOT),
                *(
                    os.environ.get("PYTHONPATH", "").split(os.pathsep)
                    if os.environ.get("PYTHONPATH")
                    else []
                ),
            ]
        ),
    )

from .config import AppSettings

__all__ = ["AppSettings"]
