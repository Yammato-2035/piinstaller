"""
Rescue test matrix — machine-readable boot/menu/hardware status (Phase R.3).

Written to /setuphelfer-evidence/matrix/ on each boot or menu start.
"""

from __future__ import annotations

import json
import re
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

RESCUE_TEST_MATRIX_VERSION = 4

MatrixStatus = Literal["green", "yellow", "red", "gray", "blocked", "unknown"]

_PACKAGE_LIST_REL = Path(
    "build/rescue/live-build/setuphelfer-rescue-live/config/package-lists/setuphelfer.list.chroot"
)
_GRUB_THEME_REL = Path(
    "build/rescue/live-build/setuphelfer-rescue-live/config/includes.binary/boot/grub/themes/setuphelfer"
)
_BROWSER_PACKAGES = frozenset({"chromium", "firefox-esr", "firefox", "x-www-browser"})
_DISPLAY_PACKAGES = frozenset({"xserver-xorg", "xinit", "openbox", "dbus-x11"})
_KIOSK_SCRIPTS = (
    "scripts/rescue-live/image/setuphelfer-rescue-kiosk-start",
    "scripts/rescue-live/image/setuphelfer-rescue-kiosk-health",
)
_TELEMETRY_PUSH_REL = Path("scripts/rescue-live/image/setuphelfer-rescue-telemetry-push")

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


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "config" / "version.json").is_file():
            return parent
    return here.parents[2]


def _read_package_names() -> set[str]:
    path = _repo_root() / _PACKAGE_LIST_REL
    if not path.is_file():
        return set()
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        pkg = line.strip().split("#", 1)[0].strip()
        if pkg:
            names.add(pkg)
    return names


def _telemetry_push_has_r3_spool(repo: Path) -> bool:
    push = repo / _TELEMETRY_PUSH_REL
    if not push.is_file():
        return False
    text = push.read_text(encoding="utf-8", errors="replace")
    return "setuphelfer_rescue_r3_telemetry_spool" in text


