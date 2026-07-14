"""Import helpers for physical MSI E2E evidence (001D4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.rescue_payload_version import rescue_payload_version
from core.rescue_physical_e2e_evidence_import import import_e2e_run_evidence, list_e2e_run_dirs

DEV_LAB_RUN_ID = "e2e-rescue-physical-20260714-153401-d35375d0"
EXPECTED_PAYLOAD = "1.10.0.22"


def _run_metadata(run_dir: Path) -> dict[str, Any]:
    for name in ("auto-physical-e2e-result.json", "msi-e2e-auto-result.json", "e2e-result.json"):
        path = run_dir / name
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                continue
    return {}


def is_physical_msi_run(run_dir: Path) -> bool:
    if run_dir.name == DEV_LAB_RUN_ID or run_dir.name.startswith(DEV_LAB_RUN_ID):
        return False
    meta = _run_metadata(run_dir)
    if meta.get("source") == "physical_msi":
        return True
    if meta.get("layout_mode") == "external_registered":
        return True
    run_id = str(meta.get("e2e_run_id") or run_dir.name)
    return run_id.startswith("e2e-rescue-msi-")


def select_physical_msi_run(
    setup_logs_base: Path,
    *,
    expected_payload_version: str = EXPECTED_PAYLOAD,
) -> dict[str, Any]:
    runs = list_e2e_run_dirs(setup_logs_base)
    for run_dir in runs:
        if not is_physical_msi_run(run_dir):
            continue
        meta = _run_metadata(run_dir)
        payload = str(meta.get("payload_version") or "")
        if payload and payload != expected_payload_version:
            continue
        return {
            "ok": True,
            "run_dir": run_dir,
            "e2e_run_id": run_dir.name,
            "source": "physical_msi",
            "payload_version": payload or expected_payload_version,
        }
    return {"ok": False, "code": "new_physical_msi_run_missing", "runs_seen": [p.name for p in runs[:5]]}


def import_physical_msi_evidence(
    *,
    repo_root: Path,
    setup_logs_base: Path,
    expected_payload_version: str = EXPECTED_PAYLOAD,
) -> dict[str, Any]:
    selected = select_physical_msi_run(setup_logs_base, expected_payload_version=expected_payload_version)
    if not selected.get("ok"):
        return {"import_ok": False, **selected}
    manifest = import_e2e_run_evidence(
        selected["run_dir"],
        repo_root=repo_root,
        setup_logs_base=setup_logs_base,
    )
    manifest["source"] = "physical_msi"
    manifest["payload_version"] = selected.get("payload_version") or rescue_payload_version()
    manifest["physical_e2e_run_id"] = selected["e2e_run_id"]
    (selected["run_dir"] / "import-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
