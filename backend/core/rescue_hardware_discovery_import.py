"""Identity-gated import for terminal hardware_discovery runs (PI-RS-ASUS-CAPTURE-FINALIZE-004)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping

PROFILE_ASUS_ROG_GABRIEL = "asus_rog_gabriel"
RUN_TYPE = "hardware_discovery"
TERMINAL_STATUSES = frozenset({"complete", "partial", "failed", "cancelled"})


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _run_status(run_dir: Path) -> dict[str, Any]:
    for name in ("run-status.json", "run_status.json"):
        p = run_dir / name
        if p.is_file():
            return _load_json(p)
    return {}


def _has_completion_marker(run_dir: Path) -> bool:
    return any((run_dir / name).is_file() for name in ("COMPLETED.TAG", "PARTIAL.TAG", "FAILED.TAG"))


def evaluate_hardware_discovery_import_candidate(
    run_dir: Path | str,
    *,
    expected_boot_id: str,
    expected_run_id: str,
    expected_fingerprint: str = PROFILE_ASUS_ROG_GABRIEL,
    expected_board: str = "G513QM",
    expected_manufacturer_substr: str = "ASUS",
) -> dict[str, Any]:
    """Strict import filter — no newest-session fallback, no MSI attach."""
    root = Path(run_dir)
    status = _run_status(root)
    identity = _load_json(root / "machine_identity.json") or _load_json(root / "machine-identity.json")
    binding = _load_json(root / "machine_binding.json") or _load_json(root / "machine-binding.json")

    reasons: list[str] = []
    run_type = str(status.get("run_type") or "")
    boot_id = str(status.get("boot_id") or "")
    run_id = str(status.get("run_id") or root.name)
    terminal = bool(status.get("terminal")) or (
        str(status.get("status") or "") in TERMINAL_STATUSES and _has_completion_marker(root)
    )
    profile = str(
        status.get("profile_id")
        or binding.get("profile")
        or identity.get("expected_profile")
        or ""
    )
    vendor = str(identity.get("sys_vendor") or identity.get("manufacturer") or "")
    product = str(identity.get("product_name") or "")
    board = str(identity.get("board_name") or identity.get("board") or "")

    if run_type and run_type != RUN_TYPE:
        reasons.append("run_type_mismatch")
    if expected_boot_id and boot_id and boot_id != expected_boot_id:
        reasons.append("boot_id_mismatch")
    if expected_run_id and run_id != expected_run_id:
        reasons.append("run_id_mismatch")
    if expected_fingerprint and profile and profile != expected_fingerprint:
        reasons.append("fingerprint_mismatch")
    if expected_manufacturer_substr and vendor and expected_manufacturer_substr.upper() not in vendor.upper():
        reasons.append("manufacturer_mismatch")
    if expected_board and board and expected_board.upper() not in board.upper() and expected_board.upper() not in product.upper():
        reasons.append("board_mismatch")
    if "MSI" in vendor.upper() or "MICRO-STAR" in vendor.upper():
        reasons.append("msi_evidence_excluded")
    if not terminal or not _has_completion_marker(root):
        reasons.append("incomplete_capture")

    ok = not reasons
    return {
        "ok": ok,
        "import_status": "import_ok" if ok else ("incomplete_capture" if "incomplete_capture" in reasons else "rejected"),
        "reasons": reasons,
        "run_id": run_id,
        "boot_id": boot_id,
        "profile_id": profile,
        "terminal": terminal,
        "status": status.get("status"),
        "msi_excluded": "msi_evidence_excluded" in reasons,
        "has_manifest": (root / "manifest.json").is_file(),
        "has_sha256": (root / "sha256sums.txt").is_file(),
        "has_marker": _has_completion_marker(root),
    }


def import_hardware_discovery_run(
    *,
    source_run_dir: Path | str,
    dest_dir: Path | str,
    expected_boot_id: str,
    expected_run_id: str,
    expected_fingerprint: str = PROFILE_ASUS_ROG_GABRIEL,
) -> dict[str, Any]:
    """Copy only a matching terminal ASUS hardware_discovery run. Never attaches MSI/older sessions."""
    src = Path(source_run_dir)
    dest = Path(dest_dir)
    gate = evaluate_hardware_discovery_import_candidate(
        src,
        expected_boot_id=expected_boot_id,
        expected_run_id=expected_run_id,
        expected_fingerprint=expected_fingerprint,
    )
    if not gate["ok"]:
        return {**gate, "copied": False, "destination": str(dest)}
    dest.mkdir(parents=True, exist_ok=True)
    # Do not copy protected_raw into git-bound evidence destinations by default.
    for item in src.iterdir():
        if item.name == "protected_raw":
            continue
        target = dest / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
    summary = {
        **gate,
        "copied": True,
        "destination": str(dest),
        "protected_raw_excluded": True,
    }
    (dest / "import-gate.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def reject_msi_or_nonterminal(candidate: Mapping[str, Any]) -> bool:
    reasons = list(candidate.get("reasons") or [])
    return any(r in reasons for r in ("msi_evidence_excluded", "incomplete_capture", "fingerprint_mismatch"))
