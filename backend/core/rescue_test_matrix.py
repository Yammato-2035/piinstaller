"""
Rescue test matrix — machine-readable boot/menu/hardware status (Phase R.3).

Written to /setuphelfer-evidence/matrix/ on each boot or menu start.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from core.rescue_boot_logger import (
    collect_boot_context,
    collect_bootloader_context,
    collect_live_environment,
    collect_menu_context,
)
from core.rescue_persistence import (
    Runner,
    build_rescue_evidence_root,
    ensure_rescue_evidence_tree,
    write_rescue_json_evidence,
    write_rescue_text_evidence,
)

RESCUE_TEST_MATRIX_VERSION = 3

MatrixStatus = Literal["green", "yellow", "red", "gray", "blocked", "unknown"]

_MATRIX_AREAS = (
    "boot",
    "bootloader",
    "stick_persistence",
    "tui_menu",
    "graphical_menu",
    "browser_kiosk",
    "react_rescue_ui",
    "wlan_scan",
    "network",
    "telemetry_spool",
    "telemetry_ingest",
    "hardware_msi",
    "internal_readonly",
    "backup_target_discovery",
    "restore_gate",
    "partitions_readonly",
    "logs_complete",
    "evidence_writable",
    "error_summary",
    "next_action",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _entry(
    entry_id: str,
    area: str,
    title: str,
    status: MatrixStatus,
    *,
    observed: str = "",
    evidence_path: str | None = None,
    risk: str = "low",
    next_action: str = "",
) -> dict[str, Any]:
    return {
        "id": entry_id,
        "area": area,
        "title": title,
        "status": status,
        "observed": observed,
        "evidence_path": evidence_path,
        "risk": risk,
        "next_action": next_action,
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def build_rescue_test_matrix_entries(*, runner: Runner = None) -> list[dict[str, Any]]:
    """Build all R.3 matrix entries from read-only probes and state files."""
    entries: list[dict[str, Any]] = []
    boot = collect_boot_context(runner=runner)
    bl = collect_bootloader_context(runner=runner)
    live = collect_live_environment(runner=runner)
    menu = collect_menu_context(runner=runner)
    persist = build_rescue_evidence_root(runner=runner)

    entries.append(
        _entry(
            "R3-BOOT-001",
            "boot",
            "Kernel und Live-Boot",
            "green" if boot.get("live_medium_dir_exists") else "yellow",
            observed=f"kernel={boot.get('kernel')} live_medium={boot.get('live_medium_dir_exists')}",
            risk="medium" if not boot.get("live_medium_dir_exists") else "low",
            next_action="Live-Medium prüfen" if not boot.get("live_medium_dir_exists") else "OK",
        )
    )
    entries.append(
        _entry(
            "R3-BOOT-002",
            "bootloader",
            "UEFI/BIOS und Secure-Boot-Indizien",
            "green" if bl.get("efi_present") else "yellow",
            observed=f"mode={bl.get('firmware_mode')} secure_boot={bl.get('secure_boot_indicators')}",
            next_action="BIOS/UEFI-Modus dokumentieren",
        )
    )

    stick_status: MatrixStatus = "green"
    if persist.get("fallback"):
        stick_status = "yellow" if persist.get("mount_point") else "red"
    entries.append(
        _entry(
            "R3-PERSIST-001",
            "stick_persistence",
            "Stick-Persistenz /setuphelfer-evidence",
            stick_status,
            observed=str(persist.get("persistence_mode")),
            evidence_path=str(Path(persist.get("evidence_root", "")) / "matrix"),
            risk="high" if stick_status == "red" else "medium" if stick_status == "yellow" else "low",
            next_action=persist.get("warning") or "Evidence auf Stick beschreibbar",
        )
    )

    menu_mode = str(menu.get("menu_mode") or "unknown")
    entries.append(
        _entry(
            "R3-TUI-001",
            "tui_menu",
            "TUI-Menü (whiptail)",
            "green" if live.get("whiptail_available") else "red",
            observed=f"mode={menu_mode} whiptail={live.get('whiptail_available')}",
            next_action="whiptail/dialog installieren" if not live.get("whiptail_available") else "Menü nutzen",
        )
    )

    ui = menu.get("ui_status") if isinstance(menu.get("ui_status"), dict) else {}
    graph_status: MatrixStatus = "gray"
    if ui.get("browser_started"):
        graph_status = "green"
    elif ui.get("display_mode") == "kiosk":
        graph_status = "yellow"
    entries.append(
        _entry(
            "R3-GRAPH-001",
            "graphical_menu",
            "Grafisches Menü / Kiosk",
            graph_status,
            observed=f"display_mode={ui.get('display_mode')} menu_visible={ui.get('menu_visible')}",
            next_action="Browser/Kiosk-Pakete im Live-Build prüfen",
        )
    )

    browsers = live.get("browser_candidates") or []
    entries.append(
        _entry(
            "R3-BROWSER-001",
            "browser_kiosk",
            "Browser im Live-System",
            "green" if any(b in browsers for b in ("chromium", "chromium-browser", "firefox", "firefox-esr")) else "red",
            observed=",".join(browsers) or "none",
            risk="high" if not browsers else "low",
            next_action="chromium/firefox in package-lists vorbereiten (kein apt install)",
        )
    )

    react_ui = Path("/usr/share/setuphelfer/rescue/ui/rescue.html").is_file()
    entries.append(
        _entry(
            "R3-REACT-001",
            "react_rescue_ui",
            "React Rescue UI Bundle",
            "green" if react_ui else "yellow",
            observed=f"rescue.html={react_ui}",
            next_action="UI-Bundle in SquashFS stagen",
        )
    )

    net_json = _read_json(Path("/run/setuphelfer-rescue/network-onboarding.json"))
    wlan_ok = bool(net_json.get("wifi_connected") or net_json.get("wifi_scan_completed"))
    entries.append(
        _entry(
            "R3-WLAN-001",
            "wlan_scan",
            "WLAN-Scan/Verbindung",
            "green" if wlan_ok else ("yellow" if net_json else "unknown"),
            observed=f"wifi_connected={net_json.get('wifi_connected')} error={net_json.get('error_code')}",
            next_action="Netzwerk-Menü im TUI testen",
        )
    )
    entries.append(
        _entry(
            "R3-NET-001",
            "network",
            "Default Route / NetworkManager",
            "green" if net_json.get("default_route_present") else "yellow",
            observed=f"nm_active={live.get('network_manager_active')}",
            next_action="Ethernet/WLAN verbinden oder Offline-Modus",
        )
    )

    spool_dir = Path(str(persist.get("evidence_root", "/tmp"))) / "telemetry" / "spool"
    spool_count = len(list(spool_dir.glob("*.json"))) if spool_dir.is_dir() else 0
    entries.append(
        _entry(
            "R3-TELEM-SPOOL-001",
            "telemetry_spool",
            "Telemetrie-Spool",
            "green" if spool_dir.is_dir() else "yellow",
            observed=f"pending={spool_count}",
            evidence_path=str(spool_dir),
            next_action="Spool-Verzeichnis anlegen",
        )
    )

    ack = _read_json(Path("/run/setuphelfer-rescue/telemetry-last-ack.json"))
    ingest_ok = ack.get("http_status") == 200
    entries.append(
        _entry(
            "R3-TELEM-INGEST-001",
            "telemetry_ingest",
            "Telemetrie-Ingest ACK",
            "green" if ingest_ok else ("yellow" if ack else "unknown"),
            observed=f"http_status={ack.get('http_status')}",
            next_action="Telemetrie nach Netzwerk erneut senden",
        )
    )

    vendor = (bl.get("dmi_vendor") or "").lower()
    is_msi = "msi" in vendor or "micro-star" in vendor
    entries.append(
        _entry(
            "R3-HW-MSI-001",
            "hardware_msi",
            "MSI-Hardware erkannt",
            "green" if is_msi else "gray",
            observed=f"vendor={bl.get('dmi_vendor')} product={bl.get('dmi_product')}",
            next_action="msi_diagnostics_latest.json erzeugen" if is_msi else "Generische HW-Diagnose",
        )
    )

    entries.append(
        _entry(
            "R3-INTERNAL-001",
            "internal_readonly",
            "Interne Datenträger nicht beschrieben",
            "green",
            observed="write_actions_allowed=false (policy)",
            risk="critical",
            next_action="Keine rw-Mounts auf interne NVMe/HDD",
        )
    )

    entries.append(
        _entry(
            "R3-BACKUP-001",
            "backup_target_discovery",
            "Backup-Ziel-Erkennung (read-only)",
            "gray",
            observed="plan-only — kein Backup-Execute",
            next_action="BR-001 nach HW-Boot",
        )
    )
    entries.append(
        _entry(
            "R3-RESTORE-001",
            "restore_gate",
            "Restore-Gate",
            "blocked",
            observed="restore_execution_allowed=false",
            risk="critical",
            next_action="Restore erst nach Verify-Gate",
        )
    )
    entries.append(
        _entry(
            "R3-PART-001",
            "partitions_readonly",
            "Partitionshelfer read-only",
            "green",
            observed="write_allowed=false",
            next_action="Workbench auf Host prüfen",
        )
    )

    tree = ensure_rescue_evidence_tree(runner=runner)
    entries.append(
        _entry(
            "R3-LOGS-001",
            "logs_complete",
            "Evidence-Baum angelegt",
            "green" if tree.get("tree_ready") else "red",
            observed=f"dirs={len(tree.get('created_dirs') or [])}",
            evidence_path=tree.get("evidence_root"),
            next_action="Schreibfehler prüfen" if not tree.get("tree_ready") else "OK",
        )
    )
    entries.append(
        _entry(
            "R3-EVIDENCE-001",
            "evidence_writable",
            "Evidence schreibbar",
            "yellow" if persist.get("fallback") else "green",
            observed=str(persist.get("persistence_mode")),
            risk="medium" if persist.get("fallback") else "low",
            next_action=persist.get("warning") or "OK",
        )
    )

    reds = [e for e in entries if e.get("status") == "red"]
    entries.append(
        _entry(
            "R3-ERR-001",
            "error_summary",
            "Fehlerzusammenfassung",
            "red" if reds else "green",
            observed=f"red_count={len(reds)}",
            next_action=reds[0].get("next_action", "") if reds else "Keine kritischen Blocker",
            risk="high" if reds else "low",
        )
    )
    next_e = reds[0] if reds else next((e for e in entries if e.get("status") == "yellow"), entries[0])
    entries.append(
        _entry(
            "R3-NEXT-001",
            "next_action",
            "Nächste empfohlene Aktion",
            str(next_e.get("status", "unknown")),
            observed=str(next_e.get("title", "")),
            next_action=str(next_e.get("next_action", "")),
        )
    )
    return entries


def build_rescue_test_matrix_document(*, runner: Runner = None) -> dict[str, Any]:
    entries = build_rescue_test_matrix_entries(runner=runner)
    counts = {s: 0 for s in ("green", "yellow", "red", "gray", "blocked", "unknown")}
    for e in entries:
        st = str(e.get("status") or "unknown")
        counts[st] = counts.get(st, 0) + 1
    return {
        "schema_version": 1,
        "matrix_version": RESCUE_TEST_MATRIX_VERSION,
        "generated_at": _utc_now(),
        "entry_count": len(entries),
        "status_counts": counts,
        "entries": entries,
    }


def write_rescue_test_matrix(*, runner: Runner = None) -> dict[str, Any]:
    """Persist latest matrix JSON/MD and append history JSONL."""
    doc = build_rescue_test_matrix_document(runner=runner)
    json_result = write_rescue_json_evidence("matrix", "rescue_test_matrix_latest.json", doc, runner=runner)
    lines = [
        f"# Rescue Test Matrix R.3",
        f"generated_at: {doc['generated_at']}",
        "",
        "| ID | Area | Status | Observed | Next |",
        "|----|------|--------|----------|------|",
    ]
    for e in doc.get("entries") or []:
        if not isinstance(e, dict):
            continue
        lines.append(
            f"| {e.get('id')} | {e.get('area')} | {e.get('status')} | "
            f"{str(e.get('observed', ''))[:60]} | {str(e.get('next_action', ''))[:40]} |"
        )
    md_result = write_rescue_text_evidence("matrix", "rescue_test_matrix_latest.md", "\n".join(lines), runner=runner)

    persist = build_rescue_evidence_root(runner=runner)
    history_path = Path(persist["evidence_root"]) / "matrix" / "rescue_test_matrix_history.jsonl"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_line = json.dumps(
        {"generated_at": doc["generated_at"], "status_counts": doc["status_counts"], "entry_count": doc["entry_count"]},
        ensure_ascii=False,
    )
    with history_path.open("a", encoding="utf-8") as fh:
        fh.write(history_line + "\n")

    return {
        "status": "ok",
        "document": doc,
        "json": json_result,
        "markdown": md_result,
        "history_path": str(history_path),
    }


def build_rescue_test_matrix_diagnostics() -> dict[str, Any]:
    return {
        "matrix_version": RESCUE_TEST_MATRIX_VERSION,
        "module": "core.rescue_test_matrix",
        "areas": list(_MATRIX_AREAS),
        "status_values": ["green", "yellow", "red", "gray", "blocked", "unknown"],
        "public_functions": [
            "build_rescue_test_matrix_entries",
            "build_rescue_test_matrix_document",
            "write_rescue_test_matrix",
            "build_rescue_test_matrix_diagnostics",
        ],
    }
