"""
Kompatibilitaets-Shim: liefert das stdlib-Modul `inspect`.

Das Projekt nutzt zusaetzlich den Ordner `backend/inspect/` fuer Inspect-API-Code.
Diese Datei stellt sicher, dass `import inspect` weiterhin das Python-stdlib-
Modul liefert und nicht den lokalen Ordner.
"""

from __future__ import annotations

import importlib.util
import sys
import sysconfig
from pathlib import Path

_stdlib_inspect = Path(sysconfig.get_paths()["stdlib"]) / "inspect.py"
_spec = importlib.util.spec_from_file_location("_stdlib_inspect", _stdlib_inspect)
if not (_spec and _spec.loader):
    raise ImportError(f"cannot load stdlib inspect from {_stdlib_inspect}")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
sys.modules[__name__] = _mod
