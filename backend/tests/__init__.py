"""Test package bootstrap for backend unit tests."""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
_backend = str(_BACKEND)

# `python -m pytest` from backend/ prepends the repo root to sys.path.
# The legacy top-level recovery/ package then shadows backend/recovery/ imports.
if _backend in sys.path:
    sys.path.remove(_backend)
sys.path.insert(0, _backend)

for _mod_name in list(sys.modules):
    if _mod_name != "recovery" and not _mod_name.startswith("recovery."):
        continue
    _mod = sys.modules[_mod_name]
    _file = getattr(_mod, "__file__", "") or ""
    if _file and not _file.startswith(_backend):
        del sys.modules[_mod_name]
