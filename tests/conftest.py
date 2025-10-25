from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
root_str = str(ROOT)

if root_str not in sys.path:
    sys.path.insert(0, root_str)

path_value = os.environ.get("PATH", "")
path_entries = path_value.split(os.pathsep) if path_value else []
if root_str not in path_entries:
    os.environ["PATH"] = os.pathsep.join([root_str, path_value]) if path_value else root_str
