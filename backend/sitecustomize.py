"""
Python-Startup-Fix fuer stdlib `inspect`.

Hintergrund:
Das Verzeichnis `backend/inspect/` kann bei Python-Start das stdlib-Modul
`inspect` ueberschatten. Uvicorn/FastAPI/asyncio benoetigen jedoch zwingend
das echte stdlib-Modul.
"""

from __future__ import annotations

import importlib.util
import sys
import sysconfig
from pathlib import Path

_stdlib_inspect = Path(sysconfig.get_paths()["stdlib"]) / "inspect.py"
if _stdlib_inspect.is_file():
    _spec = importlib.util.spec_from_file_location("inspect", _stdlib_inspect)
    if _spec and _spec.loader:
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        sys.modules["inspect"] = _mod