def build_r4_static_matrix_entries(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    """Static/plannable R.4 build-config matrix entries (no runtime required)."""
    repo = repo_root or _repo_root()
    packages = _read_package_names()
    entries: list[dict[str, Any]] = []

    browser_hit = packages & _BROWSER_PACKAGES
    entries.append(
        _entry(
            "R4-BROWSER-PKG-001",
            "browser_kiosk",
            "Browser in package-list (build)",
            "green" if browser_hit else "red",
            observed=",".join(sorted(browser_hit)) or "none",
            evidence_path=str(_PACKAGE_LIST_REL),
            risk="high" if not browser_hit else "low",
            next_action="chromium in setuphelfer.list.chroot" if not browser_hit else "Rebuild ISO (R.5)",
        )
    )

    display_hit = packages & _DISPLAY_PACKAGES
    display_ok = {"xserver-xorg", "xinit", "openbox"}.issubset(packages)
    entries.append(
        _entry(
            "R4-DISPLAY-PKG-001",
            "graphical_menu",
            "Display-Stack in package-list (build)",
            "green" if display_ok else ("yellow" if display_hit else "red"),
            observed=",".join(sorted(display_hit)) or "none",
            evidence_path=str(_PACKAGE_LIST_REL),
            next_action="xserver-xorg+xinit+openbox ergänzen" if not display_ok else "Rebuild ISO (R.5)",
        )
    )

    kiosk_ok = all((repo / rel).is_file() for rel in _KIOSK_SCRIPTS)
    entries.append(
        _entry(
            "R4-KIOSK-001",
            "browser_kiosk",
            "Kiosk-Startskripte vorhanden",
            "green" if kiosk_ok else "red",
            observed=f"kiosk_scripts={int(kiosk_ok)}",
            evidence_path="scripts/rescue-live/image/setuphelfer-rescue-kiosk-start",
            next_action="Kiosk-Skripte ins Image stagen" if not kiosk_ok else "Autostart in openbox prüfen",
        )
    )

    theme_dir = repo / _GRUB_THEME_REL
    theme_txt = theme_dir / "theme.txt"
    desktop_name = ""
    if theme_txt.is_file():
        match = re.search(r'desktop-image:\s*"([^"]+)"', theme_txt.read_text(encoding="utf-8"))
        desktop_name = match.group(1) if match else ""
    theme_bg = theme_dir / desktop_name if desktop_name else theme_dir / "setuphelfer-boot-menu-de.jpg"
    theme_ok = theme_txt.is_file() and theme_bg.is_file()
    entries.append(
        _entry(
            "R4-GRUB-THEME-001",
            "bootloader",
            "GRUB-Theme konfiguriert (Staging)",
            "green" if theme_ok else "yellow",
            observed=f"theme.txt={theme_txt.is_file()} bg={theme_bg.name}:{theme_bg.is_file()}",
            evidence_path=str(_GRUB_THEME_REL),
            next_action="stage-rescue-graphical-assets.sh ausführen" if not theme_ok else "grub.cfg nach Build prüfen",
        )
    )

    manifest = repo / "build/rescue/asset-manifest.json"
    entries.append(
        _entry(
            "R4-GRUB-ASSETS-001",
            "bootloader",
            "GRUB-Assets/Manifest vorhanden",
            "green" if manifest.is_file() else "yellow",
            observed=f"asset_manifest={manifest.is_file()}",
            evidence_path=str(manifest) if manifest.is_file() else str(_GRUB_THEME_REL),
            next_action="stage-rescue-graphical-assets.sh" if not manifest.is_file() else "verify-rescue-grub-theme.sh",
        )
    )

    spool_integrated = _telemetry_push_has_r3_spool(repo)
    entries.append(
        _entry(
            "R4-TELEM-SPOOL-INT-001",
            "telemetry_spool",
            "Telemetrie-Push nutzt R.3-Spool",
            "green" if spool_integrated else "red",
            observed=f"r3_spool_hooks={spool_integrated}",
            evidence_path=str(_TELEMETRY_PUSH_REL),
            next_action="setuphelfer_rescue_r3_telemetry_spool einbinden" if not spool_integrated else "Retry nach Netzwerk",
        )
    )

    push_present = (repo / _TELEMETRY_PUSH_REL).is_file()
    entries.append(
        _entry(
            "R4-TELEM-PUSH-001",
            "telemetry_ingest",
            "Telemetrie-Push-Skript vorhanden",
            "green" if push_present else "red",
            observed=f"telemetry_push={push_present}",
            evidence_path=str(_TELEMETRY_PUSH_REL),
            next_action="Skript ins sbin stagen" if not push_present else "Ingest nach Boot testen (R.5)",
        )
    )
    return entries


def build_r6_boot_persistence_matrix_entries(*, runner: Runner = None) -> list[dict[str, Any]]:
    """R.6 boot-marker and early persistence hook probes."""
    entries: list[dict[str, Any]] = []
    tree = ensure_rescue_evidence_tree(runner=runner)
    evidence_root = Path(str(tree.get("evidence_root") or ""))
    boot_json = evidence_root / "boot" / "boot_marker.json"
    boot_md = evidence_root / "boot" / "boot_marker.md"
    marker_written = boot_json.is_file() and boot_md.is_file()
    start_assistant = Path("/usr/local/sbin/setuphelfer-rescue-start-assistant").is_file()
    boot_init = Path("/usr/local/sbin/setuphelfer-rescue-boot-evidence-init").is_file()

    entries.append(
        _entry(
            "R6-BOOT-MARKER-001",
            "stick_persistence",
            "boot_marker_written",
            "green" if marker_written else "red",
            observed=f"json={boot_json.is_file()} md={boot_md.is_file()}",
            evidence_path=str(boot_md) if boot_md.is_file() else None,
            risk="high" if not marker_written else "low",
            next_action="boot-evidence-init beim Start prüfen" if not marker_written else "OK",
        )
    )
    entries.append(
        _entry(
            "R6-EVIDENCE-ROOT-001",
            "stick_persistence",
            "evidence_root_created",
            "green" if tree.get("tree_ready") else "red",
            observed=f"root={tree.get('evidence_root')} dirs={len(tree.get('created_dirs') or [])}",
            evidence_path=str(evidence_root),
            next_action="Stick-Mount und Schreibrechte prüfen" if not tree.get("tree_ready") else "OK",
        )
    )
    entries.append(
        _entry(
            "R6-TARGET-STICK-001",
            "stick_persistence",
            "evidence_target_is_stick",
            "green" if not tree.get("fallback") else "yellow",
            observed=str(tree.get("persistence_mode")),
            risk="medium" if tree.get("fallback") else "low",
            next_action=tree.get("warning") or "OK",
        )
    )
    entries.append(
        _entry(
            "R6-TARGET-RAM-001",
            "stick_persistence",
            "evidence_target_is_ram_fallback",
            "yellow" if tree.get("fallback") else "gray",
            observed=f"fallback={tree.get('fallback')}",
            next_action="FAT32 remount rw prüfen" if tree.get("fallback") else "Nicht aktiv",
        )
    )
    entries.append(
        _entry(
            "R6-START-ASSIST-001",
            "tui_menu",
            "start_assistant_invoked",
            "green" if start_assistant else "red",
            observed=f"start_assistant={start_assistant} boot_init={boot_init}",
            next_action="Start-Assistent und boot-evidence-init stagen" if not start_assistant else "OK",
        )
    )
    return entries


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

    entries.extend(build_r4_static_matrix_entries())
    entries.extend(build_r6_boot_persistence_matrix_entries(runner=runner))

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
        f"# Rescue Test Matrix R.{RESCUE_TEST_MATRIX_VERSION}",
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
            "build_r4_static_matrix_entries",
            "build_rescue_test_matrix_document",
            "write_rescue_test_matrix",
            "build_rescue_test_matrix_diagnostics",
        ],
    }
