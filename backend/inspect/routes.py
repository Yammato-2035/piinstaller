from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from fastapi import APIRouter

_base = Path(__file__).resolve().parent

_collector_spec = importlib.util.spec_from_file_location(
    "setuphelfer_inspect_collector",
    _base / "collector.py",
)
if not (_collector_spec and _collector_spec.loader):
    raise ImportError("cannot load inspect collector")
_collector_mod = importlib.util.module_from_spec(_collector_spec)
sys.modules["setuphelfer_inspect_collector"] = _collector_mod
_collector_spec.loader.exec_module(_collector_mod)
collect_inspect_result = _collector_mod.collect_inspect_result
InspectResult = _collector_mod.InspectResult

router = APIRouter(prefix="/api/inspect", tags=["inspect"])


@router.get("/run", response_model=InspectResult)
async def get_inspect_run() -> InspectResult:
    return collect_inspect_result()
