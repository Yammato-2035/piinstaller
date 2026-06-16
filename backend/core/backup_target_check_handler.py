"""Backup target-check handler (Phase B.3) — extracted from app.py."""

from __future__ import annotations

import os
import shlex
from pathlib import Path
from typing import Any

from core import backup_readonly_runtime as rt
from core.backup_recovery_i18n import tr
from modules.storage_detection import BackupTargetValidationError, validate_backup_target


async def backup_target_check(
    backup_dir: str,
    create: int = 0,
    auto_prepare: int = 0,
    label: str = "br001",
):
    """
    Prüft ein Backup-Ziel:
    - Existenz / optional anlegen (create=1)
    - Freier Speicher (statvfs)
    - Schreibtest (normaler User, fallback: sudo wenn Passwort gespeichert)
    - auto_prepare=1: bei STORAGE-PROTECTION-007 Ziel per sudo vorbereiten (wenn Passwort bekannt)
    """
    prepare_result: dict[str, Any] | None = None
    err_map = rt.backup_target_err_to_api()
    try:
        if not (backup_dir or "").strip():
            from core.backup_target_auto_prepare import setuphelfer_backup_dir

            backup_dir = str(setuphelfer_backup_dir(label or "br001"))
        try:
            backup_dir = rt.validate_backup_dir(backup_dir)
        except Exception as ve:
            msg = str(ve)
            sudo_pw = rt.sudo_password()
            if auto_prepare and ("STORAGE-PROTECTION-007" in msg or "BACKUP-TARGET-EXTERNAL-MOUNT" in msg):
                if sudo_pw:
                    from core.backup_target_auto_prepare import prepare_setuphelfer_external_target

                    prepare_result = prepare_setuphelfer_external_target(
                        label=label or "br001",
                        sudo_password=sudo_pw,
                        run=rt.run_command,
                    )
                    if prepare_result.get("status") == "ready":
                        backup_dir = str(prepare_result.get("backup_dir") or backup_dir)
                        try:
                            backup_dir = rt.validate_backup_dir(backup_dir)
                            msg = ""
                        except Exception as ve2:
                            msg = str(ve2)
            if msg:
                bc = "backup.path_invalid"
                det: dict[str, Any] = {"reason": msg}
                if msg.startswith("STORAGE-PROTECTION-006") or "STORAGE-PROTECTION-006:" in msg:
                    bc = "backup.target_traverse_denied"
                    det["diagnosis_id"] = "STORAGE-PROTECTION-006"
                    det["reason"] = msg.split(":", 1)[1].strip() if ":" in msg else msg
                elif msg.startswith("STORAGE-PROTECTION-007") or "STORAGE-PROTECTION-007:" in msg:
                    bc = "backup.target_external_mount_required"
                    det["diagnosis_id"] = "STORAGE-PROTECTION-007"
                    det["reason"] = msg.split(":", 1)[1].strip() if ":" in msg else msg
                elif "BACKUP-TARGET-AUTO-MOUNT-FAILED" in msg:
                    bc = "backup.target_auto_mount_failed"
                    det["diagnosis_id"] = "BACKUP-TARGET-AUTO-MOUNT-FAILED"
                else:
                    from core.backup_target_service_access import extract_backup_target_diagnosis_id

                    btd = extract_backup_target_diagnosis_id(msg)
                    if btd:
                        det["diagnosis_id"] = btd
                if prepare_result:
                    det["auto_prepare"] = prepare_result
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {"status": "error", "message": f"Ungültiges Backup-Ziel: {msg}"},
                        bc,
                        "error",
                        det,
                    ),
                )

        p = Path(backup_dir)
        sudo_password = rt.sudo_password()
        created = False

        if create and not p.exists():
            mkdir_cmd = f"mkdir -p {shlex.quote(backup_dir)}"
            mkdir_res = rt.run_command(mkdir_cmd)
            if not mkdir_res["success"] and sudo_password:
                mkdir_res = rt.run_command(mkdir_cmd, sudo=True, sudo_password=sudo_password)
            if mkdir_res["success"]:
                created = True
            else:
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "message": f"Zielverzeichnis konnte nicht erstellt werden: {backup_dir}",
                            "created": False,
                        },
                        "backup.mkdir_failed",
                        "error",
                        {"path": backup_dir},
                    ),
                )

        exists = p.exists()
        is_dir = p.is_dir() if exists else False

        fs: dict[str, Any] = {}
        try:
            st = os.statvfs(backup_dir if exists else str(p.parent))
            total = st.f_frsize * st.f_blocks
            free = st.f_frsize * st.f_bavail
            used = total - free
            used_percent = round((used / total) * 100, 1) if total else 0.0

            def human(n: int) -> str:
                for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
                    if n < 1024:
                        return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
                    n /= 1024
                return f"{n:.1f} PB"

            fs = {
                "total_bytes": int(total),
                "free_bytes": int(free),
                "used_percent": used_percent,
                "total_human": human(total),
                "free_human": human(free),
            }
        except Exception:
            fs = {}

        def _best_mount_for_path(path_str: str) -> dict[str, Any] | None:
            path_str = (path_str or "").strip()
            if not path_str:
                return None
            best = None
            best_len = -1
            for mnt in rt.findmnt_mounts():
                tgt = (mnt.get("target") or "").strip()
                if not tgt:
                    continue
                if path_str == tgt or path_str.startswith(tgt.rstrip("/") + "/"):
                    if len(tgt) > best_len:
                        best = mnt
                        best_len = len(tgt)
            return best

        mount_info = None
        try:
            mi = _best_mount_for_path(backup_dir if exists else str(p.parent))
            if mi:
                src = (mi.get("source") or "").strip()
                fstype = (mi.get("fstype") or "").strip()
                opts = (mi.get("options") or "").strip()
                is_ro_mount = ("ro" in [o.strip() for o in opts.split(",") if o.strip()]) if opts else False

                node = rt.find_lsblk_by_name(src) if src.startswith("/dev/") else None
                disk = rt.find_disk_by_name(node.get("pkname") or node.get("name")) if node and node.get("name") else None
                is_usb = bool((disk or node or {}).get("tran") == "usb") if (disk or node) else False
                is_rm = bool((disk or node or {}).get("rm")) if (disk or node) else False
                is_ro_dev = bool((disk or node or {}).get("ro")) if (disk or node) else False

                mount_info = {
                    "target": (mi.get("target") or "").strip(),
                    "source": src,
                    "fstype": fstype,
                    "options": opts,
                    "mount_readonly": is_ro_mount,
                    "device_readonly": is_ro_dev,
                    "is_usb": is_usb,
                    "is_removable": is_rm,
                }
        except Exception:
            mount_info = None

        write_test: dict[str, Any] = {
            "success": False,
            "mode": "user",
            "message": "",
            "reason_code": None,
            "hints": [],
            "suggest_usb_prepare": False,
        }
        if exists and is_dir:
            test_name = f".pi-installer-write-test-{os.getpid()}.tmp"
            test_path = p / test_name
            try:
                test_path.write_text("ok", encoding="utf-8")
                test_path.unlink(missing_ok=True)
                write_test = {
                    "success": True,
                    "mode": "user",
                    "message": "Schreibtest ok (User)",
                    "reason_code": None,
                    "hints": [],
                    "suggest_usb_prepare": False,
                }
            except Exception as e:
                err_user = str(e)
                write_test = {
                    "success": False,
                    "mode": "user",
                    "message": f"Schreibtest fehlgeschlagen (User): {err_user}",
                    "reason_code": None,
                    "hints": [],
                    "suggest_usb_prepare": False,
                }
                if sudo_password:
                    write_test_snippet = (
                        "tmp=$(mktemp -p " + backup_dir + " .pi-installer-write-test.XXXXXX) && echo ok > \"$tmp\" && rm -f \"$tmp\""
                    )
                    cmd = "sh -c " + shlex.quote(write_test_snippet)
                    sudo_res = rt.run_command(cmd, sudo=True, sudo_password=sudo_password)
                    if sudo_res["success"]:
                        write_test = {
                            "success": True,
                            "mode": "sudo",
                            "message": "Schreibtest ok (sudo)",
                            "reason_code": "permissions",
                            "hints": [],
                            "suggest_usb_prepare": False,
                        }
                    else:
                        err_sudo = (sudo_res.get("stderr") or sudo_res.get("error") or "Schreibtest fehlgeschlagen (sudo)").strip()
                        write_test = {
                            "success": False,
                            "mode": "sudo",
                            "message": err_sudo[:200],
                            "reason_code": None,
                            "hints": [],
                            "suggest_usb_prepare": False,
                        }

        if exists and is_dir and not write_test.get("success"):
            combined = write_test.get("message") or ""
            hints: list[str] = []
            reason = None

            fstype = (mount_info or {}).get("fstype") or ""
            is_ro_mount = bool((mount_info or {}).get("mount_readonly"))
            is_ro_dev = bool((mount_info or {}).get("device_readonly"))
            is_usb = bool((mount_info or {}).get("is_usb") or (mount_info or {}).get("is_removable"))

            if fstype in ("iso9660", "udf", "squashfs"):
                reason = "readonly_filesystem"
                hints.append(f"Dateisystem ist read-only ({fstype}).")
            if is_ro_mount:
                reason = reason or "mount_readonly"
                hints.append("Datenträger ist read-only gemountet (mount option ro).")
            if is_ro_dev:
                reason = reason or "device_readonly"
                hints.append("Datenträger ist hardwareseitig/Kernel-seitig schreibgeschützt (RO=1).")

            if "Read-only file system" in combined or "EROFS" in combined:
                reason = reason or "read_only"
                hints.append("Schreibfehler: Read-only file system (EROFS).")
            if "Permission denied" in combined:
                reason = reason or "permission_denied"
                hints.append("Schreibrechte fehlen (Permission denied).")
                hints.append(
                    "Empfohlen: Mount-Punkt root:setuphelfer, Modus 0770; Backend-Unit mit SupplementaryGroups=setuphelfer "
                    "(siehe docs/developer/BACKUP_RECOVERY_ENGINES.md). Optional Test: SETUPHELFER_FIX_PERMISSIONS=1."
                )
                if write_test.get("mode") == "user" and not sudo_password:
                    hints.append("Mit sudo könnte es funktionieren (Sudo-Passwort fehlt / Backend neu gestartet).")
            if "No space left on device" in combined:
                reason = reason or "no_space"
                hints.append("Kein freier Speicher (ENOSPC).")

            suggest_usb_prepare = bool(is_usb and (reason in ("readonly_filesystem", "mount_readonly", "device_readonly", "read_only")))
            if suggest_usb_prepare:
                hints.append(
                    "Hinweis: Schreibtest ist fehlgeschlagen. Der Stick ist evtl. schreibgeschützt oder im falschen "
                    "Dateisystem (z.B. ISO). „USB vorbereiten…“ kann das beheben (Datenverlust)."
                )

            write_test["reason_code"] = reason
            write_test["hints"] = hints
            write_test["suggest_usb_prepare"] = suggest_usb_prepare

        storage_validation: dict[str, Any] = {"ok": True, "i18n_key": None, "detail": None}
        if exists and is_dir:
            probe_arch = p / ".__pi_installer_backup_mount_probe__.tar.gz"
            try:
                validate_backup_target(probe_arch, runner=None)
            except BackupTargetValidationError as e:
                api_code = err_map.get(e.message_key, "backup.failed")
                return rt.with_backup_contract(
                    {
                        "status": "error",
                        "message": tr(e.message_key),
                        "backup_dir": backup_dir,
                        "exists": exists,
                        "is_dir": is_dir,
                        "created": created,
                        "fs": fs,
                        "write_test": write_test,
                        "mount": mount_info,
                        "storage_validation": {"ok": False, "i18n_key": e.message_key, "detail": e.detail},
                    },
                    api_code,
                    "error",
                    {"i18n_key": e.message_key, "detail": e.detail},
                )

        wt_ok = bool(write_test.get("success")) if (exists and is_dir) else True
        tc_code = "backup.target_check_ok" if wt_ok else "backup.target_not_writable"
        tc_sev = "success" if wt_ok else "warning"
        tc_details = None
        if not wt_ok and isinstance(write_test.get("reason_code"), str):
            tc_details = {"reason_code": write_test.get("reason_code")}

        success_payload: dict[str, Any] = {
            "status": "success",
            "backup_dir": backup_dir,
            "exists": exists,
            "is_dir": is_dir,
            "created": created,
            "fs": fs,
            "write_test": write_test,
            "mount": mount_info,
            "storage_validation": storage_validation,
        }
        if prepare_result:
            success_payload["auto_prepare"] = prepare_result
            if prepare_result.get("diagnosis_id"):
                success_payload["diagnosis_id"] = prepare_result.get("diagnosis_id")
        return rt.with_backup_contract(success_payload, tc_code, tc_sev, tc_details)
    except Exception as e:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": str(e)},
                "backup.target_check_failed",
                "error",
                {"detail": str(e)},
            ),
        )
