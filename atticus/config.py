"""Backward-compatible shims for configuration imports.

Use ``core.config`` for new imports.
"""

from __future__ import annotations

from core.config import *  # noqa: F401,F403
from core.config import AppSettings

__all__ = ["AppSettings"]
