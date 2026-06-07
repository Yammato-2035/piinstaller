#!/usr/bin/env python3
"""Read-only action plans for rescue start assistant (no execution)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def build_plans(disk_report: dict[str, Any], wizard: dict[str, Any]) -> dict[str, Any]:
    rec = disk_report.get("recommendation") or {}
    media_ok = wizard.get("media_check", {}).get("live_media_runtime_stable", False)
    action = wizard.get("selected_action")
    plans: dict[str, Any] = {
        "schema_version": 1,
        "execution_allowed": False,
        "requires_operator_confirmation_phrase": True,
        "media_stable_required": True,
        "secrets_exposed": False,
    }
    if not media_ok:
        plans["blocked_reason"] = "live_media_unstable"
        plans["operator_hints"] = [
            "Stick erneut prüfen oder toram-Boot wählen",
            "USB-Rewrite mit aktueller ISO",
            "Keine Reparatur/Installation starten",
        ]
        return plans

    if action == "backup":
        plans["backup_plan"] = {
            "summary_de": "Backup-Plan (nur Vorschau): Benutzerdateien und Systempartitionen auf externe Platte kopieren.",
            "source_candidates": [
                d["path"]
                for d in disk_report.get("devices", [])
                if d.get("classification") in {"linux_system", "windows_data_or_system", "linux_data"}
            ],
            "target_candidates": [
                d["path"]
                for d in disk_report.get("devices", [])
                if d.get("classification") == "external_backup_disk"
            ],
            "execution": "blocked_until_explicit_operator_run",
        }
    elif action == "restore":
        plans["restore_plan"] = {
            "summary_de": "Restore-Plan (nur Vorschau): Backup-Katalog suchen, Zielsystem prüfen, Konflikte anzeigen.",
            "catalog_search_paths": ["/media/*/Backup", "/media/*/SETUPHELFER_BACKUP"],
            "execution": "blocked_until_backup_catalog_confirmed",
        }
    elif action == "repair":
        plans["repair_plan"] = {
            "summary_de": "Reparatur-Plan (nur Vorschau): read-only Diagnose, konservative NTFS-Hinweise, keine riskante ntfsfix-Automatik.",
            "recommended_first_step_de": "Backup erstellen, dann Expertenmodus",
            "write_actions": [],
            "execution": "blocked_until_backup_acknowledged",
        }
    elif action == "install":
        plans["install_plan"] = {
            "summary_de": "Installations-Plan (nur Vorschau): Zielplatte manuell bestätigen, Backup empfohlen.",
            "distributions": {
                "linux_mint": "Anfänger/Desktop",
                "ubuntu_server": "Server/headless/NAS",
                "debian": "stabil/minimal/fortgeschritten",
            },
            "partition_layout_uefi_gpt": {
                "efi_mb": 512,
                "root_gib": "80-120",
                "home": "rest",
                "swap": "swapfile",
                "luks": "optional",
                "dual_boot": "nur wenn Windows erkannt und freier Platz",
            },
            "execution": "blocked_until_target_disk_confirmed",
        }
    elif action == "diagnostics":
        plans["diagnostics_plan"] = {
            "summary_de": "Diagnosebericht sammeln (read-only), Telemetrie optional.",
            "execution": "allowed_read_only",
        }
    return plans


def main() -> int:
    disk_path = Path(sys.argv[1])
    wizard_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    disk_report = json.loads(disk_path.read_text(encoding="utf-8"))
    wizard = json.loads(wizard_path.read_text(encoding="utf-8"))
    plans = build_plans(disk_report, wizard)
    rendered = json.dumps(plans, indent=2, ensure_ascii=False)
    if out_path:
        out_path.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
