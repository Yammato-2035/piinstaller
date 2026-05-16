"""
Backup-Ziel: Schreibbarkeit für den systemd-Dienstnutzer (typ. setuphelfer).

Ergänzt validate_write_target (Allowlist/Mount-Gerät) um eine **explizite**
Runtime-Prüfung — erkennt u. a. Desktop-User-Mounts unter /media/<login>/…
mit 0700, die für den Dienst unsichtbar bleiben.

Diagnose-IDs (API-Details, keine stillen Fehler):
  BACKUP-TARGET-PERMISSION-001 — erlaubter Pfad (z. B. unter /mnt/setuphelfer), aber Dienst darf nicht schreiben (Gruppe/ACL/systemd ReadWritePaths).
  BACKUP-TARGET-NOT-WRITABLE-002 — generisch nicht beschreibbar.
  BACKUP-TARGET-USER-MOUNT-003 — typisches udisks-Muster /media/<Benutzer>/… oder /run/media/<Benutzer>/… (nicht setuphelfer), für den Dienst ungeeignet.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

BACKUP_TARGET_PERMISSION_001 = "BACKUP-TARGET-PERMISSION-001"
BACKUP_TARGET_NOT_WRITABLE_002 = "BACKUP-TARGET-NOT-WRITABLE-002"
BACKUP_TARGET_USER_MOUNT_003 = "BACKUP-TARGET-USER-MOUNT-003"
BACKUP_TARGET_EXTERNAL_MOUNT_004 = "BACKUP-TARGET-EXTERNAL-MOUNT-004"

_RE_DIAG = re.compile(r"^(BACKUP-TARGET-[A-Z0-9-]+):\s*(.*)$", re.DOTALL)


def extract_backup_target_diagnosis_id(message: str) -> str | None:
    m = _RE_DIAG.match((message or "").strip())
    return m.group(1) if m else None


def is_user_session_media_tree(resolved: Path) -> bool:
    """
    True, wenn der Pfad unter einem typischen Desktop-Benutzer-Mountbaum liegt
    (/media/<name>/… bzw. /run/media/<name>/…) und <name> != 'setuphelfer'.

    /media/setuphelfer/… ist der empfohlene betreiberseitige Baum (ohne Login-Home-Abhängigkeit).
    """
    parts = resolved.parts
    if len(parts) >= 3 and parts[1] == "media":
        return parts[2] != "setuphelfer"
    if len(parts) >= 4 and parts[1] == "run" and parts[2] == "media":
        return parts[3] != "setuphelfer"
    return False


def _classify_not_writable(resolved: Path, detail: str) -> ValueError:
    if is_user_session_media_tree(resolved):
        return ValueError(
            f"{BACKUP_TARGET_USER_MOUNT_003}: {detail} "
            "(Desktop-User-Mount: Dienstnutzer setuphelfer ist weder Eigentümer noch zuverlässig in der Gruppe; "
            "siehe KB docs/knowledge-base/storage/external-backup-target-architecture.md)"
        )
    rs = str(resolved)
    if rs.startswith("/mnt/setuphelfer/") or rs == "/mnt/setuphelfer":
        return ValueError(
            f"{BACKUP_TARGET_PERMISSION_001}: {detail} "
            "(Ziel unter /mnt/setuphelfer: Gruppe setuphelfer, Modus 0770 und systemd ReadWritePaths prüfen)"
        )
    return ValueError(f"{BACKUP_TARGET_NOT_WRITABLE_002}: {detail}")


def _writable_probe(resolved: Path) -> tuple[bool, str]:
    probe = resolved / f".setuphelfer-wprobe-{os.getpid()}"
    try:
        probe.write_text("", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True, ""
    except OSError as e:
        return False, str(e)
    finally:
        try:
            probe.unlink(missing_ok=True)
        except OSError:
            pass


def assert_backup_target_writable_for_service(resolved: Path) -> None:
    """
    Harte Prüfung nach validate_write_target: Dienst muss Zielverzeichnis anlegen/schreiben können.

    Raises:
        ValueError: Präfix BACKUP-TARGET-* (für diagnosis_id in API-Details).
    """
    try:
        exists = resolved.exists()
    except OSError as e:
        raise ValueError(f"{BACKUP_TARGET_NOT_WRITABLE_002}: Pfad nicht zugänglich ({e})") from e

    if not exists:
        parent = resolved.parent
        while not parent.exists() and parent != parent.parent:
            parent = parent.parent
        if not parent.exists():
            raise ValueError(f"{BACKUP_TARGET_NOT_WRITABLE_002}: Ziel existiert nicht und kein Elternverzeichnis")
        if not os.access(str(parent), os.W_OK | os.X_OK):
            raise _classify_not_writable(
                resolved,
                "Ziel existiert nicht; Elternverzeichnis nicht beschreibbar/begehbar für den Dienstnutzer",
            )
        return

    if not resolved.is_dir():
        raise ValueError(f"{BACKUP_TARGET_NOT_WRITABLE_002}: Backup-Ziel ist kein Verzeichnis")

    if not os.access(str(resolved), os.W_OK | os.X_OK):
        raise _classify_not_writable(
            resolved,
            "Kein Schreib-/Betreten-Recht für den Setuphelfer-Dienst (os.access)",
        )

    ok, err = _writable_probe(resolved)
    if ok:
        return
    raise _classify_not_writable(resolved, f"Schreibprobe fehlgeschlagen ({err})")


def inspect_backup_target_mount(backup_dir_str: str) -> dict[str, Any]:
    """Mount-/Blockgerät-Diagnose inkl. STORAGE-PROTECTION-007-Vorhersage."""
    s = (backup_dir_str or "").strip()
    base = preview_backup_target_access(s)
    try:
        from core.backup_target_auto_prepare import discover_external_backup_candidates

        base["external_candidates"] = [c.to_public_dict() for c in discover_external_backup_candidates()]
    except Exception as exc:  # noqa: BLE001
        base["external_candidates_error"] = str(exc)
    if not s:
        return base
    try:
        from core.safe_device import inspect_write_target_mount

        base["mount_inspection"] = inspect_write_target_mount(s)
        wid = (base.get("mount_inspection") or {}).get("would_block_diagnosis_id")
        if wid == "STORAGE-PROTECTION-007":
            base["diagnosis_hint"] = BACKUP_TARGET_EXTERNAL_MOUNT_004
    except Exception as exc:  # noqa: BLE001
        base["mount_inspection_error"] = str(exc)
    return base


def preview_backup_target_access(backup_dir_str: str) -> dict[str, Any]:
    """
    Read-only / ohne Schreibprobe: os.access + Mountbaum-Hinweis für Cockpit/Dev-Dashboard.

    Keine .wprobe-Datei — vermeidet Side-Effects bei häufigem Polling.
    """
    out: dict[str, Any] = {
        "configured_backup_dir": (backup_dir_str or "").strip(),
        "resolved_path": None,
        "user_session_media_tree": False,
        "likely_writable_by_service": None,
        "diagnosis_hint": None,
    }
    s = (backup_dir_str or "").strip()
    if not s:
        out["likely_writable_by_service"] = None
        return out
    try:
        rp = Path(s).resolve()
    except OSError as e:
        out["diagnosis_hint"] = BACKUP_TARGET_NOT_WRITABLE_002
        out["likely_writable_by_service"] = False
        out["error"] = str(e)
        return out
    out["resolved_path"] = str(rp)
    out["user_session_media_tree"] = is_user_session_media_tree(rp)
    try:
        if not rp.exists():
            parent = rp.parent
            while not parent.exists() and parent != parent.parent:
                parent = parent.parent
            if not parent.exists():
                out["likely_writable_by_service"] = False
                out["diagnosis_hint"] = BACKUP_TARGET_NOT_WRITABLE_002
                return out
            acc = os.access(str(parent), os.W_OK | os.X_OK)
            out["likely_writable_by_service"] = acc
            if not acc:
                out["diagnosis_hint"] = (
                    BACKUP_TARGET_USER_MOUNT_003 if is_user_session_media_tree(rp) else BACKUP_TARGET_NOT_WRITABLE_002
                )
            return out
        if not rp.is_dir():
            out["likely_writable_by_service"] = False
            out["diagnosis_hint"] = BACKUP_TARGET_NOT_WRITABLE_002
            return out
        acc = os.access(str(rp), os.W_OK | os.X_OK)
        out["likely_writable_by_service"] = acc
        if not acc:
            if is_user_session_media_tree(rp):
                out["diagnosis_hint"] = BACKUP_TARGET_USER_MOUNT_003
            elif str(rp).startswith("/mnt/setuphelfer/") or str(rp) == "/mnt/setuphelfer":
                out["diagnosis_hint"] = BACKUP_TARGET_PERMISSION_001
            else:
                out["diagnosis_hint"] = BACKUP_TARGET_NOT_WRITABLE_002
    except OSError as e:
        out["likely_writable_by_service"] = False
        out["diagnosis_hint"] = BACKUP_TARGET_NOT_WRITABLE_002
        out["error"] = str(e)
    return out


def read_configured_backup_dir() -> str | None:
    """Liest backup_dir aus backup.json (gleicher Ort wie app._backup_settings_path)."""
    try:
        from core.install_paths import get_config_dir

        p = get_config_dir() / "backup.json"
        if not p.is_file():
            return None
        raw = json.loads(p.read_text(encoding="utf-8") or "{}")
        bd = (raw.get("backup_dir") or "").strip()
        return bd or None
    except Exception:
        return None


__all__ = [
    "BACKUP_TARGET_EXTERNAL_MOUNT_004",
    "BACKUP_TARGET_NOT_WRITABLE_002",
    "BACKUP_TARGET_PERMISSION_001",
    "BACKUP_TARGET_USER_MOUNT_003",
    "inspect_backup_target_mount",
    "assert_backup_target_writable_for_service",
    "extract_backup_target_diagnosis_id",
    "is_user_session_media_tree",
    "preview_backup_target_access",
    "read_configured_backup_dir",
]
