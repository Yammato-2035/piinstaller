"""Import backend/recovery submodules under python -m pytest path layout."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

_BACKEND = Path(__file__).resolve().parent.parent


def import_recovery_submodule(name: str) -> ModuleType:
    backend = str(_BACKEND)
    if sys.path[0] != backend:
        if backend in sys.path:
            sys.path.remove(backend)
        sys.path.insert(0, backend)
    for mod_name in list(sys.modules):
        if mod_name != "recovery" and not mod_name.startswith("recovery."):
            continue
        mod = sys.modules[mod_name]
        mod_file = getattr(mod, "__file__", "") or ""
        if mod_file and not mod_file.startswith(backend):
            del sys.modules[mod_name]
    return importlib.import_module(f"recovery.{name}")
