from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from fastapi import APIRouter

_base = Path(__file__).resolve().parent

_collector_spec = importlib.util.spec_from_file_location(
    "setuphelfer_inspect_collector_safety",
    _base.parent / "inspect" / "collector.py",
)
if not (_collector_spec and _collector_spec.loader):
    raise ImportError("cannot load inspect collector for safety routes")
_collector_mod = importlib.util.module_from_spec(_collector_spec)
sys.modules["setuphelfer_inspect_collector_safety"] = _collector_mod
_collector_spec.loader.exec_module(_collector_mod)
collect_inspect_result = _collector_mod.collect_inspect_result

_wg_spec = importlib.util.spec_from_file_location("setuphelfer_write_guard_routes", _base / "write_guard.py")
if not (_wg_spec and _wg_spec.loader):
    raise ImportError("cannot load write_guard")
_wg_mod = importlib.util.module_from_spec(_wg_spec)
_wg_spec.loader.exec_module(_wg_mod)
build_write_safety_summary = _wg_mod.build_write_safety_summary

router = APIRouter(prefix="/api/safety", tags=["safety"])


@router.get("/targets")
async def get_safety_targets() -> list[dict[str, object]]:
    """
    Liefert je Top-Level-Disk: device, size, classification (allowed|warning|blocked),
    write_allowed, reason_code. Keine Schreiboperation.
    """
    result = collect_inspect_result()
    payload = result.model_dump()
    summary = build_write_safety_summary(payload)
    minimal: list[dict[str, object]] = []
    for t in summary.get("targets") or []:
        if not isinstance(t, dict):
            continue
        minimal.append(
            {
                "device": t.get("device"),
                "size": t.get("size"),
                "classification": t.get("classification"),
                "write_allowed": t.get("write_allowed"),
                "reason_code": t.get("reason_code"),
            }
        )
    return minimal
