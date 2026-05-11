"""
Inspect Phase 2 – Empfehlungspfade (Codes, Priorität), keine Aktionen.
"""

from __future__ import annotations

from typing import Any


def _path(code: str, priority: str, requires_confirmation: bool) -> dict[str, Any]:
    return {"code": code, "priority": priority, "requires_confirmation": requires_confirmation}


def generate_advice(classification: dict[str, Any], inspect_result: dict[str, Any]) -> dict[str, Any]:
    """
    Liefert recommended_paths aus Klassifikation + Rohdatenkontext (nur lesend).
    inspect_result kann für zukünftige Erweiterungen genutzt werden; derzeit defensiv minimal.
    """
    _ = inspect_result  # reserviert für kontextsensitive Regeln ohne neue Erkennung
    st_raw = classification.get("system_type")
    st = st_raw if isinstance(st_raw, str) else "UNKNOWN"
    st = st.strip().upper() if isinstance(st, str) else "UNKNOWN"

    paths: list[dict[str, Any]] = []

    if st == "EMPTY":
        paths = [
            _path("advice.install_linux", "high", True),
            _path("advice.restore_backup", "medium", True),
        ]
    elif st == "WINDOWS":
        paths = [
            _path("advice.preserve_windows", "high", True),
            _path("advice.repair_boot", "medium", True),
            _path("advice.offer_dualboot", "low", True),
        ]
    elif st == "LINUX":
        paths = [
            _path("advice.restore_backup", "high", True),
            _path("advice.repair_boot", "medium", True),
            _path("advice.analyze_failure", "low", True),
        ]
    elif st == "DUALBOOT":
        paths = [
            _path("advice.manual_decision_required", "high", True),
            _path("advice.repair_boot", "low", True),
        ]
    elif st == "BROKEN_BOOT":
        paths = [
            _path("advice.repair_boot", "high", True),
            _path("advice.restore_backup", "high", True),
        ]
    elif st == "PARTIAL_SYSTEM":
        paths = [
            _path("advice.analyze_failure", "high", True),
            _path("advice.restore_backup", "medium", True),
        ]
    else:
        paths = [
            _path("advice.further_assessment_required", "high", True),
            _path("advice.manual_decision_required", "medium", True),
        ]

    return {"recommended_paths": paths}
