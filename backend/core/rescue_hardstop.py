"""
Serverseitige Hard-Stops für kontrollierten Rescue-Restore (Phase 3.N3).

Alle Prüfungen rein ableitend aus Request, Grant-Zustand und aktuellen Systemdaten.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from core.device_identity import build_device_identity, compare_device_identity
from modules.rescue_target_assessment import assess_target_device, compare_backup_to_target

Runner = Callable[..., Any] | None


@dataclass
class RestoreHardStopContext:
    """Kontext für Hard-Stop-Auswertung (nach Gate + Pfad-Allowlist)."""

    state: dict[str, Any]
    backup_path: Path
    target_device: str | None
    restore_risk_level: str
    encryption_key_hex: str | None
    runner: Runner = None


def _parent_disk(dev: str, *, runner: Runner = None) -> str | None:
    import subprocess

    run = runner or subprocess.run
    r = run(["lsblk", "-n", "-o", "PKNAME", "-p", dev], capture_output=True, text=True, timeout=30, check=False)
    pk = (r.stdout or "").strip()
    if r.returncode == 0 and pk.startswith("/dev/"):
        return pk
    return dev if dev.startswith("/dev/") else None


def _findmnt_source(path: Path, *, runner: Runner = None) -> str | None:
    import subprocess

    run = runner or subprocess.run
    r = run(
        ["findmnt", "-n", "-o", "SOURCE", "-T", str(path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if r.returncode != 0:
        return None
    line = (r.stdout or "").strip().splitlines()
    return line[0].strip() if line else None


def evaluate_restore_hardstops(ctx: RestoreHardStopContext) -> list[str]:
    """
    Sammelt Hard-Stop-Codes (``rescue.hardstop.*`` und spiegelnde ``rescue.restore.*``).

    Reihenfolge: Backup-Snapshot → Verschlüsselung → Zielidentität → SMART → Quelle=Ziel.
    """
    codes: list[str] = []
    st = ctx.state

    snap = st.get("backup_snapshot") or {}
    try:
        cur_stat = ctx.backup_path.stat()
    except FileNotFoundError:
        codes.append("rescue.restore.backup_missing")
        return codes
    except OSError:
        codes.append("rescue.restore.backup_unreadable")
        return codes

    if snap:
        if int(snap.get("size") or -1) != int(cur_stat.st_size):
            codes.append("rescue.hardstop.backup_corrupt")
            codes.append("rescue.restore.backup_changed")
        if float(snap.get("mtime") or -1.0) != float(cur_stat.st_mtime):
            codes.append("rescue.hardstop.backup_corrupt")
            codes.append("rescue.restore.backup_changed")

    needs_key = bool(st.get("backup_requires_decryption"))
    if needs_key and not (ctx.encryption_key_hex or "").strip():
        codes.append("rescue.hardstop.invalid_key")
        codes.append("rescue.restore.key_missing")

    td = (ctx.target_device or "").strip() or None
    stored_id = st.get("target_device_identity")
    if td and stored_id:
        cur_id = build_device_identity(td, runner=ctx.runner)
        ok, _errs = compare_device_identity(stored_id if isinstance(stored_id, dict) else None, cur_id)
        if not ok:
            codes.append("rescue.hardstop.target_identity_mismatch")
            codes.extend(c for c in _errs if c not in codes)
    elif td and not stored_id:
        codes.append("rescue.hardstop.target_identity_mismatch")
        codes.append("rescue.restore.target_identity_mismatch")

    if td:
        ta = assess_target_device(td, runner=ctx.runner)
        if "rescue.target.smart_critical" in (ta.get("codes") or []):
            codes.append("rescue.hardstop.target_critical")
        if "rescue.target.partition_table_unreadable" in (ta.get("codes") or []):
            codes.append("rescue.restore.target_blocked")
        tgt_cmp = compare_backup_to_target(ctx.backup_path, ta, runner=ctx.runner)
        if tgt_cmp.get("capacity_ok") is False:
            codes.append("rescue.restore.target_too_small")

    if td:
        src_m = _findmnt_source(ctx.backup_path, runner=ctx.runner)
        if src_m and src_m.startswith("/dev/"):
            t_parent = _parent_disk(td, runner=ctx.runner)
            s_parent = _parent_disk(src_m, runner=ctx.runner)
            if t_parent and s_parent:
                try:
                    if Path(t_parent).resolve() == Path(s_parent).resolve():
                        codes.append("rescue.hardstop.source_equals_target")
                except OSError:
                    pass

    return sorted(set(codes))


def enforce_restore_hardstops(ctx: RestoreHardStopContext) -> str | None:
    """Ersten blockierenden Code liefern oder None wenn keine Hard-Stops."""
    found = evaluate_restore_hardstops(ctx)
    priority = (
        "rescue.hardstop.source_equals_target",
        "rescue.hardstop.target_critical",
        "rescue.hardstop.target_identity_mismatch",
        "rescue.hardstop.backup_corrupt",
        "rescue.hardstop.invalid_key",
        "rescue.restore.target_too_small",
        "rescue.restore.target_blocked",
        "rescue.restore.backup_missing",
        "rescue.restore.backup_unreadable",
        "rescue.restore.backup_changed",
        "rescue.restore.key_missing",
    )
    for p in priority:
        if p in found:
            return p
    return found[0] if found else None


__all__ = [
    "RestoreHardStopContext",
    "enforce_restore_hardstops",
    "evaluate_restore_hardstops",
]
