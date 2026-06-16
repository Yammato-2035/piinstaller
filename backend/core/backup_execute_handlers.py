"""Backup execute handlers — first POST slice (Phase B.4)."""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import shutil
import signal
import tarfile
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import Request

from core import backup_readonly_runtime as rt
from core.backup_profiles import (
    build_profile_preview,
    normalize_backup_profile,
    resolve_profile_request,
)


async def backup_job_cancel(job_id: str):
    job_id = (job_id or "").strip()
    runner_status = rt.read_backup_runner_status(job_id)
    if runner_status:
        rs_st = str(runner_status.get("status") or "").strip().lower()
        rt.sync_ram_job_from_runner(job_id)
        if rs_st == "cancelled":
            return rt.with_backup_contract(
                {"status": "success", "message": "Job bereits abgebrochen"},
                "backup.job_already_done",
                "info",
                {"job_id": job_id},
            )
        if rs_st in ("success", "error", "failed"):
            return rt.with_backup_contract(
                {"status": "success", "message": "Job ist bereits abgeschlossen"},
                "backup.job_already_done",
                "info",
                {"job_id": job_id, "runner_status": rs_st},
            )
        unit_name = str(runner_status.get("unit_name") or "").strip()
        unit_scope = str(runner_status.get("unit_scope") or "system").strip().lower()
        if not unit_name:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract({"status": "error", "message": "Runner-Unit unbekannt"}, "backup.cancel_failed", "error"),
            )
        if unit_scope == "user":
            stop_argv = ["systemctl", "--user", "stop", unit_name]
        else:
            stop_argv = ["systemctl", "stop", unit_name]
        stop_res = rt.systemctl_run_argv(stop_argv, timeout=30)
        if not stop_res.get("success"):
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Abbruch fehlgeschlagen"},
                    "backup.cancel_failed",
                    "error",
                    {"unit_name": unit_name, "stderr": (stop_res.get("stderr") or "")[:300]},
                ),
            )
        return rt.with_backup_contract(
            {"status": "success", "message": "Abbruch angefordert"},
            "backup.cancel_requested",
            "success",
            {"unit_name": unit_name, "unit_scope": unit_scope},
        )

    job = rt.get_backup_jobs().get(job_id)
    if not job:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract({"status": "error", "message": "Job nicht gefunden"}, "backup.job_not_found", "error"),
        )

    if job.get("status") in ("success", "error", "cancelled"):
        return rt.with_backup_contract(
            {"status": "success", "message": "Job ist bereits abgeschlossen"},
            "backup.job_already_done",
            "info",
        )

    cancel_map = rt.get_backup_job_cancel()
    ev = cancel_map.get(job_id)
    if not ev:
        ev = threading.Event()
        cancel_map[job_id] = ev
    ev.set()
    job["status"] = "cancel_requested"
    job["message"] = "Abbruch angefordert…"
    job["code"] = "backup.cancel_requested"
    job["severity"] = "info"

    try:
        pgid = job.get("pgid")
        if isinstance(pgid, int) and pgid > 1:
            os.killpg(pgid, signal.SIGTERM)
    except Exception:
        pass

    return rt.with_backup_contract({"status": "success", "message": "Abbruch angefordert"}, "backup.cancel_requested", "success")


async def backup_job_evidence_collect(job_id: str):
    """Sammelt Diagnose-Artefakte erneut ein (kein Backup-/Restore-Start)."""
    jid = (job_id or "").strip()
    if not rt.backup_job_id_re().fullmatch(jid):
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {
                    "status": "error",
                    "message": "Ungültige job_id",
                    "evidence": {
                        "evidence_status": "invalid_job_id",
                        "evidence_dir": None,
                        "manifest_path": None,
                        "collected_sources": [],
                        "permission_denied_sources": [],
                        "errors": ["invalid_job_id"],
                    },
                },
                "backup.evidence.invalid_job_id",
                "error",
                {"job_id": jid},
            ),
        )
    manifest, err = rt.run_backup_evidence_collect(jid)
    if err:
        ev = rt.normalize_evidence_api_payload(None, None)
        ev["evidence_status"] = "error"
        ev["errors"] = [err]
        return rt.with_backup_contract(
            {"status": "success", "evidence": ev},
            "backup.evidence.collect_failed",
            "info",
            {"job_id": jid},
        )
    mdir = manifest.get("output_dir") if isinstance(manifest, dict) else None
    mp = Path(str(mdir)) / "manifest.json" if mdir else None
    mp_resolved: Optional[Path] = mp if mp and mp.is_file() else None
    ev = rt.normalize_evidence_api_payload(manifest if isinstance(manifest, dict) else None, mp_resolved)
    if ev.get("permission_denied_sources"):
        return rt.with_backup_contract(
            {"status": "success", "evidence": ev},
            "backup.evidence.ok_with_permissions_denied",
            "info",
            {"job_id": jid},
        )
    return rt.with_backup_contract(
        {"status": "success", "evidence": ev},
        "backup.evidence.ok",
        "success",
        {"job_id": jid},
    )


async def backup_profiles_list_post():
    return rt.backup_profiles_list_payload()


async def backup_profile_preview(request: Request):
    """Read-only: Profilbeschreibung und Zielgroesse, kein Backup-Start."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    prof = str(body.get("profile") or "recommended").strip()
    bd_raw = body.get("backup_dir", "")
    try:
        bd = rt.validate_backup_dir(str(bd_raw))
    except Exception as ve:
        from core.backup_target_service_access import extract_backup_target_diagnosis_id

        det: dict[str, Any] = {"reason": str(ve)}
        btd = extract_backup_target_diagnosis_id(str(ve))
        if btd:
            det["diagnosis_id"] = btd
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": f"Ungültiges Backup-Ziel: {str(ve)}"},
                "backup.path_invalid",
                "error",
                det,
            ),
        )
    tf: Optional[int] = None
    try:
        p = Path(bd)
        if p.is_dir():
            tf = int(shutil.disk_usage(str(p)).free)
    except Exception:
        pass
    preview = build_profile_preview(profile_raw=prof, backup_dir=bd, target_free_bytes=tf)
    return rt.with_backup_contract(
        {"status": "success", "preview": preview},
        "backup.profile_preview",
        "success",
        {"profile": prof, "backup_dir": bd},
    )


async def backup_set_settings(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}

    sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
    if not sudo_password:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True},
                "backup.sudo_required",
                "error",
            ),
        )

    settings = data.get("settings") or {}
    # merge + migrate legacy -> schedules[]
    base = rt.ensure_schedule_migration(settings)
    # ensure we keep explicit schedules if provided
    if isinstance(settings.get("schedules"), list):
        base["schedules"] = settings.get("schedules") or []
    if isinstance(settings.get("datasets"), dict):
        base["datasets"] = {**rt.default_backup_settings()["datasets"], **settings.get("datasets")}
    if isinstance(settings.get("state"), dict):
        base["state"] = settings.get("state") or {}

    # validate some fields
    try:
        base["backup_dir"] = rt.validate_backup_dir(base.get("backup_dir", "/mnt/setuphelfer/backups"))
    except Exception as ve:
        from core.backup_target_service_access import extract_backup_target_diagnosis_id
        from core.safety_facade import WriteTargetProtectionError

        details: dict = {"reason": str(ve)}
        btd = extract_backup_target_diagnosis_id(str(ve))
        if btd:
            details["diagnosis_id"] = btd
        if isinstance(ve, WriteTargetProtectionError):
            details["diagnosis_id"] = ve.diagnosis_id
        elif isinstance(ve.__cause__, WriteTargetProtectionError):
            details["diagnosis_id"] = ve.__cause__.diagnosis_id
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": f"Ungültiges Backup-Ziel: {str(ve)}"},
                "backup.path_invalid",
                "error",
                details,
            ),
        )
    try:
        keep = int((base.get("retention") or {}).get("keep_last", 5))
        if keep < 1 or keep > 100:
            raise ValueError()
        base["retention"]["keep_last"] = keep
    except Exception:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": "retention.keep_last muss zwischen 1 und 100 liegen"},
                "backup.settings_retention_invalid",
                "error",
            ),
        )

    # validate schedules basic shape
    try:
        cleaned = []
        for r in (base.get("schedules") or []):
            if not isinstance(r, dict):
                continue
            rid = str(r.get("id") or "").strip()
            if not rid:
                continue
            rr = dict(r)
            rr["id"] = rid
            rr["enabled"] = bool(rr.get("enabled"))
            rr["name"] = str(rr.get("name") or "").strip() or rid
            rr["type"] = str(rr.get("type") or "incremental").strip()
            rr["target"] = str(rr.get("target") or "local").strip()
            rr["keep_last"] = int(rr.get("keep_last") or base["retention"]["keep_last"])
            rr["time"] = str(rr.get("time") or "02:00").strip()
            rr["days"] = rr.get("days") if isinstance(rr.get("days"), list) else ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            cleaned.append(rr)
        base["schedules"] = cleaned
    except Exception:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract({"status": "error", "message": "schedules ist ungültig"}, "backup.schedules_invalid", "error"),
        )

    # store config (root-protected) + apply timer
    rt.write_backup_settings(base, sudo_password=sudo_password)
    rt.apply_backup_schedule(base, sudo_password=sudo_password)

    return rt.with_backup_contract(
        {"status": "success", "message": "Backup-Einstellungen gespeichert", "settings": base},
        "backup.settings_saved",
        "success",
    )



async def backup_run_now(request: Request):
    """Scheduled Backup sofort ausführen (nutzt Runner Script)."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
    if not sudo_password:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True},
                "backup.sudo_required",
                "error",
            ),
        )

    runner = "/usr/local/bin/setuphelfer-backup-run"
    rule_id = (data.get("rule_id") or "").strip()
    # ensure it exists via applying schedule with current settings
    settings = rt.read_backup_settings()
    rt.apply_backup_schedule(settings, sudo_password=sudo_password)
    cmd = runner if not rule_id else f"{runner} --rule {shlex.quote(rule_id)}"
    res = await rt.run_command_async(cmd, sudo=True, sudo_password=sudo_password, timeout=7200)
    ok_cmd = bool(res.get("success"))
    payload = {
        "status": "success" if ok_cmd else "error",
        "stdout": (res.get("stdout") or "").strip()[:4000],
        "stderr": (res.get("stderr") or "").strip()[:4000],
        "returncode": res.get("returncode"),
    }
    return rt.with_backup_contract(
        payload,
        "backup.schedule_run_ok" if ok_cmd else "backup.schedule_run_failed",
        "success" if ok_cmd else "error",
    )



async def backup_cloud_test(request: Request):
    """Testet WebDAV/Seafile Erreichbarkeit (ohne Speichern)."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    url = (data.get("webdav_url") or "").strip()
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not url:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract({"status": "error", "message": "webdav_url erforderlich"}, "backup.cloud_test_missing_url", "error"),
        )
    if not username or not password:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": "username + password erforderlich"},
                "backup.cloud_test_missing_credentials",
                "error",
            ),
        )

    # PROPFIND Depth:0 ist typisch für WebDAV (Status 207 = Multi-Status)
    cmd = (
        "curl -sS -o /dev/null "
        "-w '%{http_code}' "
        f"-u {shlex.quote(username)}:{shlex.quote(password)} "
        "-X PROPFIND -H 'Depth: 0' "
        f"{shlex.quote(url)}"
    )
    res = rt.run_command(cmd)
    code_str = (res.get("stdout") or "").strip()
    try:
        code = int(code_str) if code_str else None
    except Exception:
        code = None

    ok = res.get("success") and (code in (200, 201, 204, 207))
    msg = None
    if not ok:
        if code == 401:
            msg = "401 Unauthorized (Login/Token prüfen)"
        elif code:
            msg = f"HTTP {code} (Server erreichbar, aber Antwort unerwartet)"
        else:
            msg = (res.get("stderr") or "Verbindung fehlgeschlagen").strip()[:300]

    payload = {"status": "success" if ok else "error", "ok": bool(ok), "http_code": code, "message": msg}
    return rt.with_backup_contract(
        payload,
        "backup.cloud_test_ok" if ok else "backup.cloud_test_failed",
        "success" if ok else "error",
        {"http_code": code} if code is not None else None,
    )



async def backup_cloud_delete(request: Request):
    """Löscht ein Cloud-Backup über WebDAV DELETE"""
    try:
        data = await request.json()
    except Exception:
        data = {}
    
    backup_file = (data.get("backup_file") or data.get("href") or "").strip()
    if not backup_file:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": "backup_file oder href erforderlich"},
                "backup.cloud_delete_missing_param",
                "error",
            ),
        )
    
    settings = rt.read_backup_settings()
    cloud = settings.get("cloud") or {}
    if not cloud.get("enabled"):
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": "Cloud-Upload ist deaktiviert"},
                "backup.cloud_delete_disabled",
                "error",
            ),
        )
    
    provider = cloud.get("provider") or "seafile_webdav"
    if provider not in ("seafile_webdav", "webdav", "nextcloud_webdav"):
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": f"Provider '{provider}' wird für Cloud-Löschung nicht unterstützt"},
                "backup.cloud_delete_provider_unsupported",
                "error",
                {"provider": provider},
            ),
        )
    
    url = (cloud.get("webdav_url") or "").strip().rstrip("/")
    user = (cloud.get("username") or "").strip()
    pw = (cloud.get("password") or "").strip()
    
    if not url or not user or not pw:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": "WebDAV URL + Username + Passwort fehlen"},
                "backup.cloud_delete_credentials_missing",
                "error",
            ),
        )
    
    # Verwende base_url aus Request, falls vorhanden (wird vom Frontend gesendet)
    # Sonst konstruiere base aus webdav_url und remote_path
    base_url_from_request = (data.get("base_url") or "").strip()
    remote_path = (cloud.get("remote_path") or "").strip().strip("/")
    
    if base_url_from_request:
        base = base_url_from_request
        if not base.endswith("/"):
            base = base + "/"
    else:
        base = f"{url}/{remote_path}" if remote_path else url
        if not base.endswith("/"):
            base = base + "/"
    
    # backup_file (href) kann sein:
    # 1. Vollständige URL (https://example.com/dav/backups/file.tar.gz)
    # 2. Relativer Pfad zur WebDAV-Root (/dav/backups/file.tar.gz) 
    # 3. Relativer Pfad zur base (file.tar.gz)
    #
    # PROPFIND gibt href relativ zur angeforderten URL zurück.
    # Wenn PROPFIND auf base (z.B. https://example.com/dav/backups/) ausgeführt wird,
    # dann ist href entweder:
    # - Absolut relativ zur Root: /dav/backups/file.tar.gz
    # - Relativ zur base: file.tar.gz
    # - Vollständige URL: https://example.com/dav/backups/file.tar.gz
    
    from urllib.parse import urlparse, urljoin
    
    if backup_file.startswith("http://") or backup_file.startswith("https://"):
        # Vollständige URL - verwende direkt
        remote_url = backup_file
    elif backup_file.startswith("/"):
        # href ist absolut relativ zur WebDAV-Root
        # Kombiniere mit der Domain der base_url
        parsed_base = urlparse(base.rstrip("/"))
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
        remote_url = base_domain + backup_file
    else:
        # href ist relativ zur base - füge zur base hinzu
        # urljoin behandelt relative Pfade korrekt
        remote_url = urljoin(base, backup_file)
    
    # Debug-Informationen für Response (MUSS vor der Verwendung definiert werden)
    debug_info = {
        "webdav_url": url,
        "remote_path": remote_path,
        "base_from_request": base_url_from_request,
        "base": base,
        "backup_file": backup_file,
        "remote_url": remote_url
    }
    
    # WICHTIG: Wenn remote_url mit base beginnt, aber base bereits in href enthalten ist,
    # könnte es zu einer doppelten Pfadstruktur kommen. Prüfe das.
    # Beispiel: base = "https://example.com/dav/backups/", href = "/dav/backups/file.tar.gz"
    # Dann wäre remote_url = "https://example.com/dav/backups/file.tar.gz" (korrekt)
    # Aber wenn base = "https://example.com/dav/backups/", href = "backups/file.tar.gz"
    # Dann wäre remote_url = "https://example.com/dav/backups/backups/file.tar.gz" (falsch!)
    
    # Prüfe, ob der Pfad bereits in base enthalten ist
    parsed_remote = urlparse(remote_url)
    parsed_base_check = urlparse(base.rstrip("/"))
    
    # Wenn der Pfad der remote_url bereits mit dem Pfad der base beginnt, ist es korrekt
    # Sonst könnte es ein Problem geben
    if parsed_remote.path.startswith(parsed_base_check.path):
        # Pfad ist korrekt
        pass
    else:
        # Möglicherweise falsche Konstruktion - versuche es mit base + Dateiname
        filename = backup_file.split("/")[-1]
        alt_remote_url = base.rstrip("/") + "/" + filename
        # Verwende diese nur, wenn sie anders ist
        if alt_remote_url != remote_url:
            debug_info["alternative_construction"] = alt_remote_url
    
    # DELETE Request mit zusätzlichem Debug-Output
    # Zuerst versuchen wir mit der konstruierten URL
    cmd = (
        "curl -sS -o /dev/null -w '%{http_code}' "
        f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
        "-X DELETE "
        f"{shlex.quote(remote_url)}"
    )
    res = rt.run_command(cmd)
    
    if res.get("success"):
        http_code = (res.get("stdout") or "").strip()
        try:
            code = int(http_code)
            if code in (200, 202, 204):
                return rt.with_backup_contract(
                    {"status": "success", "message": "Cloud-Backup gelöscht", "debug": debug_info},
                    "backup.cloud_delete_ok",
                    "success",
                )
            elif code == 404:
                # Debug-Info für 404-Fehler
                debug_info["http_code"] = 404
                # Datei nicht gefunden - versuche mehrere alternative URL-Konstruktionen
                alternatives_tried = [remote_url]
                
                if not backup_file.startswith("http://") and not backup_file.startswith("https://"):
                    # Versuch 1: Nur Dateiname zur base hinzufügen
                    filename = backup_file.split("/")[-1]
                    alt_url1 = base + filename
                    alternatives_tried.append(alt_url1)
                    rt.logger().info(f"[Cloud-Delete] Versuche alternative URL 1: {alt_url1}")
                    
                    cmd_alt1 = (
                        "curl -sS -o /dev/null -w '%{http_code}' "
                        f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
                        "-X DELETE "
                        f"{shlex.quote(alt_url1)}"
                    )
                    res_alt1 = rt.run_command(cmd_alt1)
                    if res_alt1.get("success"):
                        http_code_alt1 = (res_alt1.get("stdout") or "").strip()
                        try:
                            code_alt1 = int(http_code_alt1)
                            if code_alt1 in (200, 202, 204):
                                debug_info["successful_alternative"] = alt_url1
                                return rt.with_backup_contract(
                                    {"status": "success", "message": "Cloud-Backup gelöscht", "debug": debug_info},
                                    "backup.cloud_delete_ok",
                                    "success",
                                )
                        except ValueError:
                            pass
                    
                    # Versuch 2: Wenn href mit / beginnt, entferne führenden / und kombiniere mit base
                    if backup_file.startswith("/"):
                        # Entferne führenden Slash und kombiniere mit base
                        path_without_leading_slash = backup_file.lstrip("/")
                        # Entferne remote_path aus dem Pfad, falls vorhanden
                        if remote_path:
                            path_parts = path_without_leading_slash.split("/")
                            remote_path_parts = remote_path.strip("/").split("/")
                            # Prüfe, ob der Pfad mit remote_path beginnt
                            if len(path_parts) >= len(remote_path_parts):
                                if path_parts[:len(remote_path_parts)] == remote_path_parts:
                                    # Entferne remote_path-Teil
                                    path_without_leading_slash = "/".join(path_parts[len(remote_path_parts):])
                        alt_url2 = base.rstrip("/") + "/" + path_without_leading_slash
                        alternatives_tried.append(alt_url2)
                        rt.logger().info(f"[Cloud-Delete] Versuche alternative URL 2: {alt_url2}")
                        
                        cmd_alt2 = (
                            "curl -sS -o /dev/null -w '%{http_code}' "
                            f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
                            "-X DELETE "
                            f"{shlex.quote(alt_url2)}"
                        )
                        res_alt2 = rt.run_command(cmd_alt2)
                        if res_alt2.get("success"):
                            http_code_alt2 = (res_alt2.get("stdout") or "").strip()
                            try:
                                code_alt2 = int(http_code_alt2)
                                if code_alt2 in (200, 202, 204):
                                    debug_info["successful_alternative"] = alt_url2
                                    return rt.with_backup_contract(
                                        {"status": "success", "message": "Cloud-Backup gelöscht", "debug": debug_info},
                                        "backup.cloud_delete_ok",
                                        "success",
                                    )
                            except ValueError:
                                pass
                
                # Datei nicht gefunden - könnte bereits gelöscht sein oder falscher Pfad
                debug_info["alternatives_tried"] = alternatives_tried[:5]
                debug_info["http_code"] = code
                debug_info["final_remote_url"] = remote_url[:200]
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "message": f"Datei nicht gefunden (HTTP 404). Versuchte URLs: {', '.join(alternatives_tried[:3])}",
                            "http_code": code,
                            "remote_url": remote_url[:200],
                            "backup_file": backup_file[:200],
                            "alternatives_tried": alternatives_tried[:5],
                            "debug": debug_info,
                        },
                        "backup.cloud_delete_not_found",
                        "error",
                        {"http_code": code},
                    ),
                )
            else:
                debug_info["http_code"] = code
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "message": f"Löschung fehlgeschlagen (HTTP {code})",
                            "http_code": code,
                            "remote_url": remote_url[:200],
                            "debug": debug_info,
                        },
                        "backup.cloud_delete_http_error",
                        "error",
                        {"http_code": code},
                    ),
                )
        except ValueError:
            debug_info["http_code_error"] = http_code
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": f"Ungültige HTTP-Antwort: {http_code}", "debug": debug_info},
                    "backup.cloud_delete_invalid_response",
                    "error",
                ),
            )
    else:
        error_msg = res.get("stderr") or res.get("error") or "Unbekannter Fehler"
        debug_info["curl_error"] = error_msg[:200]
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": f"Löschung fehlgeschlagen: {error_msg[:200]}", "debug": debug_info},
                "backup.cloud_delete_curl_failed",
                "error",
            ),
        )



async def backup_cloud_verify(request: Request):
    """Verifiziert ein einzelnes Remote-Backup via WebDAV PROPFIND Depth:0."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    name = (data.get("name") or "").strip()
    settings = rt.read_backup_settings()
    cloud = settings.get("cloud") or {}
    url = (cloud.get("webdav_url") or "").strip().rstrip("/")
    user = (cloud.get("username") or "").strip()
    pw = (cloud.get("password") or "").strip()
    remote_path = (cloud.get("remote_path") or "").strip().strip("/")

    if not name or not name.endswith(".tar.gz"):
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": "name (.tar.gz) erforderlich"},
                "backup.cloud_verify_missing_name",
                "error",
            ),
        )
    if not url or not user or not pw:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": "WebDAV Settings fehlen"},
                "backup.cloud_verify_settings_incomplete",
                "error",
            ),
        )

    base = f"{url}/{remote_path}" if remote_path else url
    if not base.endswith("/"):
        base += "/"
    remote = f"{base}{name}"
    cmd = (
        "curl -sS -o /dev/null "
        "-w '%{http_code}' "
        f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
        "-X PROPFIND -H 'Depth: 0' "
        f"{shlex.quote(remote)}"
    )
    res = rt.run_command(cmd)
    code_str = (res.get("stdout") or "").strip()
    try:
        code = int(code_str) if code_str else None
    except Exception:
        code = None
    ok = res.get("success") and (code in (200, 201, 204, 207))
    payload = {"status": "success" if ok else "error", "ok": bool(ok), "http_code": code, "remote": remote}
    return rt.with_backup_contract(
        payload,
        "backup.cloud_verify_ok" if ok else "backup.cloud_verify_failed",
        "success" if ok else "error",
        {"http_code": code} if code is not None else None,
    )


async def backup_target_prepare(request: Request):
    """
    Bereitet /media/setuphelfer/<label> auf (Bind- oder Direkt-Mount, root:setuphelfer 0770).
    Erfordert sudo_password. Kein Formatieren, keine Löschung fremder Daten.
    """
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}
        label = str(data.get("label") or "br001").strip()
        uuid = (data.get("uuid") or data.get("partition_uuid") or "").strip() or None
        partition = (data.get("partition") or data.get("device") or "").strip() or None
        mode = str(data.get("mode") or "auto").strip().lower()
        sudo_password = (data.get("sudo_password") or "").strip() or (rt.sudo_store().get_password() or "")
        if not sudo_password:
            sudo_test = rt.run_command("sudo -n true", sudo=False)
            if not sudo_test.get("success"):
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True},
                        "backup.sudo_required",
                        "error",
                    ),
                )
        from core.backup_target_auto_prepare import (
            BACKUP_TARGET_AUTO_MOUNT_FAILED,
            BACKUP_TARGET_AUTO_MOUNT_READY,
            prepare_setuphelfer_external_target,
        )

        result = prepare_setuphelfer_external_target(
            label=label,
            sudo_password=sudo_password,
            run=rt.run_command,
            uuid=uuid,
            partition=partition,
            mode=mode,
        )
        diag = result.get("diagnosis_id")
        if result.get("status") == "ready":
            return rt.with_backup_contract(
                result,
                "backup.target_auto_mount_ready",
                "success",
                {"diagnosis_id": BACKUP_TARGET_AUTO_MOUNT_READY, "backup_dir": result.get("backup_dir")},
            )
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                result,
                "backup.target_auto_mount_failed",
                "error",
                {"diagnosis_id": BACKUP_TARGET_AUTO_MOUNT_FAILED},
            ),
        )
    except Exception as e:
        rt.logger().exception("backup_target_prepare failed")
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": str(e)},
                "backup.target_auto_mount_failed",
                "error",
                {"detail": str(e)},
            ),
        )


async def backup_usb_mount(request: Request):
    """
    Mountet ein (noch) ungemountetes USB-Device (Partition) nach /mnt/pi-installer-usb/<name>.
    Nicht-destruktiv: kein Formatieren, kein Label ändern.
    """
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}

        device = (data.get("device") or "").strip()
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")

        if not device or not device.startswith("/dev/"):
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "device (/dev/...) erforderlich"},
                    "backup.usb_mount_missing_device",
                    "error",
                ),
            )
        if not sudo_password:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True},
                    "backup.sudo_required",
                    "error",
                ),
            )

        node = rt.find_lsblk_by_name(device)
        if not node:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "USB-Gerät nicht gefunden"},
                    "backup.usb_not_found",
                    "error",
                ),
            )

        # bereits gemountet? -> bestehenden Mountpoint zurückgeben
        system_mounts = {"/", "/boot", "/boot/firmware", "[SWAP]"}
        mps = node.get("mountpoints")
        mp = node.get("mountpoint")
        existing = None
        if isinstance(mps, list):
            for one in mps:
                if one and one not in system_mounts:
                    existing = one
                    break
        elif mp and mp not in system_mounts:
            existing = mp
        if existing:
            return rt.with_backup_contract(
                {"status": "success", "message": "Bereits gemountet", "mounted_to": existing, "device": device},
                "backup.usb_already_mounted",
                "info",
                {"mounted_to": existing},
            )

        part_name = node.get("name")
        pk = node.get("pkname")
        disk_name = pk or (part_name if node.get("type") == "disk" else None)
        if not disk_name:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Konnte Disk nicht bestimmen"},
                    "backup.usb_disk_unknown",
                    "error",
                ),
            )

        disk = rt.find_disk_by_name(disk_name)
        if not disk:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract({"status": "error", "message": "Disk nicht gefunden"}, "backup.usb_disk_not_found", "error"),
            )

        # Safety: nur USB/removable, nie Systemdisk
        is_usb = (disk.get("tran") == "usb")
        is_rm = bool(disk.get("rm"))
        if not (is_usb or is_rm):
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Nur USB/Removable Datenträger sind erlaubt"},
                    "backup.usb_not_removable",
                    "error",
                ),
            )
        if rt.disk_is_system(disk):
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Refused: System-Datenträger erkannt"},
                    "backup.usb_refused_system",
                    "error",
                ),
            )

        # Mount directory name
        def safe_seg(s: str) -> str:
            s = (s or "").strip()
            if not s:
                return ""
            allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
            out = []
            for ch in s.replace(" ", "_"):
                if ch in allowed:
                    out.append(ch)
            return "".join(out)[:32].strip("_") or ""

        label = str(node.get("label") or "")
        seg = safe_seg(label) or safe_seg(str(part_name or "")) or safe_seg(str(disk_name or "")) or "USB"
        mount_dir = f"/mnt/pi-installer-usb/{seg}"

        # mount
        rt.run_command(f"mkdir -p {shlex.quote(mount_dir)}", sudo=True, sudo_password=sudo_password, timeout=30)
        uid = os.getuid()
        gid = os.getgid()
        fstype = (node.get("fstype") or "").strip().lower()
        mount_opts = "rw"
        # Non-POSIX FS (vfat/exfat/ntfs) need uid/gid so UI user can write
        if fstype in ("vfat", "fat", "msdos", "exfat", "ntfs", "ntfs3"):
            mount_opts = f"rw,uid={uid},gid={gid},umask=0022"
        mnt_cmd = f"mount -o {shlex.quote(mount_opts)} {shlex.quote(device)} {shlex.quote(mount_dir)}"
        mnt = rt.run_command(mnt_cmd, sudo=True, sudo_password=sudo_password, timeout=60)
        if not mnt.get("success"):
            msg = (mnt.get("stderr") or mnt.get("stdout") or mnt.get("error") or "Mount fehlgeschlagen").strip()[:300]
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract({"status": "error", "message": msg}, "backup.usb_mount_failed", "error"),
            )

        # ensure backup folder exists and is writable for current user
        backups_dir = f"{mount_dir}/pi-installer-backups"
        rt.run_command(f"mkdir -p {shlex.quote(backups_dir)}", sudo=True, sudo_password=sudo_password, timeout=30)
        rt.run_command(f"chmod 0775 {shlex.quote(mount_dir)} {shlex.quote(backups_dir)}", sudo=True, sudo_password=sudo_password, timeout=30)
        rt.run_command(f"chown {uid}:{gid} {shlex.quote(mount_dir)} {shlex.quote(backups_dir)}", sudo=True, sudo_password=sudo_password, timeout=30)

        return rt.with_backup_contract(
            {"status": "success", "message": "Gemountet", "mounted_to": mount_dir, "device": device, "label": label or None},
            "backup.usb_mount_ok",
            "success",
            {"mounted_to": mount_dir},
        )
    except Exception as e:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract({"status": "error", "message": str(e)}, "backup.usb_mount_failed", "error", {"detail": str(e)}),
        )


async def backup_usb_prepare(request: Request):
    """
    USB vorbereiten:
    - optional formatieren (Datenverlust!)
    - optional umbenennen (Label)
    - mounten auf /mnt/pi-installer-usb/<label>
    """
    try:
        data = await request.json()
        mountpoint = (data.get("mountpoint") or "").strip()
        device = (data.get("device") or "").strip()
        do_format = bool(data.get("format", False))
        new_label_raw = data.get("label", "")
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")

        if not sudo_password:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True},
                    "backup.sudo_required",
                    "error",
                ),
            )

        node = rt.find_lsblk_by_mountpoint(mountpoint) if mountpoint else None
        if not node and mountpoint:
            for fs in rt.findmnt_mounts():
                tgt = (fs.get("target") or "").strip()
                src = (fs.get("source") or "").strip()
                if tgt and src and tgt == mountpoint and src.startswith("/dev/"):
                    node = rt.find_lsblk_by_name(src)
                    break
        if not node and device:
            node = rt.find_lsblk_by_name(device)
        if not node:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Mountpoint nicht gefunden"},
                    "backup.usb_prepare_mount_not_found",
                    "error",
                ),
            )

        part_name = node.get("name")
        pk = node.get("pkname")
        disk_name = pk or (part_name if node.get("type") == "disk" else None)
        if not disk_name:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Konnte Disk nicht bestimmen"},
                    "backup.usb_disk_unknown",
                    "error",
                ),
            )

        disk = rt.find_disk_by_name(disk_name)
        if not disk:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract({"status": "error", "message": "Disk nicht gefunden"}, "backup.usb_disk_not_found", "error"),
            )

        # Safety: nur USB/removable, nie Systemdisk
        is_usb = (disk.get("tran") == "usb")
        is_rm = bool(disk.get("rm"))
        if not (is_usb or is_rm):
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Nur USB/Removable Datenträger sind erlaubt"},
                    "backup.usb_not_removable",
                    "error",
                ),
            )
        if rt.disk_is_system(disk):
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Refused: System-Datenträger erkannt"},
                    "backup.usb_refused_system",
                    "error",
                ),
            )

        new_label = None
        if new_label_raw:
            new_label = rt.sanitize_label(new_label_raw, max_len=16)

        results = []

        disk_dev = f"/dev/{disk_name}"
        part_dev = f"/dev/{part_name}" if part_name else None

        def step(cmd: str, label: str, allow_fail: bool = False) -> dict:
            res = rt.run_command(cmd, sudo=True, sudo_password=sudo_password, timeout=120)
            ok = bool(res.get("success"))
            if ok:
                results.append(f"✅ {label}")
                return res
            msg = (res.get("stderr") or res.get("stdout") or res.get("error") or "").strip()
            msg = msg[:300] if msg else "Unbekannter Fehler"
            results.append(f"❌ {label}: {msg}")
            if allow_fail:
                return res
            return {"_failed": True, "label": label, "message": msg, "raw": res}

        # quick tool checks (helps on minimal images)
        for tool in ("wipefs", "parted", "mkfs.ext4", "partprobe", "mount", "umount"):
            w = rt.run_command(f"which {shlex.quote(tool)} 2>/dev/null")
            if not w.get("success"):
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {"status": "error", "message": f"Formatierung nicht möglich: Tool fehlt ({tool})", "results": results},
                        "backup.usb_prepare_tool_missing",
                        "error",
                        {"tool": tool},
                    ),
                )

        # refuse hardware RO
        if bool(disk.get("ro")) or bool(node.get("ro")):
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "message": "Formatierung nicht möglich: Datenträger ist schreibgeschützt (RO=1).",
                        "results": results,
                    },
                    "backup.usb_readonly",
                    "error",
                ),
            )

        # Unmount (erforderlich für wipefs/parted/mkfs)
        # 1) explizit den ausgewählten Mountpoint unmounten (auch mit Spaces)
        if mountpoint:
            step(f"umount {shlex.quote(mountpoint)}", f"Unmount {mountpoint}", allow_fail=True)
            step(f"umount -l {shlex.quote(mountpoint)}", f"Lazy-Unmount {mountpoint}", allow_fail=True)

        # 2) alles von dieser Disk unmounten (sicher)
        for mp in rt.mountpoints_for_disk(disk_dev):
            step(f"umount {shlex.quote(mp)}", f"Unmount {mp}", allow_fail=True)
            step(f"umount -l {shlex.quote(mp)}", f"Lazy-Unmount {mp}", allow_fail=True)

        # 3) prüfen ob noch etwas gemountet ist -> dann abbrechen
        remaining = rt.mountpoints_for_disk(disk_dev)
        if remaining:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "message": (
                            "Der USB-Stick ist noch gemountet oder wird von einem Prozess verwendet. "
                            "Bitte schließen Sie alle Fenster/Programme, die auf den Stick zugreifen, und versuchen Sie es erneut."
                        ),
                        "still_mounted": remaining,
                    },
                    "backup.usb_still_mounted",
                    "error",
                ),
            )

        mounted_to = None

        if do_format:
            if not new_label:
                new_label = "PI-INSTALLER"

            # Partition table + single partition
            # Achtung: extrem destruktiv -> nur nach explizitem User-Confirm im Frontend aufrufen!
            results.append(f"Formatierung gestartet: {disk_dev}")
            r = step(f"wipefs -a {shlex.quote(disk_dev)}", f"wipefs auf {disk_dev}")
            if r.get("_failed"):
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {"status": "error", "message": f"Formatierung fehlgeschlagen bei wipefs: {r['message']}", "results": results},
                        "backup.usb_prepare_format_failed",
                        "error",
                    ),
                )

            r = step(f"parted -s {shlex.quote(disk_dev)} mklabel gpt", f"Partitionstabelle GPT erstellen ({disk_dev})")
            if r.get("_failed"):
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {"status": "error", "message": f"Formatierung fehlgeschlagen bei parted mklabel: {r['message']}", "results": results},
                        "backup.usb_prepare_format_failed",
                        "error",
                    ),
                )

            r = step(f"parted -s {shlex.quote(disk_dev)} mkpart primary 1MiB 100%", f"Partition erstellen ({disk_dev})")
            if r.get("_failed"):
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {"status": "error", "message": f"Formatierung fehlgeschlagen bei parted mkpart: {r['message']}", "results": results},
                        "backup.usb_prepare_format_failed",
                        "error",
                    ),
                )

            # Let kernel settle
            step("partprobe", "partprobe", allow_fail=True)
            step("udevadm settle 2>/dev/null", "udevadm settle", allow_fail=True)

            # Bestimme neue Partition (meist ...1)
            part_guess = f"{disk_dev}1"
            # mkfs ext4
            r = step(f"mkfs.ext4 -F -L {shlex.quote(new_label)} {shlex.quote(part_guess)}", f"mkfs.ext4 ({part_guess})")
            if r.get("_failed"):
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {"status": "error", "message": f"Formatierung fehlgeschlagen bei mkfs.ext4: {r['message']}", "results": results},
                        "backup.usb_prepare_format_failed",
                        "error",
                    ),
                )
            results.append("Dateisystem ext4 erstellt")
            part_dev = part_guess
        else:
            # Rename only (best effort)
            if new_label and part_dev:
                fstype = node.get("fstype") or ""
                if fstype == "ext4":
                    rn = rt.run_command(f"e2label {shlex.quote(part_dev)} {shlex.quote(new_label)}", sudo=True, sudo_password=sudo_password)
                    if rn["success"]:
                        results.append(f"Label gesetzt: {new_label}")
                    else:
                        results.append(f"Label setzen fehlgeschlagen: {rn.get('stderr','')[:120]}")
                elif fstype in ("vfat", "fat", "msdos"):
                    rn = rt.run_command(f"fatlabel {shlex.quote(part_dev)} {shlex.quote(new_label)}", sudo=True, sudo_password=sudo_password)
                    if rn["success"]:
                        results.append(f"Label gesetzt: {new_label}")
                    else:
                        results.append(f"Label setzen fehlgeschlagen: {rn.get('stderr','')[:120]}")
                else:
                    results.append(f"Umbenennen nicht unterstützt für fstype={fstype} (bitte formatieren)")

        # Mount after format/rename (optional, to stable path)
        if part_dev and (do_format or new_label):
            label_for_mount = (new_label or "PI-INSTALLER").replace(" ", "_")
            mount_dir = f"/mnt/pi-installer-usb/{label_for_mount}"
            step(f"mkdir -p {shlex.quote(mount_dir)}", f"Mount-Verzeichnis anlegen ({mount_dir})")
            mnt = step(f"mount {shlex.quote(part_dev)} {shlex.quote(mount_dir)}", f"Mount {part_dev} -> {mount_dir}", allow_fail=True)
            if mnt.get("success"):
                mounted_to = mount_dir
                results.append(f"Gemountet: {mount_dir}")
            else:
                # give actionable hint
                err = (mnt.get("stderr") or mnt.get("stdout") or mnt.get("error") or "").strip()[:200]
                results.append(f"Mount fehlgeschlagen: {err}")

        return rt.with_backup_contract(
            {
                "status": "success",
                "message": "USB vorbereitet",
                "results": results,
                "mounted_to": mounted_to,
                "disk": disk_dev,
                "partition": part_dev,
                "label": new_label,
            },
            "backup.usb_prepare_ok",
            "success",
        )
    except Exception as e:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract({"status": "error", "message": str(e)}, "backup.usb_prepare_failed", "error", {"detail": str(e)}),
        )


async def backup_usb_eject(request: Request):
    """
    USB sicher auswerfen:
    - sync
    - unmount (alle Mountpoints der Disk)
    - optional power-off (udisksctl), wenn verfügbar
    """
    try:
        data = await request.json()
        mountpoint = (data.get("mountpoint") or "").strip()
        device = (data.get("device") or "").strip()
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")

        if not sudo_password:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True},
                    "backup.sudo_required",
                    "error",
                ),
            )

        node = rt.find_lsblk_by_mountpoint(mountpoint) if mountpoint else None
        if not node and device:
            node = rt.find_lsblk_by_name(device)
        if not node:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "USB-Gerät nicht gefunden (Mountpoint/Device)"},
                    "backup.usb_not_found",
                    "error",
                ),
            )

        part_name = node.get("name")
        pk = node.get("pkname")
        disk_name = pk or (part_name if node.get("type") == "disk" else None)
        if not disk_name:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Konnte Disk nicht bestimmen"},
                    "backup.usb_disk_unknown",
                    "error",
                ),
            )

        disk = rt.find_disk_by_name(disk_name)
        if not disk:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract({"status": "error", "message": "Disk nicht gefunden"}, "backup.usb_disk_not_found", "error"),
            )

        # Safety
        is_usb = (disk.get("tran") == "usb")
        is_rm = bool(disk.get("rm"))
        if not (is_usb or is_rm):
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Nur USB/Removable Datenträger sind erlaubt"},
                    "backup.usb_not_removable",
                    "error",
                ),
            )
        if rt.disk_is_system(disk):
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Refused: System-Datenträger erkannt"},
                    "backup.usb_refused_system",
                    "error",
                ),
            )

        disk_dev = f"/dev/{disk_name}"

        results = []
        rt.run_command("sync", sudo=True, sudo_password=sudo_password)
        results.append("sync ausgeführt")

        # Unmount all mountpoints for disk
        for mp in rt.mountpoints_for_disk(disk_dev):
            rt.run_command(f"umount {shlex.quote(mp)}", sudo=True, sudo_password=sudo_password)
            rt.run_command(f"umount -l {shlex.quote(mp)}", sudo=True, sudo_password=sudo_password)

        remaining = rt.mountpoints_for_disk(disk_dev)
        if remaining:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "message": "Auswerfen fehlgeschlagen: Datenträger ist noch gemountet/busy",
                        "still_mounted": remaining,
                        "results": results,
                    },
                    "backup.usb_eject_busy",
                    "error",
                ),
            )
        results.append("Unmount erfolgreich")

        # Optional: power off
        power_off = None
        which = rt.run_command("which udisksctl 2>/dev/null")
        if which["success"] and which.get("stdout", "").strip():
            po = rt.run_command(f"udisksctl power-off -b {shlex.quote(disk_dev)}", sudo=True, sudo_password=sudo_password)
            if po["success"]:
                power_off = True
                results.append("udisksctl power-off erfolgreich")
            else:
                power_off = False
                results.append(f"udisksctl power-off fehlgeschlagen: {(po.get('stderr') or '')[:120]}")

        return rt.with_backup_contract(
            {
                "status": "success",
                "message": "USB sicher ausgeworfen",
                "disk": disk_dev,
                "results": results,
                "power_off": power_off,
            },
            "backup.usb_eject_ok",
            "success",
            {"power_off": power_off is True},
        )
    except Exception as e:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract({"status": "error", "message": str(e)}, "backup.usb_eject_failed", "error", {"detail": str(e)}),
        )


async def clone_disk(request: Request):
    """System von SD-Karte auf Ziellaufwerk klonen (async Job)."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}

        sudo_password = (data.get("sudo_password") or "").strip() or (rt.sudo_store().get_password() or "")
        target_device = (data.get("target_device") or "").strip()

        if not target_device or not target_device.startswith("/dev/"):
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "target_device (/dev/...) erforderlich"},
                    "backup.clone_missing_target",
                    "error",
                ),
            )
        if not sudo_password:
            sudo_test = rt.run_command("sudo -n true", sudo=False)
            if not sudo_test.get("success"):
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True},
                        "backup.sudo_required",
                        "error",
                    ),
                )

        if rt.has_active_long_running_job():
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "message": "Es läuft bereits ein Backup- oder Klon-Auftrag.",
                    },
                    "backup.job_conflict",
                    "error",
                ),
            )

        job_id = rt.new_job_id()
        rt.get_backup_jobs()[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "type": "clone",
            "target_device": target_device,
            "started_at": rt.now_iso(),
            "finished_at": None,
            "message": "Wartet…",
            "code": "backup.clone_job_queued",
            "severity": "info",
            "results": [],
        }

        def _runner():
            try:
                ev = rt.get_backup_job_cancel().get(job_id)
                if not ev:
                    ev = threading.Event()
                    rt.get_backup_job_cancel()[job_id] = ev
                rt.get_backup_jobs()[job_id]["status"] = "running"
                rt.get_backup_jobs()[job_id]["message"] = "Klon läuft…"
                rt.get_backup_jobs()[job_id]["code"] = "backup.clone_job_running"
                rt.get_backup_jobs()[job_id]["severity"] = "info"
                result = rt.do_clone_logic(target_device, sudo_password, rt.get_backup_jobs()[job_id], cancel_event=ev)
                rt.get_backup_jobs()[job_id]["results"] = result.get("results") or []
                rt.get_backup_jobs()[job_id]["finished_at"] = rt.now_iso()
                rt.get_backup_jobs()[job_id]["status"] = result.get("status", "error")
                rt.get_backup_jobs()[job_id]["message"] = result.get("message", "Fertig")
                if isinstance(result.get("code"), str):
                    rt.get_backup_jobs()[job_id]["code"] = result["code"]
                if isinstance(result.get("severity"), str):
                    rt.get_backup_jobs()[job_id]["severity"] = result["severity"]
            except Exception as e:
                rt.logger().exception("clone job failed")
                rt.get_backup_jobs()[job_id]["status"] = "error"
                rt.get_backup_jobs()[job_id]["message"] = str(e)
                rt.get_backup_jobs()[job_id]["code"] = "backup.clone_failed"
                rt.get_backup_jobs()[job_id]["severity"] = "error"
                rt.get_backup_jobs()[job_id]["finished_at"] = rt.now_iso()
            finally:
                rt.get_backup_job_cancel().pop(job_id, None)

        t = threading.Thread(target=_runner, daemon=True)
        t.start()

        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "accepted", "job_id": job_id, "message": "Klon-Job gestartet"},
                "backup.clone_started",
                "success",
                {"job_id": job_id},
            ),
        )
    except Exception as e:
        rt.logger().exception("clone endpoint failed")
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract({"status": "error", "message": str(e)}, "backup.clone_failed", "error", {"detail": str(e)}),
        )


async def create_backup(request: Request):
    """Backup erstellen (optional async job)."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        data = rt.normalize_backup_create_crypto_payload(data if isinstance(data, dict) else {})
        encrypt_requested = bool((data.get("encryption_method") or "").strip())
        enc_flag = data.get("encryption")
        wants_enc_flag = enc_flag is True or (isinstance(enc_flag, str) and enc_flag.strip().lower() in ("true", "1", "yes"))
        if wants_enc_flag and not (data.get("encryption_key") or "").strip():
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "message": "Verschlüsselung angefordert, aber kein Passwort/Schlüssel (password oder encryption_key).",
                    },
                    "backup.encrypt_password_required",
                    "error",
                ),
            )

        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        raw_type_f = data.get("type")
        if raw_type_f is None or str(raw_type_f).strip() == "":
            raw_type = "profile"
        else:
            raw_type = str(raw_type_f).strip().lower()
        profile_in = str(data.get("profile") or data.get("backup_profile") or "").strip()

        allowed_create_types = frozenset({"profile", "full", "data", "incremental"})
        if raw_type not in allowed_create_types:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": f"Ungültiger Backup-Typ: {raw_type}"},
                    "backup.create_unknown_type",
                    "error",
                    {"allowed": sorted(allowed_create_types)},
                ),
            )

        create_warning_codes: list[str] = []
        needs_full_confirm = False
        normalized_profile = ""

        if raw_type == "incremental":
            backup_type = "incremental"
            normalized_profile, w = normalize_backup_profile(profile_in or None)
            create_warning_codes.extend(w)
        elif raw_type == "data":
            backup_type = "data"
            normalized_profile, w = normalize_backup_profile(profile_in or None)
            create_warning_codes.extend(w)
        elif raw_type == "full":
            r = resolve_profile_request(request_type="full", profile_raw=None)
            backup_type = str(r["runner_backup_type"])
            normalized_profile = str(r["normalized_profile"])
            create_warning_codes.extend(list(r.get("warning_codes") or []))
            needs_full_confirm = bool(r.get("requires_expert_confirmation"))
        else:
            r = resolve_profile_request(request_type="profile", profile_raw=profile_in or None)
            backup_type = str(r["runner_backup_type"])
            normalized_profile = str(r["normalized_profile"])
            create_warning_codes.extend(list(r.get("warning_codes") or []))
            needs_full_confirm = bool(r.get("requires_expert_confirmation"))

        run_async = bool(data.get("async", False))
        target = (data.get("target") or "local").strip()  # local | cloud_only | local_and_cloud

        backup_dir = data.get("backup_dir") or ""
        try:
            backup_dir = rt.validate_backup_dir(backup_dir)
        except Exception as ve:
            from core.backup_target_service_access import extract_backup_target_diagnosis_id

            det: dict[str, Any] = {"reason": str(ve)}
            btd = extract_backup_target_diagnosis_id(str(ve))
            if btd:
                det["diagnosis_id"] = btd
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": f"Ungültiges Backup-Ziel: {str(ve)}"},
                    "backup.path_invalid",
                    "error",
                    det,
                ),
            )

        if needs_full_confirm and not bool(data.get("confirm_full_expert")):
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "message": "Vollständiges System-Backup (Root) erfordert explizite Bestätigung.",
                        "warning_codes": create_warning_codes,
                    },
                    "backup.full_expert_confirmation_required",
                    "error",
                    {
                        "requires_confirm_full_expert": True,
                        "warning_codes": create_warning_codes,
                        "normalized_profile": normalized_profile,
                    },
                ),
            )

        active_pkg_ops = rt.detect_active_package_operations()
        if active_pkg_ops:
            rt.logger().warning(
                "backup_preflight_blocked_package_activity",
                extra={"action": "backup_preflight", "active_package_processes": active_pkg_ops[:5]},
            )
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "message": "Backup-Start blockiert: laufende Paket-/Update-Aktivität erkannt",
                    },
                    "backup.blocked_package_activity",
                    "error",
                    {
                        "diagnosis_id": "UPDATE-CONFLICT-041",
                        "active_package_processes": active_pkg_ops[:10],
                    },
                ),
            )

        runner_mode = rt.backup_runner_mode()
        backup_start_mode = rt.backup_start_mode()
        use_full_template_runner = backup_type == "full" and (
            backup_start_mode == "helper"
            or backup_start_mode == "systemd"
            or runner_mode == "systemd-template"
        )

        needs_sudo_precheck = rt.backup_create_needs_sudo_precheck(
            backup_type,
            target,
            skip_full_when_systemd_template=use_full_template_runner,
        )

        if needs_sudo_precheck and not sudo_password:
            sudo_test = rt.run_command("sudo -n true", sudo=False)
            if not sudo_test.get("success"):
                if rt.sudo_n_true_failed_due_to_nnp(sudo_test):
                    return rt.json_response(
                        status_code=200,
                        content=rt.with_backup_contract(
                            {
                                "status": "error",
                                "message": "sudo ist in diesem Dienstkontext nicht verfügbar (NoNewPrivileges). / sudo is not available in this service context (NoNewPrivileges).",
                                "requires_sudo_password": False,
                            },
                            "backup.sudo_blocked_by_nnp",
                            "error",
                            {"diagnosis_id": "SYSTEMD-NNP-031"},
                        ),
                    )
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True},
                        "backup.sudo_required",
                        "error",
                    ),
                )

        timestamp = rt.run_command("date +%Y%m%d_%H%M%S").get("stdout", "").strip()

        if needs_sudo_precheck:
            mkdir_result = rt.run_command(f"mkdir -p {shlex.quote(backup_dir)}", sudo=True, sudo_password=sudo_password, timeout=60)
            if not mkdir_result.get("success"):
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {"status": "error", "message": f"Backup-Verzeichnis konnte nicht erstellt werden: {backup_dir}"},
                        "backup.mkdir_failed",
                        "error",
                        {"path": backup_dir},
                    ),
                )
        else:
            try:
                os.makedirs(backup_dir, exist_ok=True)
            except OSError as e:
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "message": f"Backup-Verzeichnis konnte nicht erstellt oder nicht beschrieben werden: {backup_dir}",
                        },
                        "backup.mkdir_failed",
                        "error",
                        {"path": backup_dir, "reason": str(e), "diagnosis_id": "PERM-GROUP-008"},
                    ),
                )

        # precompute backup file name for UI
        bf = None
        if backup_type == "full":
            bf = f"{backup_dir}/pi-backup-full-{timestamp}.tar.gz"
        elif backup_type == "incremental":
            bf = f"{backup_dir}/pi-backup-inc-{timestamp}.tar.gz"
        elif backup_type == "data":
            bf = f"{backup_dir}/pi-backup-data-{timestamp}.tar.gz"

        last_hint = str(data.get("last_backup", "") or "")
        # cloud settings from persisted backup settings
        backup_settings = rt.read_backup_settings()
        cloud = backup_settings.get("cloud") or {}

        use_data_template_runner = backup_type == "data" and (
            backup_start_mode == "helper"
            or backup_start_mode == "systemd"
            or runner_mode == "systemd-template"
        )
        use_helper_for_start = backup_type == "data" and backup_start_mode == "helper"

        def _cloud_remote_url(local_file: str, cloud_settings: dict = None) -> Optional[str]:
            # Verwende übergebene Cloud-Einstellungen oder die aus dem äußeren Scope
            cloud_to_use = cloud_settings if cloud_settings is not None else cloud
            # Prüfe ob Cloud aktiviert ist
            if not cloud_to_use.get("enabled"):
                return None
            provider = cloud_to_use.get("provider") or "seafile_webdav"
            # Für WebDAV-basierte Provider: URL konstruieren
            if provider in ("seafile_webdav", "webdav", "nextcloud_webdav"):
                url = (cloud_to_use.get("webdav_url") or "").strip().rstrip("/")
                user = (cloud_to_use.get("username") or "").strip()
                pw = (cloud_to_use.get("password") or "").strip()
                if not url or not user or not pw:
                    return None
                remote_path = (cloud_to_use.get("remote_path") or "").strip().strip("/")
                base = f"{url}/{remote_path}" if remote_path else url
                if not base.endswith("/"):
                    base += "/"
                return f"{base}{Path(local_file).name}"
            # Für andere Provider wird die URL vom Backup-Modul generiert
            return None

        def _cloud_upload_and_verify(local_file: str, cloud_settings: dict = None, job_id: str = "") -> tuple[bool, str]:
            """Cloud-Upload mit Verifizierung. job_id für Fortschritt und 1‑Min‑Prüfung bei Timeout."""
            # Verwende übergebene Cloud-Einstellungen oder die aus dem äußeren Scope
            cloud_to_use = cloud_settings if cloud_settings is not None else cloud
            rt.logger().info(f"[Cloud-Upload] _cloud_upload_and_verify: local_file={local_file}, cloud.enabled={cloud_to_use.get('enabled')}, target={target}")
            if not cloud_to_use.get("enabled"):
                rt.logger().warning("[Cloud-Upload] Cloud-Upload ist deaktiviert (cloud.enabled=False)")
                return False, "Cloud-Upload ist deaktiviert"
            provider = cloud_to_use.get("provider") or "seafile_webdav"
            url_ok = bool((cloud_to_use.get("webdav_url") or "").strip())
            user_ok = bool((cloud_to_use.get("username") or "").strip())
            pw_ok = bool((cloud_to_use.get("password") or "").strip())
            rt.logger().info(f"[Cloud-Upload] Provider={provider}, url={url_ok}, user={user_ok}, pw={pw_ok}, file_exists={Path(local_file).exists()}")
            
            webdav_providers = ("seafile_webdav", "webdav", "nextcloud_webdav")
            if provider not in webdav_providers:
                try:
                    backup_mod = rt.get_backup_module()
                    backup_mod.rt.run_command = rt.run_command
                    ok, info = backup_mod.upload_to_cloud(local_file, provider, cloud_to_use, sudo_password)
                    if ok:
                        return True, info
                except Exception as e:
                    rt.logger().error(f"Backup-Modul Upload (non-WebDAV): {e}", exc_info=True)
                return False, f"Provider '{provider}' wird für Cloud-Upload nicht unterstützt (nur WebDAV)"
            # WebDAV: eigene Logik mit Fortschritt und 1‑Min‑Prüfung bei Timeout
            url = (cloud_to_use.get("webdav_url") or "").strip().rstrip("/")
            user = (cloud_to_use.get("username") or "").strip()
            pw = (cloud_to_use.get("password") or "").strip()
            if not url or not user or not pw:
                rt.logger().error("[Cloud-Upload] Cloud-Settings fehlen: url=%s, user=%s, pw=%s", bool(url), bool(user), bool(pw))
                return False, "Cloud-Settings fehlen (URL/User/Passwort)"
            remote = _cloud_remote_url(local_file, cloud_to_use)
            if not remote:
                rt.logger().error("[Cloud-Upload] Cloud-Ziel konnte nicht bestimmt werden; provider=%s, url_len=%s", provider, len(url))
                return False, f"Cloud-Ziel konnte nicht bestimmt werden (Provider: {provider}, URL: {url[:50]}...)"
            upload_timeout = 7200  # 2 h für große Backups / langsame Verbindungen
            # Parent-Collection (Verzeichnis) für MKCOL: null -> 409 vermeiden
            remote_path = (cloud_to_use.get("remote_path") or "").strip().strip("/")
            if remote_path:
                base = f"{url}/{remote_path}".rstrip("/") + "/"
                parts = [p for p in base.rstrip("/").replace(url.rstrip("/"), "", 1).strip("/").split("/") if p]
                mkcol_base = url.rstrip("/") + "/"
                for seg in parts:
                    mkcol_base = mkcol_base.rstrip("/") + "/" + seg + "/"
                    mc = rt.run_command(
                        f"curl -sS -o /dev/null -w '%{{http_code}}' -u {shlex.quote(user)}:{shlex.quote(pw)} -X MKCOL {shlex.quote(mkcol_base)}",
                        timeout=60,
                    )
                    code_mk = (mc.get("stdout") or "").strip()
                    try:
                        c = int(code_mk) if code_mk else None
                    except Exception:
                        c = None
                    if c in (201, 204):
                        rt.logger().info("[Cloud-Upload] MKCOL %s -> %s", mkcol_base, code_mk)
                    elif c == 405:
                        pass  # existiert bereits
                    elif c not in (200, 201, 204, 405):
                        rt.logger().warning("[Cloud-Upload] MKCOL %s -> HTTP %s (weiter mit PUT)", mkcol_base, c)
            rt.logger().info("[Cloud-Upload] WebDAV PUT → %s (timeout=%ds)", remote, upload_timeout)
            ok, put_code, err = rt.curl_put_with_progress(
                local_file, remote, user, pw, job_id, upload_timeout
            )
            if not ok:
                rt.logger().error("[Cloud-Upload] PUT fehlgeschlagen: %s", err)
                return False, err or "Upload fehlgeschlagen"
            if put_code is not None and put_code not in (200, 201, 204):
                hint = " (Datei existiert evtl. oder übergeordnetes Verzeichnis fehlt – MKCOL/Overwrite prüfen)" if put_code == 409 else ""
                rt.logger().error("[Cloud-Upload] PUT HTTP %s (erwartet 200/201/204)%s", put_code, hint)
                return False, f"Upload fehlgeschlagen (HTTP {put_code or '—'}){hint}"
            if put_code is None:
                return True, remote  # Timeout, 1‑Min‑Prüfung war erfolgreich
            # verify via PROPFIND (optional; manche Server liefern 404 für PROPFIND auf Datei)
            cmd_v = (
                "curl -sS -o /dev/null -w '%{http_code}' "
                f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
                "-X PROPFIND -H 'Depth: 0' "
                f"{shlex.quote(remote)}"
            )
            vr = rt.run_command(cmd_v, timeout=120)
            code_str = (vr.get("stdout") or "").strip()
            try:
                code = int(code_str) if code_str else None
            except Exception:
                code = None
            if vr.get("success") and code in (200, 201, 204, 207):
                rt.logger().info("[Cloud-Upload] Erfolgreich (PUT %s, PROPFIND %s): %s", put_code, code, remote)
                return True, remote
            # PROPFIND 404 ist bei einigen WebDAV-Servern normal; PUT war erfolgreich
            if put_code in (200, 201, 204):
                rt.logger().info("[Cloud-Upload] PUT ok, PROPFIND %s (ignoriert): %s", code, remote)
                return True, remote
            rt.logger().error("[Cloud-Upload] PROPFIND HTTP %s; PUT war %s", code, put_code)
            return False, f"Remote Verifizierung fehlgeschlagen (HTTP {code or '—'})"

        if use_data_template_runner:
            if rt.has_active_long_running_job():
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "message": "Es läuft bereits ein Backup- oder Klon-Auftrag.",
                        },
                        "backup.job_conflict",
                        "error",
                    ),
                )

            data_sources, skipped_optional, unreadable_required = rt.plan_data_backup_sources()
            required_sources = [str(p) for p in rt.data_required_source_candidates()]
            optional_sources = [str(p) for p in rt.data_optional_source_candidates()]
            if unreadable_required or not data_sources:
                unreadable_txt = ", ".join(str(x.get("path")) for x in unreadable_required if x.get("path"))
                results = []
                if unreadable_txt:
                    results.append(f"Pflichtquelle nicht lesbar: {unreadable_txt}")
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "message": "Datenquelle nicht lesbar",
                            "results": results,
                            "backup_file": None,
                            "timestamp": timestamp,
                        },
                        "backup.source_permission_denied",
                        "error",
                        {
                            "selected_sources": data_sources,
                            "unreadable_sources": unreadable_required,
                            "skipped_sources": skipped_optional,
                            "required_sources": required_sources,
                            "optional_sources": optional_sources,
                            "required_permission": "read_execute",
                            "diagnosis_id": "BACKUP-SOURCE-PERM-032",
                        },
                    ),
                )

            source = data_sources[0]
            job_id = rt.new_job_id()
            unit_name = f"setuphelfer-backup@{job_id}.service"
            status_dir = rt.backup_runner_status_dir()
            job_file = rt.backup_runner_job_file(job_id)
            status_file = rt.backup_runner_status_file(job_id)
            status_file.parent.mkdir(parents=True, exist_ok=True)
            job_payload = {
                "job_id": job_id,
                "backup_type": "data",
                "backup_dir": backup_dir,
                "source": source,
                "lang": str(data.get("lang") or ""),
                "requested_by": "api",
                "created_at": rt.now_iso(),
                "backup_profile": normalized_profile,
                "profile_warning_codes": create_warning_codes,
            }
            job_file.write_text(json.dumps(job_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            initial_status = {
                "job_id": job_id,
                "unit_name": unit_name,
                "unit_scope": "system",
                "status": "queued",
                "code": "backup.job.queued",
                "severity": "info",
                "diagnosis_id": None,
                "backup_started_at": rt.now_iso(),
                "backup_finished_at": None,
                "backup_type": "data",
                "backup_dir": backup_dir,
                "source": source,
                "archive_path": bf,
                "partial_path": f"{bf}.partial",
                "abort_reason": None,
                "progress_optional": None,
            }
            status_file.write_text(json.dumps(initial_status, ensure_ascii=False, indent=2), encoding="utf-8")

            rt.get_backup_jobs()[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "type": backup_type,
                "backup_dir": backup_dir,
                "backup_file": bf,
                "target": target,
                "started_at": rt.now_iso(),
                "finished_at": None,
                "message": "Wartet…",
                "code": "backup.job.queued",
                "severity": "info",
                "results": [],
                "unit_name": unit_name,
                "unit_scope": "system",
                "status_source": "systemd_runner",
            }

            if use_helper_for_start:
                ok, hcode, hraw = rt.start_backup_via_helper(job_id)
                if not ok:
                    rt.get_backup_jobs()[job_id]["status"] = "error"
                    rt.get_backup_jobs()[job_id]["message"] = "Backup-Starter fehlgeschlagen"
                    rt.get_backup_jobs()[job_id]["code"] = hcode
                    rt.get_backup_jobs()[job_id]["severity"] = "error"
                    try:
                        status_file.write_text(
                            json.dumps(
                                {
                                    **initial_status,
                                    "status": "error",
                                    "code": hcode,
                                    "severity": "error",
                                    "diagnosis_id": "SYSTEMD-RUNNER-001",
                                    "abort_reason": "starter_failed",
                                    "backup_finished_at": rt.now_iso(),
                                    "starter_response": hraw,
                                    "unit_scope": "system",
                                },
                                ensure_ascii=False,
                                indent=2,
                            ),
                            encoding="utf-8",
                        )
                    except Exception:
                        pass
                    return rt.json_response(
                        status_code=200,
                        content=rt.with_backup_contract(
                            {"status": "error", "message": "Backup-Starter fehlgeschlagen"},
                            hcode,
                            "error",
                            {"diagnosis_id": "SYSTEMD-RUNNER-001", **(hraw if isinstance(hraw, dict) else {})},
                        ),
                    )
                return rt.with_backup_contract(
                    {
                        "status": "accepted",
                        "job_id": job_id,
                        "backup_file": bf,
                        "message": "Backup gestartet",
                    },
                    "backup.job_started",
                    "success",
                    {
                        "job_id": job_id,
                        "unit_name": unit_name,
                        "runner_mode": "helper",
                        "starter_code": hcode,
                        "starter": hraw,
                        "start_mode": backup_start_mode,
                        "unit_scope": "system",
                    },
                )

            run_res = rt.systemctl_run_argv(["systemctl", "start", unit_name], timeout=60)
            if not run_res.get("success"):
                rt.get_backup_jobs()[job_id]["status"] = "error"
                rt.get_backup_jobs()[job_id]["message"] = "Backup-Runner konnte nicht gestartet werden"
                rt.get_backup_jobs()[job_id]["code"] = "backup.runner_start_failed"
                rt.get_backup_jobs()[job_id]["severity"] = "error"
                try:
                    status_file.write_text(
                        json.dumps(
                            {
                                **initial_status,
                                "status": "error",
                                "code": "backup.runner_start_failed",
                                "severity": "error",
                                "diagnosis_id": "SYSTEMD-RUNNER-001",
                                "abort_reason": "runner_start_failed",
                                "backup_finished_at": rt.now_iso(),
                                "stderr_excerpt": (run_res.get("stderr") or run_res.get("error") or "")[:300],
                                "unit_scope": "system",
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
                except Exception:
                    pass
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {"status": "error", "message": "Backup-Runner konnte nicht gestartet werden"},
                        "backup.runner_start_failed",
                        "error",
                        {"diagnosis_id": "SYSTEMD-RUNNER-001", "stderr": (run_res.get("stderr") or run_res.get("error") or "")[:300]},
                    ),
                )

            return rt.with_backup_contract(
                {
                    "status": "accepted",
                    "job_id": job_id,
                    "backup_file": bf,
                    "message": "Backup gestartet",
                },
                "backup.job_started",
                "success",
                {
                    "job_id": job_id,
                    "unit_name": unit_name,
                    "runner_mode": "systemd-template",
                    "start_mode": backup_start_mode,
                    "unit_scope": "system",
                },
            )

        elif use_full_template_runner:
            if rt.has_active_long_running_job():
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "message": "Es läuft bereits ein Backup- oder Klon-Auftrag.",
                        },
                        "backup.job_conflict",
                        "error",
                    ),
                )

            job_id = rt.new_job_id()
            unit_name = f"setuphelfer-backup@{job_id}.service"
            status_dir = rt.backup_runner_status_dir()
            job_file = rt.backup_runner_job_file(job_id)
            status_file = rt.backup_runner_status_file(job_id)
            status_file.parent.mkdir(parents=True, exist_ok=True)
            job_payload = {
                "job_id": job_id,
                "backup_type": "full",
                "backup_dir": backup_dir,
                "source": "/",
                "lang": str(data.get("lang") or ""),
                "requested_by": "api",
                "created_at": rt.now_iso(),
                "backup_profile": normalized_profile,
                "profile_warning_codes": create_warning_codes,
            }
            job_file.write_text(json.dumps(job_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            initial_status = {
                "job_id": job_id,
                "unit_name": unit_name,
                "unit_scope": "system",
                "status": "queued",
                "code": "backup.job.queued",
                "severity": "info",
                "diagnosis_id": None,
                "backup_started_at": rt.now_iso(),
                "backup_finished_at": None,
                "backup_type": "full",
                "backup_dir": backup_dir,
                "source": "/",
                "archive_path": bf,
                "partial_path": f"{bf}.partial",
                "abort_reason": None,
                "progress_optional": None,
            }
            status_file.write_text(json.dumps(initial_status, ensure_ascii=False, indent=2), encoding="utf-8")

            rt.get_backup_jobs()[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "type": backup_type,
                "backup_dir": backup_dir,
                "backup_file": bf,
                "target": target,
                "started_at": rt.now_iso(),
                "finished_at": None,
                "message": "Wartet…",
                "code": "backup.job.queued",
                "severity": "info",
                "results": [],
                "unit_name": unit_name,
                "unit_scope": "system",
                "status_source": "systemd_runner",
            }

            if backup_start_mode == "helper":
                ok, hcode, hraw = rt.start_backup_via_helper(job_id)
                if not ok:
                    rt.get_backup_jobs()[job_id]["status"] = "error"
                    rt.get_backup_jobs()[job_id]["message"] = "Backup-Starter fehlgeschlagen"
                    rt.get_backup_jobs()[job_id]["code"] = hcode
                    rt.get_backup_jobs()[job_id]["severity"] = "error"
                    try:
                        status_file.write_text(
                            json.dumps(
                                {
                                    **initial_status,
                                    "status": "error",
                                    "code": hcode,
                                    "severity": "error",
                                    "diagnosis_id": "SYSTEMD-RUNNER-001",
                                    "abort_reason": "starter_failed",
                                    "backup_finished_at": rt.now_iso(),
                                    "starter_response": hraw,
                                    "unit_scope": "system",
                                },
                                ensure_ascii=False,
                                indent=2,
                            ),
                            encoding="utf-8",
                        )
                    except Exception:
                        pass
                    return rt.json_response(
                        status_code=200,
                        content=rt.with_backup_contract(
                            {"status": "error", "message": "Backup-Starter fehlgeschlagen"},
                            hcode,
                            "error",
                            {"diagnosis_id": "SYSTEMD-RUNNER-001", **(hraw if isinstance(hraw, dict) else {})},
                        ),
                    )
                return rt.with_backup_contract(
                    {
                        "status": "accepted",
                        "job_id": job_id,
                        "backup_file": bf,
                        "message": "Backup gestartet",
                    },
                    "backup.job_started",
                    "success",
                    {
                        "job_id": job_id,
                        "unit_name": unit_name,
                        "runner_mode": "helper",
                        "starter_code": hcode,
                        "starter": hraw,
                        "start_mode": backup_start_mode,
                        "unit_scope": "system",
                    },
                )

            run_res = rt.systemctl_run_argv(["systemctl", "start", unit_name], timeout=60)
            if not run_res.get("success"):
                rt.get_backup_jobs()[job_id]["status"] = "error"
                rt.get_backup_jobs()[job_id]["message"] = "Backup-Runner konnte nicht gestartet werden"
                rt.get_backup_jobs()[job_id]["code"] = "backup.runner_start_failed"
                rt.get_backup_jobs()[job_id]["severity"] = "error"
                try:
                    status_file.write_text(
                        json.dumps(
                            {
                                **initial_status,
                                "status": "error",
                                "code": "backup.runner_start_failed",
                                "severity": "error",
                                "diagnosis_id": "SYSTEMD-RUNNER-001",
                                "abort_reason": "runner_start_failed",
                                "backup_finished_at": rt.now_iso(),
                                "stderr_excerpt": (run_res.get("stderr") or run_res.get("error") or "")[:300],
                                "unit_scope": "system",
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
                except Exception:
                    pass
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {"status": "error", "message": "Backup-Runner konnte nicht gestartet werden"},
                        "backup.runner_start_failed",
                        "error",
                        {"diagnosis_id": "SYSTEMD-RUNNER-001", "stderr": (run_res.get("stderr") or run_res.get("error") or "")[:300]},
                    ),
                )

            return rt.with_backup_contract(
                {
                    "status": "accepted",
                    "job_id": job_id,
                    "backup_file": bf,
                    "message": "Backup gestartet",
                },
                "backup.job_started",
                "success",
                {
                    "job_id": job_id,
                    "unit_name": unit_name,
                    "runner_mode": "systemd-template",
                    "start_mode": backup_start_mode,
                    "unit_scope": "system",
                },
            )

        if run_async:
            if rt.has_active_long_running_job():
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "message": "Es läuft bereits ein Backup- oder Klon-Auftrag.",
                        },
                        "backup.job_conflict",
                        "error",
                    ),
                )
            job_id = rt.new_job_id()
            rt.get_backup_jobs()[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "type": backup_type,
                "backup_dir": backup_dir,
                "backup_file": bf,
                "target": target,
                "started_at": rt.now_iso(),
                "finished_at": None,
                "message": "Wartet…",
                "code": "backup.job.queued",
                "severity": "info",
                "results": [],
            }

            def _runner_thread():
                try:
                    cancel_ev = rt.get_backup_job_cancel().get(job_id)
                    if not cancel_ev:
                        cancel_ev = threading.Event()
                        rt.get_backup_job_cancel()[job_id] = cancel_ev
                    rt.get_backup_jobs()[job_id]["status"] = "running"
                    rt.get_backup_jobs()[job_id]["message"] = "Backup läuft…"
                    rt.get_backup_jobs()[job_id]["code"] = "backup.job.running"
                    rt.get_backup_jobs()[job_id]["severity"] = "info"
                    result = rt.do_backup_logic(
                        sudo_password=sudo_password,
                        backup_type=backup_type,
                        backup_dir=backup_dir,
                        timestamp=timestamp,
                        target=target,
                        last_backup_hint=last_hint,
                        cancel_event=cancel_ev,
                        job=rt.get_backup_jobs()[job_id],
                    )
                    rt.get_backup_jobs()[job_id]["results"] = result.get("results") or []
                    if isinstance(result.get("code"), str):
                        rt.get_backup_jobs()[job_id]["code"] = result.get("code")
                    if isinstance(result.get("severity"), str):
                        rt.get_backup_jobs()[job_id]["severity"] = result.get("severity")
                    backup_file_path = result.get("backup_file") or bf
                    
                    # Optional: Verschlüsselung
                    encryption_method = data.get("encryption_method")
                    encryption_key = data.get("encryption_key")
                    if encryption_method and backup_file_path and result.get("status") == "success":
                        try:
                            backup_mod = rt.get_backup_module()
                            backup_mod.rt.run_command = rt.run_command
                            rt.get_backup_jobs()[job_id]["message"] = "Verschlüsselung läuft…"
                            rt.get_backup_jobs()[job_id]["code"] = "backup.job.encrypting"
                            rt.get_backup_jobs()[job_id]["severity"] = "info"
                            enc_success, enc_file, enc_error = backup_mod.encrypt_backup(
                                backup_file_path,
                                encryption_key,
                                encryption_method,
                                sudo_password
                            )
                            if enc_success:
                                backup_file_path = enc_file
                                rt.get_backup_jobs()[job_id]["backup_file"] = enc_file
                                rt.get_backup_jobs()[job_id]["encrypted"] = True
                                rt.get_backup_jobs()[job_id]["results"].append(f"verschlüsselt: {enc_file}")
                                rt.logger().info(f"Backup verschlüsselt: {enc_file}")
                            elif encrypt_requested:
                                try:
                                    if backup_file_path and Path(backup_file_path).exists():
                                        Path(backup_file_path).unlink()
                                except OSError:
                                    pass
                                rt.get_backup_jobs()[job_id]["status"] = "error"
                                rt.get_backup_jobs()[job_id]["backup_file"] = None
                                rt.get_backup_jobs()[job_id]["message"] = f"Verschlüsselung fehlgeschlagen: {enc_error or 'Unbekannter Fehler'}"
                                rt.get_backup_jobs()[job_id]["code"] = "backup.encrypt_failed"
                                rt.get_backup_jobs()[job_id]["severity"] = "error"
                                rt.get_backup_jobs()[job_id]["results"].append(f"Verschlüsselung fehlgeschlagen: {enc_error}")
                            else:
                                rt.get_backup_jobs()[job_id]["results"].append(f"Verschlüsselung fehlgeschlagen: {enc_error}")
                                rt.get_backup_jobs()[job_id]["warning"] = f"Verschlüsselung fehlgeschlagen: {enc_error}"
                        except Exception as e:
                            if encrypt_requested:
                                try:
                                    if backup_file_path and Path(backup_file_path).exists():
                                        Path(backup_file_path).unlink()
                                except OSError:
                                    pass
                                rt.get_backup_jobs()[job_id]["status"] = "error"
                                rt.get_backup_jobs()[job_id]["backup_file"] = None
                                rt.get_backup_jobs()[job_id]["message"] = f"Verschlüsselung fehlgeschlagen: {str(e)}"
                                rt.get_backup_jobs()[job_id]["code"] = "backup.encrypt_failed"
                                rt.get_backup_jobs()[job_id]["severity"] = "error"
                                rt.get_backup_jobs()[job_id]["results"].append(f"Verschlüsselung Fehler: {str(e)}")
                            else:
                                rt.get_backup_jobs()[job_id]["results"].append(f"Verschlüsselung Fehler: {str(e)}")
                                rt.get_backup_jobs()[job_id]["warning"] = f"Verschlüsselung Fehler: {str(e)}"
                    else:
                        rt.get_backup_jobs()[job_id]["backup_file"] = backup_file_path

                    if result.get("status") == "success" and rt.get_backup_jobs()[job_id].get("code") == "backup.job.encrypting":
                        rt.get_backup_jobs()[job_id]["code"] = str(result.get("code") or "backup.success")
                        rt.get_backup_jobs()[job_id]["severity"] = str(result.get("severity") or "success")
                    
                    # optional cloud upload nur wenn explizit gewünscht (cloud_only oder local_and_cloud)
                    # Bei target="local" (z.B. USB-Stick) NIEMALS in die Cloud hochladen
                    backup_settings_thread = rt.read_backup_settings()
                    cloud_thread = backup_settings_thread.get("cloud") or {}
                    cloud_should_upload = target in ("cloud_only", "local_and_cloud")
                    rt.logger().info(f"Cloud-Upload-Prüfung: target={target}, cloud.enabled={cloud_thread.get('enabled')}, cloud_should_upload={cloud_should_upload}, backup_file={rt.get_backup_jobs()[job_id].get('backup_file')}")
                    if result.get("status") == "success" and cloud_should_upload:
                        # Verwende Cloud-Einstellungen aus Thread
                        cloud = cloud_thread
                        backup_file_to_upload = rt.get_backup_jobs()[job_id]["backup_file"]
                        rt.logger().info(f"Cloud-Upload gestartet für {backup_file_to_upload}, Provider: {cloud.get('provider')}, Enabled: {cloud.get('enabled')}, Target: {target}")
                        
                        # Prüfe Cloud-Credentials VOR dem Upload
                        provider = cloud.get("provider") or "seafile_webdav"
                        webdav_providers = ("seafile_webdav", "webdav", "nextcloud_webdav")
                        credentials_ok = False
                        if provider in webdav_providers:
                            url_ok = bool((cloud.get("webdav_url") or "").strip())
                            user_ok = bool((cloud.get("username") or "").strip())
                            pw_ok = bool((cloud.get("password") or "").strip())
                            credentials_ok = url_ok and user_ok and pw_ok
                        else:
                            # Für andere Provider: Prüfe Provider-spezifische Settings
                            if provider in ("s3", "s3_compatible"):
                                credentials_ok = bool(cloud.get("bucket") and cloud.get("access_key_id") and cloud.get("secret_access_key"))
                            elif provider == "google_cloud":
                                credentials_ok = bool(cloud.get("bucket"))
                            elif provider == "azure":
                                credentials_ok = bool(cloud.get("account_name") and cloud.get("container") and cloud.get("account_key"))
                            else:
                                credentials_ok = False
                        
                        if not credentials_ok:
                            error_msg = f"Cloud-Credentials fehlen für Provider '{provider}'. Backup wurde nur lokal gespeichert."
                            rt.get_backup_jobs()[job_id]["results"].append(f"⚠️ Cloud-Upload übersprungen: {error_msg}")
                            rt.get_backup_jobs()[job_id]["warning"] = error_msg
                            rt.logger().warning(f"[Cloud-Upload] {error_msg}")
                            # Bei cloud_only ist das ein Fehler, bei local_and_cloud nur eine Warnung
                            if target == "cloud_only":
                                rt.get_backup_jobs()[job_id]["status"] = "error"
                                rt.get_backup_jobs()[job_id]["message"] = "Cloud-Upload fehlgeschlagen: Credentials fehlen"
                                rt.get_backup_jobs()[job_id]["code"] = "backup.cloud_credentials_missing"
                                rt.get_backup_jobs()[job_id]["severity"] = "error"
                            else:
                                # Backup lokal erfolgreich, Cloud-Upload fehlgeschlagen
                                rt.get_backup_jobs()[job_id]["status"] = "success"
                                rt.get_backup_jobs()[job_id]["message"] = "Backup lokal erfolgreich (Cloud-Upload übersprungen)"
                                rt.get_backup_jobs()[job_id]["code"] = "backup.cloud_upload_skipped"
                                rt.get_backup_jobs()[job_id]["severity"] = "warning"
                        # Prüfe ob Datei existiert
                        elif not Path(backup_file_to_upload).exists():
                            error_msg = f"Backup-Datei nicht gefunden: {backup_file_to_upload}"
                            rt.get_backup_jobs()[job_id]["results"].append(f"upload failed: {error_msg}")
                            rt.get_backup_jobs()[job_id]["warning"] = f"Cloud-Upload fehlgeschlagen: {error_msg}"
                            if target == "cloud_only":
                                rt.get_backup_jobs()[job_id]["status"] = "error"
                                rt.get_backup_jobs()[job_id]["code"] = "backup.cloud_upload_file_missing"
                                rt.get_backup_jobs()[job_id]["severity"] = "error"
                            else:
                                rt.get_backup_jobs()[job_id]["status"] = "success"
                                rt.get_backup_jobs()[job_id]["message"] = "Backup lokal erfolgreich (Cloud-Upload fehlgeschlagen)"
                                rt.get_backup_jobs()[job_id]["code"] = "backup.partial_success"
                                rt.get_backup_jobs()[job_id]["severity"] = "warning"
                            rt.logger().error(error_msg)
                        else:
                            rt.get_backup_jobs()[job_id]["message"] = "Upload läuft…"
                            rt.get_backup_jobs()[job_id]["code"] = "backup.job.uploading"
                            rt.get_backup_jobs()[job_id]["severity"] = "info"
                            try:
                                ok, info = _cloud_upload_and_verify(backup_file_to_upload, cloud, job_id)
                                rt.logger().info(f"Cloud-Upload Ergebnis: ok={ok}, info={info}")
                                if ok:
                                    rt.get_backup_jobs()[job_id].pop("upload_progress_pct", None)
                                    rt.get_backup_jobs()[job_id]["remote_file"] = info
                                    rt.get_backup_jobs()[job_id]["results"].append(f"✅ uploaded: {info}")
                                    rt.get_backup_jobs()[job_id]["location"] = "Cloud"
                                    rt.get_backup_jobs()[job_id]["message"] = "Backup erfolgreich hochgeladen"
                                    rt.get_backup_jobs()[job_id]["code"] = "backup.cloud_upload_ok"
                                    rt.get_backup_jobs()[job_id]["severity"] = "success"
                                    if target == "cloud_only":
                                        try:
                                            rt.run_command(f"rm -f {shlex.quote(backup_file_to_upload)}", sudo=True, sudo_password=sudo_password)
                                            rt.get_backup_jobs()[job_id]["results"].append("Lokale Datei gelöscht (cloud_only)")
                                        except Exception as e:
                                            rt.logger().warning(f"Lokale Datei konnte nicht gelöscht werden: {e}")
                                else:
                                    rt.get_backup_jobs()[job_id].pop("upload_progress_pct", None)
                                    rt.get_backup_jobs()[job_id]["results"].append(f"❌ upload failed: {info}")
                                    rt.get_backup_jobs()[job_id]["warning"] = f"Cloud-Upload fehlgeschlagen: {info}"
                                    if target == "cloud_only":
                                        rt.get_backup_jobs()[job_id]["status"] = "error"
                                        rt.get_backup_jobs()[job_id]["message"] = "Cloud-Upload fehlgeschlagen"
                                        rt.get_backup_jobs()[job_id]["code"] = "backup.cloud_upload_failed"
                                        rt.get_backup_jobs()[job_id]["severity"] = "error"
                                    else:
                                        rt.get_backup_jobs()[job_id]["status"] = "success"
                                        rt.get_backup_jobs()[job_id]["message"] = "Backup lokal erfolgreich (Cloud-Upload fehlgeschlagen)"
                                        rt.get_backup_jobs()[job_id]["code"] = "backup.partial_success"
                                        rt.get_backup_jobs()[job_id]["severity"] = "warning"
                                    rt.logger().error(f"Cloud-Upload fehlgeschlagen: {info}")
                            except Exception as e:
                                error_msg = f"Cloud-Upload Fehler: {str(e)}"
                                rt.logger().error(f"[Cloud-Upload] Unerwarteter Fehler: {e}", exc_info=True)
                                rt.get_backup_jobs()[job_id]["results"].append(f"❌ upload exception: {error_msg}")
                                rt.get_backup_jobs()[job_id]["warning"] = error_msg
                                if target == "cloud_only":
                                    rt.get_backup_jobs()[job_id]["status"] = "error"
                                    rt.get_backup_jobs()[job_id]["message"] = "Cloud-Upload fehlgeschlagen"
                                    rt.get_backup_jobs()[job_id]["code"] = "backup.cloud_upload_failed"
                                    rt.get_backup_jobs()[job_id]["severity"] = "error"
                                else:
                                    rt.get_backup_jobs()[job_id]["status"] = "success"
                                    rt.get_backup_jobs()[job_id]["message"] = "Backup lokal erfolgreich (Cloud-Upload fehlgeschlagen)"
                                    rt.get_backup_jobs()[job_id]["code"] = "backup.partial_success"
                                    rt.get_backup_jobs()[job_id]["severity"] = "warning"
                    rt.get_backup_jobs()[job_id]["finished_at"] = rt.now_iso()
                    # Status wird bereits oben gesetzt, nur noch finalisieren
                    if rt.get_backup_jobs()[job_id]["status"] not in ("error", "cancelled"):
                        if result.get("status") == "cancelled":
                            rt.get_backup_jobs()[job_id]["status"] = "cancelled"
                            rt.get_backup_jobs()[job_id]["message"] = "Abgebrochen"
                            rt.get_backup_jobs()[job_id]["code"] = "backup.cancelled"
                            rt.get_backup_jobs()[job_id]["severity"] = "info"
                        elif result.get("status") == "success":
                            # Status bleibt success (auch wenn Upload fehlgeschlagen ist, außer bei cloud_only)
                            if rt.get_backup_jobs()[job_id]["status"] != "error":
                                rt.get_backup_jobs()[job_id]["status"] = "success"
                                rt.get_backup_jobs()[job_id]["message"] = "Fertig"
                                if rt.get_backup_jobs()[job_id].get("code") not in (
                                    "backup.cloud_upload_ok",
                                    "backup.cloud_upload_skipped",
                                    "backup.cloud_upload_failed",
                                    "backup.partial_success",
                                    "backup.cloud_upload_file_missing",
                                    "backup.cloud_credentials_missing",
                                ):
                                    rt.get_backup_jobs()[job_id]["code"] = "backup.success"
                                    rt.get_backup_jobs()[job_id]["severity"] = (
                                        "warning" if result.get("warning") or rt.get_backup_jobs()[job_id].get("warning") else "success"
                                    )
                            if result.get("warning"):
                                rt.get_backup_jobs()[job_id]["warning"] = result.get("warning")
                        else:
                            rt.get_backup_jobs()[job_id]["status"] = "error"
                            rt.get_backup_jobs()[job_id]["message"] = result.get("message") or "Fehler"
                            if isinstance(result.get("code"), str):
                                rt.get_backup_jobs()[job_id]["code"] = result.get("code")
                                rt.get_backup_jobs()[job_id]["severity"] = result.get("severity") or "error"
                            else:
                                rt.get_backup_jobs()[job_id]["code"] = "backup.error"
                                rt.get_backup_jobs()[job_id]["severity"] = "error"
                except Exception as e:
                    rt.get_backup_jobs()[job_id]["status"] = "error"
                    rt.get_backup_jobs()[job_id]["message"] = str(e)
                    rt.get_backup_jobs()[job_id]["code"] = "backup.error"
                    rt.get_backup_jobs()[job_id]["severity"] = "error"
                    rt.get_backup_jobs()[job_id]["finished_at"] = rt.now_iso()
                finally:
                    # cleanup cancel event
                    try:
                        rt.get_backup_job_cancel().pop(job_id, None)
                    except Exception:
                        pass

            threading.Thread(target=_runner_thread, daemon=True).start()
            return rt.with_backup_contract(
                {"status": "accepted", "job_id": job_id, "backup_file": bf, "message": "Backup gestartet"},
                "backup.job_started",
                "success",
                {"job_id": job_id},
            )

        # sync mode
        result = await asyncio.to_thread(
            rt.do_backup_logic,
            sudo_password=sudo_password,
            backup_type=backup_type,
            backup_dir=backup_dir,
            timestamp=timestamp,
            target=target,
            last_backup_hint=last_hint,
        )
        
        # Optional: Verschlüsselung
        encryption_method = data.get("encryption_method")
        encryption_key = data.get("encryption_key")
        backup_file_path = result.get("backup_file") or bf
        if encryption_method and backup_file_path and result.get("status") == "success":
            try:
                backup_mod = rt.get_backup_module()
                backup_mod.rt.run_command = rt.run_command
                enc_success, enc_file, enc_error = backup_mod.encrypt_backup(
                    backup_file_path,
                    encryption_key,
                    encryption_method,
                    sudo_password
                )
                if enc_success:
                    backup_file_path = enc_file
                    result["backup_file"] = enc_file
                    result["results"] = (result.get("results") or []) + [f"verschlüsselt: {enc_file}"]
                    result["encrypted"] = True
                elif encrypt_requested:
                    try:
                        if backup_file_path and Path(backup_file_path).exists():
                            Path(backup_file_path).unlink()
                    except OSError:
                        pass
                    result = {
                        "status": "error",
                        "message": f"Verschlüsselung fehlgeschlagen: {enc_error or 'Unbekannter Fehler'}",
                        "results": result.get("results") or [],
                        "backup_file": None,
                        "timestamp": timestamp,
                    }
                    result = rt.with_backup_contract(
                        result,
                        "backup.encrypt_failed",
                        "error",
                        {"reason": (enc_error or "")[:300]},
                    )
                else:
                    result["warning"] = (result.get("warning") or "") + f" Verschlüsselung fehlgeschlagen: {enc_error}"
            except Exception as e:
                if encrypt_requested:
                    try:
                        if backup_file_path and Path(backup_file_path).exists():
                            Path(backup_file_path).unlink()
                    except OSError:
                        pass
                    result = {
                        "status": "error",
                        "message": f"Verschlüsselung fehlgeschlagen: {str(e)}",
                        "results": result.get("results") or [],
                        "backup_file": None,
                        "timestamp": timestamp,
                    }
                    result = rt.with_backup_contract(
                        result,
                        "backup.encrypt_failed",
                        "error",
                        {"reason": str(e)[:300]},
                    )
                else:
                    result["warning"] = (result.get("warning") or "") + f" Verschlüsselung Fehler: {str(e)}"
        
        # Cloud-Upload nur bei explizitem Cloud-Ziel; bei target="local" (z.B. USB) nie hochladen
        cloud_should_upload = target in ("cloud_only", "local_and_cloud")
        if result.get("status") == "success" and cloud_should_upload:
            ok, info = _cloud_upload_and_verify(result.get("backup_file") or bf)
            if ok:
                result["remote_file"] = info
                if target == "cloud_only":
                    try:
                        rt.run_command(f"rm -f {shlex.quote(str(result.get('backup_file') or bf))}", sudo=True, sudo_password=sudo_password)
                    except Exception:
                        pass
            else:
                result["warning"] = f"Upload fehlgeschlagen: {info}"
                detail = {"cloud_error": str(info)[:500]}
                if target == "cloud_only":
                    result = rt.with_backup_contract(result, "backup.cloud_upload_failed", "error", detail)
                else:
                    result = rt.with_backup_contract(result, "backup.partial_success", "warning", detail)
        if isinstance(result, dict) and "code" not in result:
            sev = "success"
            if result.get("status") == "error":
                sev = "error"
            elif result.get("status") == "cancelled":
                sev = "info"
            cd = (
                "backup.success"
                if result.get("status") == "success"
                else ("backup.cancelled" if result.get("status") == "cancelled" else "backup.error")
            )
            result = rt.with_backup_contract(result, cd, sev)
        return result
    except Exception as e:
        rt.logger().error(f"💥 Fehler bei Backup-Erstellung: {str(e)}", exc_info=True)
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": f"Fehler bei der Backup-Erstellung: {str(e)}"},
                "backup.error",
                "error",
                {"detail": str(e)},
            ),
        )


async def verify_backup(request: Request):
    """Verifiziert ein Backup-Archiv. Unterstützt Basis- und Tiefenprüfung (für verschlüsselte Backups)."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    backup_file = (data.get("backup_file") or data.get("file") or "").strip()
    mode = (data.get("mode") or "basic").strip().lower()
    encryption_key = data.get("encryption_key") or data.get("password") or None

    if mode not in ("basic", "deep"):
        mode = "basic"

    if not backup_file:
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {
                    "status": "error",
                    "api_status": "error",
                    "message": "backup_file erforderlich",
                    "data": {},
                },
                "backup.verify_missing_file",
                "error",
            ),
        )

    # Sicherheitsprüfung: Pfad-Validierung (realpath + Allowlist)
    try:
        bf = rt.normalize_path(backup_file)
        if not rt.is_under_allowed_root(bf):
            rt.logger().warning("Backup-Verify blockiert: Pfad außerhalb erlaubter Wurzeln", extra={"action": "backup_verify", "path": str(bf)})
            rt.merge_backup_realtest_state(
                last_verify_ok=False,
                last_verify_path=str(bf),
                last_failure_kind="verify_path_disallowed",
                last_failure_message="Pfad außerhalb Allowlist",
            )
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "api_status": "error",
                        "message": "Backup-Datei liegt außerhalb erlaubter Pfade",
                        "data": {"results": {"valid": False, "file": str(bf), "error": "Pfad außerhalb Allowlist"}},
                    },
                    "backup.permission_denied",
                    "error",
                    {"file": str(bf)},
                ),
            )
    except Exception as e:
        rt.logger().warning("Backup-Verify blockiert: ungültiger Pfad", extra={"action": "backup_verify", "error": str(e)})
        rt.merge_backup_realtest_state(
            last_verify_ok=False,
            last_failure_kind="verify_path_invalid",
            last_failure_message=str(e)[:300],
        )
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {
                    "status": "error",
                    "api_status": "error",
                    "message": f"Ungültiger Pfad: {str(e)}",
                    "data": {"results": {"valid": False, "file": backup_file, "error": str(e)[:300]}},
                },
                "backup.path_invalid",
                "error",
                {"reason": str(e)},
            ),
        )

    if not bf.exists():
        rt.merge_backup_realtest_state(
            last_verify_ok=False,
            last_verify_path=str(bf),
            last_failure_kind="verify_not_found",
            last_failure_message="Datei existiert nicht",
        )
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {
                    "status": "error",
                    "api_status": "error",
                    "message": "Backup-Datei existiert nicht",
                    "data": {"results": {"valid": False, "file": str(bf), "error": "Datei existiert nicht"}},
                },
                "backup.backup_not_found",
                "error",
                {"file": str(bf)},
            ),
        )

    if str(bf).endswith(".partial"):
        rt.merge_backup_realtest_state(
            last_verify_ok=False,
            last_verify_path=str(bf),
            last_failure_kind="verify_partial_blocked",
            last_failure_message="Partial-Archiv ist kein gültiges Backup",
        )
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {
                    "status": "error",
                    "api_status": "error",
                    "message": "Partial-Archive dürfen nicht verifiziert werden",
                    "data": {"results": {"valid": False, "file": str(bf), "error": "partial_archive_not_allowed"}},
                },
                "backup.verify_partial_not_allowed",
                "error",
                {"file": str(bf), "diagnosis_id": "BACKUP-ARCHIVE-003"},
            ),
        )

    # Prüfe, ob verschlüsselt
    is_encrypted = backup_file.endswith('.gpg') or backup_file.endswith('.enc') or '.tar.gz.gpg' in backup_file or '.tar.gz.enc' in backup_file

    # Unverschlüsseltes .tar.gz: Archiv-Einträge prüfen (Traversal, Symlinks, Sonderdateien)
    plain_tar_gz = str(bf).endswith(".tar.gz") and not is_encrypted
    plain_arch_analysis: Optional[dict] = None
    if plain_tar_gz:
        try:
            arch_analysis = rt.analyze_tar_members(str(bf))
        except Exception as e:
            rt.merge_backup_realtest_state(
                last_verify_ok=False,
                last_verify_path=str(bf),
                last_failure_kind="verify_archive_read",
                last_failure_message=str(e)[:300],
            )
            rt.logger().warning("Backup-Verify: Archiv nicht lesbar", extra={"action": "backup_verify", "path": str(bf), "error": str(e)[:200]})
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "api_status": "error",
                        "message": f"Backup-Archiv konnte nicht gelesen werden (beschädigt oder kein gültiges tar.gz): {str(e)[:200]}",
                        "data": {
                            "results": {
                                "valid": False,
                                "file": str(bf),
                                "error": str(e)[:300],
                                "verification_mode": mode,
                            }
                        },
                    },
                    "backup.verify_archive_unreadable",
                    "error",
                    {"reason": str(e)[:200], "diagnosis_id": "BACKUP-ARCHIVE-002"},
                ),
            )
        if arch_analysis.get("blocked_entries"):
            rt.merge_backup_realtest_state(
                last_verify_ok=False,
                last_verify_path=str(bf),
                last_failure_kind="verify_blocked_entries",
                last_failure_message="Archiv enthält gesperrte Einträge",
                open_critical_risks=["verify_blocked_archive"],
                last_verify_shallow_ok=False,
            )
            rt.logger().warning(
                "Backup-Verify: gesperrte Archiv-Einträge",
                extra={"action": "backup_verify", "path": str(bf), "blocked": arch_analysis.get("blocked_entries")},
            )
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "api_status": "error",
                        "message": "Backup-Archiv enthält gesperrte Einträge (Traversal, absolute Pfade oder nicht unterstützte Sonderdateien wie Geräte/FIFOs).",
                        "data": {"results": {"valid": False, "blocked_entries": arch_analysis.get("blocked_entries"), "analysis": arch_analysis}},
                        "results": {
                            "file": str(bf),
                            "exists": True,
                            "encrypted": False,
                            "valid": False,
                            "blocked_entries": arch_analysis.get("blocked_entries"),
                            "analysis": arch_analysis,
                            "error": "Gesperrte Archiv-Einträge",
                            "verification_mode": mode,
                        },
                    },
                    "backup.verify_blocked_entries",
                    "error",
                    {"diagnosis_id": "RESTORE-PATH-004"},
                ),
            )
        plain_arch_analysis = arch_analysis

        if mode == "deep":
            from core.backup_recovery_i18n import (
                K_ARCHIVE_CORRUPT,
                K_EXTRACT_FAILED,
                K_MISSING_MANIFEST,
                K_VERIFY_INTEGRITY_FAILED,
            )
            from modules.backup_verify import verify_deep

            vd_ok, vd_key, vd_details = verify_deep(
                str(bf),
                verify_checksums=True,
                strict_archive_manifest=False,
                try_loop_mount_image=False,
                runner=None,
            )
            if not vd_ok:
                details_err: dict = vd_details or {}
                errs = details_err.get("errors") or []
                err_msg = ""
                if details_err.get("gzip_error"):
                    err_msg = str(details_err.get("gzip_error"))[:300]
                elif errs:
                    err_msg = str((errs[0] or {}).get("detail") or (errs[0] or {}).get("kind") or "")[:300]
                else:
                    err_msg = str(details_err.get("error") or vd_key or "")[:300]
                diag_id: Optional[str] = None
                api_code = "backup.verify_failed"
                if vd_key == K_MISSING_MANIFEST:
                    api_code = "backup.failed_manifest_missing"
                    diag_id = "BACKUP-MANIFEST-001"
                elif vd_key == K_VERIFY_INTEGRITY_FAILED:
                    api_code = "backup.verify_integrity_failed"
                    if any(
                        isinstance(x, dict)
                        and x.get("kind") in ("hash_mismatch", "manifest_metadata_mismatch")
                        for x in errs
                    ):
                        api_code = "backup.failed_integrity_mismatch"
                    if any(isinstance(x, dict) and x.get("kind") == "hash_mismatch" for x in errs):
                        diag_id = "BACKUP-HASH-003"
                    else:
                        diag_id = "BACKUP-ARCHIVE-002"
                elif vd_key == K_ARCHIVE_CORRUPT:
                    api_code = "backup.verify_archive_unreadable"
                    diag_id = "BACKUP-ARCHIVE-002"
                elif vd_key == K_EXTRACT_FAILED:
                    api_code = "backup.verify_archive_unreadable"
                    diag_id = "BACKUP-ARCHIVE-002"

                rt.merge_backup_realtest_state(
                    last_verify_ok=False,
                    last_verify_path=str(bf),
                    last_failure_kind="verify_deep_integrity",
                    last_failure_message=err_msg[:300],
                )
                msg = tr(vd_key) if vd_key else "Tiefenprüfung fehlgeschlagen"
                res_payload = {
                    "status": "error",
                    "api_status": "error",
                    "message": msg,
                    "data": {
                        "results": {
                            "valid": False,
                            "file": str(bf),
                            "exists": True,
                            "encrypted": False,
                            "error": err_msg,
                            "verification_mode": mode,
                            "verify_details": details_err,
                        }
                    },
                    "results": {
                        "file": str(bf),
                        "exists": True,
                        "encrypted": False,
                        "valid": False,
                        "error": err_msg,
                        "verification_mode": mode,
                        "verify_details": details_err,
                    },
                }
                det_kw = {"diagnosis_id": diag_id, "verify_key": vd_key} if diag_id else {"verify_key": vd_key}
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(res_payload, api_code, "error", det_kw),
                )

    results = {
        "file": backup_file,
        "exists": True,
        "encrypted": is_encrypted,
        "valid": False,
        "size_bytes": 0,
        "size_human": "",
        "file_count": 0,
        "sample_files": [],
        "error": None,
        "verification_mode": mode,
    }

    try:
        st = Path(backup_file).stat()
        results["size_bytes"] = st.st_size

        def human(n: int) -> str:
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if n < 1024:
                    return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
                n /= 1024
            return f"{n:.1f} TB"

        results["size_human"] = human(st.st_size)
    except Exception as e:
        results["error"] = f"Fehler beim Lesen der Dateigröße: {str(e)}"
        # Logging gemäß Audit-Regeln – keine Credentials
        rt.logger().error("Backup-Verify fehlgeschlagen (Dateigröße)", extra={"action": "backup_verify", "path": backup_file, "error": str(e)})
        rt.merge_backup_realtest_state(
            last_verify_ok=False,
            last_verify_path=str(bf),
            last_failure_kind="verify_stat_error",
            last_failure_message=str(e)[:300],
        )
        return rt.with_backup_contract(
            {
                "status": "success",
                "api_status": "error",
                "message": "Fehler beim Lesen der Dateigröße",
                "data": {"results": results},
                "results": results,
            },
            "backup.verify_stat_error",
            "error",
        )

    # Basisprüfung für verschlüsselte Backups (ohne Schlüssel)
    if is_encrypted and mode == "basic":
        results["valid"] = results["size_bytes"] > 0
        if results["valid"]:
            results["error"] = "Nur Basisprüfung: Datei existiert und ist > 0 Bytes, Inhalt wurde nicht entschlüsselt."
            api_status = "ok"
            msg = "Backup oberflächlich geprüft (verschlüsselt, nur Größen-Check)."
            rt.merge_backup_realtest_state(
                last_verify_ok=False,
                last_verify_shallow_ok=True,
                last_verify_path=str(bf),
                last_failure_kind="verify_shallow_only",
                last_failure_message="Verschlüsselt: nur Größen-Check, kein Archiv-Inhalt geprüft",
            )
        else:
            results["error"] = "Verschlüsselte Backup-Datei ist leer oder nicht gefunden"
            api_status = "error"
            msg = "Verschlüsseltes Backup scheint leer oder defekt."
            rt.merge_backup_realtest_state(
                last_verify_ok=False,
                last_verify_shallow_ok=False,
                last_verify_path=str(bf),
                last_failure_kind="verify_encrypted_basic_fail",
                last_failure_message=msg,
            )

        rt.logger().info(
            "Backup-Verify (basic, encrypted)",
            extra={"action": "backup_verify", "path": backup_file, "mode": mode, "valid": bool(results["valid"])},
        )
        vcode = "backup.verify_shallow_encrypted_ok" if results["valid"] else "backup.verify_shallow_encrypted_fail"
        vsev = "warning" if results["valid"] else "error"
        return rt.with_backup_contract(
            {
                "status": "warning" if results["valid"] else "error",
                "api_status": api_status,
                "message": msg,
                "data": {"results": results},
                "results": results,
            },
            vcode,
            vsev,
        )

    # Tiefenprüfung für verschlüsselte Backups
    if is_encrypted and mode == "deep":
        try:
            module = rt.get_backup_module()
        except Exception as e:
            results["error"] = f"Backup-Modul konnte nicht geladen werden: {str(e)}"
            rt.logger().error("Backup-Verify tief fehlgeschlagen (BackupModule)", extra={"action": "backup_verify", "path": backup_file, "error": str(e)})
            rt.merge_backup_realtest_state(
                last_verify_ok=False,
                last_verify_path=str(bf),
                last_failure_kind="verify_module_load",
                last_failure_message=str(e)[:300],
            )
            return rt.with_backup_contract(
                {
                    "status": "success",
                    "api_status": "error",
                    "message": "Backup-Modul konnte nicht geladen werden",
                    "data": {"results": results},
                    "results": results,
                },
                "backup.verify_module_load_failed",
                "error",
            )

        module.rt.run_command = rt.run_command

        # Temporäres Verzeichnis für Entschlüsselung
        tmp_root = Path("/tmp/pi-installer-backup-verify")
        tmp_root.mkdir(parents=True, exist_ok=True)
        tmp_dir = tempfile.mkdtemp(prefix="verify-", dir=str(tmp_root))
        tmp_dir_path = Path(tmp_dir)
        decrypted_path = tmp_dir_path / "decrypted.tar.gz"

        try:
            ok, out_file, err = module.decrypt_backup(
                encrypted_file=backup_file,
                encryption_key=encryption_key,
                encryption_method="gpg" if backup_file.endswith(".gpg") or ".gpg" in backup_file else "openssl",
                output_file=str(decrypted_path),
                sudo_password="",
            )
            if not ok:
                results["error"] = f"Entschlüsselung fehlgeschlagen: {err or 'Unbekannter Fehler'}"
                rt.logger().warning("Backup-Verify tief: Entschlüsselung fehlgeschlagen", extra={"action": "backup_verify", "path": backup_file})
                rt.merge_backup_realtest_state(
                    last_verify_ok=False,
                    last_verify_path=str(bf),
                    last_failure_kind="verify_decrypt_fail",
                    last_failure_message=(err or "")[:300],
                )
                return rt.with_backup_contract(
                    {
                        "status": "success",
                        "api_status": "error",
                        "message": "Entschlüsselung des Backups fehlgeschlagen",
                        "data": {"results": results},
                        "results": results,
                    },
                    "backup.verify_decrypt_failed",
                    "error",
                )

            if not decrypted_path.exists():
                results["error"] = "Entschlüsselte Datei wurde nicht erstellt"
                rt.logger().error("Backup-Verify tief: entschlüsselte Datei fehlt", extra={"action": "backup_verify", "path": backup_file})
                rt.merge_backup_realtest_state(
                    last_verify_ok=False,
                    last_verify_path=str(bf),
                    last_failure_kind="verify_decrypt_missing",
                    last_failure_message="Entschlüsselte Datei fehlt",
                )
                return rt.with_backup_contract(
                    {
                        "status": "success",
                        "api_status": "error",
                        "message": "Entschlüsselte Datei wurde nicht erstellt",
                        "data": {"results": results},
                        "results": results,
                    },
                    "backup.verify_decrypt_missing",
                    "error",
                )

            # Integritätsprüfung auf entschlüsselter Datei
            cmd = f"tar -tzf {shlex.quote(str(decrypted_path))} 2>&1 | head -100"
            res = await rt.run_command_async(cmd, timeout=60)

            if res.get("success") and res.get("stdout"):
                results["valid"] = True
                files = [line.strip() for line in res.get("stdout", "").split("\n") if line.strip()]
                results["file_count"] = len(files)
                results["sample_files"] = files[:20]
            else:
                results["valid"] = False
                error_msg = res.get("stderr") or res.get("error") or "Unbekannter Fehler"
                results["error"] = f"Backup-Archiv ist beschädigt oder ungültig: {error_msg[:200]}"

            rt.logger().info(
                "Backup-Verify tief abgeschlossen",
                extra={"action": "backup_verify", "path": backup_file, "mode": mode, "valid": bool(results["valid"]), "files": results.get("file_count")},
            )
            api_status = "ok" if results["valid"] else "error"
            msg = "Backup erfolgreich tief geprüft" if results["valid"] else "Backup-Archiv ist beschädigt oder ungültig"
            if results["valid"]:
                rt.merge_backup_realtest_state(
                    last_verify_ok=True,
                    last_verify_path=str(bf),
                    last_failure_kind="",
                    last_failure_message="",
                    open_critical_risks=[],
                    last_verify_shallow_ok=False,
                )
            else:
                rt.merge_backup_realtest_state(
                    last_verify_ok=False,
                    last_verify_path=str(bf),
                    last_failure_kind="verify_deep_tar_invalid",
                    last_failure_message=(results.get("error") or "")[:300],
                )
            vcode = "backup.verify_success" if results["valid"] else "backup.verify_failed"
            vsev = "success" if results["valid"] else "error"
            return rt.with_backup_contract(
                {
                    "status": "success",
                    "api_status": api_status,
                    "message": msg,
                    "data": {"results": results},
                    "results": results,
                },
                vcode,
                vsev,
            )
        finally:
            # Cleanup: entschlüsselte Datei und Temp-Verzeichnis entfernen
            try:
                if decrypted_path.exists():
                    decrypted_path.unlink()
            except Exception:
                pass
            try:
                # Entferne gesamtes temp-Verzeichnis
                import shutil

                if tmp_dir_path.exists():
                    shutil.rmtree(tmp_dir_path, ignore_errors=True)
            except Exception:
                pass

    # Unverschlüsselte Backups (oder deep ohne is_encrypted) — immer normalisierten Pfad (bf) verwenden
    cmd = f"tar -tzf {shlex.quote(str(bf))} 2>&1 | head -100"
    res = await rt.run_command_async(cmd, timeout=60)

    if res.get("success") and res.get("stdout"):
        results["valid"] = True
        files = [line.strip() for line in res.get("stdout", "").split("\n") if line.strip()]
        results["sample_files"] = files[:20]
        # Member-Gesamtzahl aus Voranalyse (plain .tar.gz): unabhängig von head -100 / wc -l
        if plain_arch_analysis is not None:
            results["file_count"] = (
                int(plain_arch_analysis.get("total_files") or 0)
                + int(plain_arch_analysis.get("total_dirs") or 0)
                + int(plain_arch_analysis.get("total_other") or 0)
            )
        else:
            results["file_count"] = len(files)
            # Zähle alle Einträge (nur wenn nicht plain .tar.gz mit Analyse)
            if results["file_count"] < 100:
                cmd_count = f"tar -tzf {shlex.quote(str(bf))} 2>/dev/null | wc -l"
                res_count = await rt.run_command_async(cmd_count, timeout=30)
                if res_count.get("success"):
                    try:
                        results["file_count"] = int(res_count.get("stdout", "0").strip())
                    except Exception:
                        pass
    else:
        results["valid"] = False
        error_msg = res.get("stderr") or res.get("error") or "Unbekannter Fehler"
        results["error"] = f"Backup-Archiv ist beschädigt oder ungültig: {error_msg[:200]}"

    rt.logger().info(
        "Backup-Verify abgeschlossen",
        extra={"action": "backup_verify", "path": backup_file, "mode": mode, "valid": bool(results["valid"]), "files": results.get("file_count")},
    )
    api_status = "ok" if results["valid"] else "error"
    msg = "Backup erfolgreich geprüft" if results["valid"] else "Backup-Archiv ist beschädigt oder ungültig"
    if plain_tar_gz:
        if results["valid"]:
            rt.merge_backup_realtest_state(
                last_verify_ok=True,
                last_verify_path=str(bf),
                last_failure_kind="",
                last_failure_message="",
                open_critical_risks=[],
                last_verify_shallow_ok=False,
            )
        else:
            rt.merge_backup_realtest_state(
                last_verify_ok=False,
                last_verify_path=str(bf),
                last_failure_kind="verify_tar_list_fail",
                last_failure_message=(results.get("error") or "")[:300],
            )
    vcode = "backup.verify_success" if results["valid"] else "backup.verify_failed"
    vsev = "success" if results["valid"] else "error"
    return rt.with_backup_contract(
        {
            "status": "success",
            "api_status": api_status,
            "message": msg,
            "data": {"results": results},
            "results": results,
        },
        vcode,
        vsev,
    )


async def delete_backup(request: Request):
    """Löscht ein Backup (.tar.gz, auch verschlüsselte .tar.gz.gpg/.tar.gz.enc) sicher (mit sudo fallback)."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    backup_file = (data.get("backup_file") or "").strip()
    sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")

    # Erlaube auch verschlüsselte Backups (.tar.gz.gpg, .tar.gz.enc)
    if not backup_file or not (backup_file.endswith(".tar.gz") or backup_file.endswith(".tar.gz.gpg") or backup_file.endswith(".tar.gz.enc")):
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {
                    "status": "error",
                    "api_status": "error",
                    "message": "backup_file (.tar.gz, .tar.gz.gpg oder .tar.gz.enc) erforderlich",
                    "data": {},
                },
                "backup.delete_missing_param",
                "error",
            ),
        )

    # Allowlist + Normalisierung
    try:
        bf = rt.normalize_path(backup_file)
        if not rt.is_under_allowed_root(bf):
            rt.logger().warning("Backup-Delete blockiert: Pfad außerhalb erlaubter Wurzeln", extra={"action": "backup_delete", "path": str(bf)})
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "api_status": "error",
                        "message": "Backup-Datei liegt außerhalb erlaubter Pfade",
                        "data": {},
                    },
                    "backup.permission_denied",
                    "error",
                    {"file": str(bf)},
                ),
            )
    except Exception as e:
        rt.logger().warning("Backup-Delete blockiert: ungültiger Pfad", extra={"action": "backup_delete", "path": backup_file, "error": str(e)})
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {
                    "status": "error",
                    "api_status": "error",
                    "message": f"Ungültiger Pfad: {str(e)}",
                    "data": {},
                },
                "backup.path_invalid",
                "error",
                {"reason": str(e)},
            ),
        )

    # Prüfe ob Datei existiert
    if not bf.exists():
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {
                    "status": "error",
                    "api_status": "error",
                    "message": "Backup-Datei existiert nicht",
                    "data": {},
                },
                "backup.backup_not_found",
                "error",
                {"file": str(bf)},
            ),
        )

    # Versuche zuerst ohne sudo zu löschen
    cmd = f"rm -f {shlex.quote(str(bf))}"
    res = await rt.run_command_async(cmd, sudo=False, timeout=30)
    
    # Wenn fehlgeschlagen und sudo verfügbar, versuche mit sudo
    if not res.get("success"):
        if sudo_password:
            res = await rt.run_command_async(cmd, sudo=True, sudo_password=sudo_password, timeout=30)
        else:
            # Versuche es nochmal mit sudo -n (falls NOPASSWD konfiguriert)
            res_sudo_n = await rt.run_command_async(cmd, sudo=True, sudo_password="", timeout=30)
            if res_sudo_n.get("success"):
                res = res_sudo_n

    # verify gone
    test = await rt.run_command_async(f"test -e {shlex.quote(str(bf))}", timeout=10)
    if test.get("success"):
        # Datei existiert noch - sammle Fehlerdetails
        error_parts = []
        if res.get("stderr"):
            stderr_text = (res.get("stderr") or "").strip()
            if stderr_text:
                error_parts.append(f"Fehler: {stderr_text[:300]}")
        if res.get("error"):
            error_text = (res.get("error") or "").strip()
            if error_text:
                error_parts.append(f"Details: {error_text[:300]}")
        
        # Prüfe Dateiberechtigungen
        perm_check = await rt.run_command_async(f"ls -la {shlex.quote(backup_file)} 2>&1", timeout=10)
        if perm_check.get("success") and perm_check.get("stdout"):
            error_parts.append(f"Berechtigungen: {perm_check.get('stdout')[:200]}")
        
        error_message = "Backup konnte nicht gelöscht werden."
        if error_parts:
            error_message += " " + " ".join(error_parts)
        else:
            error_message += " Möglicherweise fehlen Berechtigungen oder die Datei ist gesperrt."
        
        rt.logger().error(
            "Backup-Delete fehlgeschlagen",
            extra={"action": "backup_delete", "path": str(bf), "error": error_message},
        )
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {
                    "status": "error",
                    "api_status": "error",
                    "message": error_message,
                    "data": {},
                },
                "backup.delete_failed",
                "error",
            ),
        )
    
    # Erfolgreich gelöscht
    rt.logger().info("Backup gelöscht", extra={"action": "backup_delete", "path": str(bf)})
    return rt.with_backup_contract(
        {
            "status": "success",
            "api_status": "ok",
            "message": "Backup gelöscht",
            "data": {},
        },
        "backup.delete_ok",
        "success",
    )


async def restore_backup(request: Request):
    """
    Backup wiederherstellen.
    Phase 1: Standard = Preview-Mode (sicherer Test-Restore nach /mnt/setuphelfer-restore-preview/<ts>).
    Root-Restore bleibt vorerst gesperrt, bis Whitelist-Logik vollständig getestet ist.
    """
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}

        backup_file = (data.get("backup_file") or data.get("file") or "").strip()
        mode = (data.get("mode") or "preview").strip().lower()
        target_dir = (data.get("target_dir") or "").strip()
        restore_key = data.get("encryption_key") or data.get("password")
        if isinstance(restore_key, str):
            restore_key = restore_key.strip() or None
        else:
            restore_key = None

        if mode not in ("preview", "restore"):
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "api_status": "error",
                        "message": "Ungültiger Restore-Modus. Erlaubt sind nur 'preview' oder 'restore'.",
                        "data": {"mode": mode},
                    },
                    "backup.restore_invalid_mode",
                    "error",
                    {"mode": mode},
                ),
            )

        if not backup_file:
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "api_status": "error",
                        "message": "Backup-Datei erforderlich",
                        "data": {},
                    },
                    "backup.restore_missing_file",
                    "error",
                ),
            )

        # Pfad-Validierung wie bei verify (realpath + Allowlist)
        try:
            bf = rt.normalize_path(backup_file)
            if not rt.is_under_allowed_root(bf):
                rt.logger().warning("Restore blockiert: Backup-Datei außerhalb erlaubter Pfade", extra={"action": "backup_restore", "path": str(bf)})
                rt.merge_backup_realtest_state(
                    last_failure_kind="restore_path_disallowed",
                    last_failure_message="Restore: Pfad außerhalb Allowlist",
                )
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "api_status": "error",
                            "message": "Backup-Datei liegt außerhalb erlaubter Pfade",
                            "data": {"results": {"valid": False, "file": str(bf), "error": "Pfad außerhalb Allowlist"}},
                        },
                        "backup.permission_denied",
                        "error",
                        {"file": str(bf)},
                    ),
                )
        except Exception as e:
            rt.logger().warning("Restore blockiert: ungültiger Backup-Pfad", extra={"action": "backup_restore", "path": backup_file, "error": str(e)})
            rt.merge_backup_realtest_state(
                last_failure_kind="restore_path_invalid",
                last_failure_message=str(e)[:300],
            )
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "api_status": "error",
                        "message": f"Ungültiger Pfad: {str(e)}",
                        "data": {"results": {"valid": False, "file": backup_file, "error": str(e)[:300]}},
                    },
                    "backup.path_invalid",
                    "error",
                    {"reason": str(e)},
                ),
            )

        if not bf.exists():
            rt.merge_backup_realtest_state(
                last_failure_kind="restore_not_found",
                last_failure_message="Backup-Datei existiert nicht",
            )
            return rt.json_response(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "api_status": "error",
                        "message": "Backup-Datei existiert nicht",
                        "data": {"results": {"valid": False, "file": str(bf), "error": "Datei existiert nicht"}},
                    },
                    "backup.backup_not_found",
                    "error",
                    {"file": str(bf)},
                ),
            )

        import shutil as _shutil_restore
        import tempfile as _tmpfile_restore

        decrypt_temp_dir: Optional[str] = None
        work_archive = str(bf)
        try:
            if rt.backup_path_looks_encrypted(work_archive):
                if not restore_key:
                    rt.merge_backup_realtest_state(
                        last_failure_kind="restore_encrypted_no_password",
                        last_failure_message="Verschlüsseltes Backup: Passwort erforderlich",
                    )
                    return rt.json_response(
                        status_code=200,
                        content=rt.with_backup_contract(
                            {
                                "status": "error",
                                "api_status": "error",
                                "message": "Verschlüsseltes Backup: Passwort (password oder encryption_key) erforderlich.",
                                "data": {},
                            },
                            "backup.restore_decrypt_password_required",
                            "error",
                        ),
                    )
                tmp_root_restore = Path("/tmp/pi-installer-backup-restore")
                tmp_root_restore.mkdir(parents=True, exist_ok=True)
                decrypt_temp_dir = _tmpfile_restore.mkdtemp(prefix="restore-dec-", dir=str(tmp_root_restore))
                decrypted_restore_path = Path(decrypt_temp_dir) / "decrypted.tar.gz"
                try:
                    restore_mod = rt.get_backup_module()
                except Exception as e_mod:
                    rt.merge_backup_realtest_state(
                        last_failure_kind="restore_decrypt_module",
                        last_failure_message=str(e_mod)[:300],
                    )
                    return rt.json_response(
                        status_code=200,
                        content=rt.with_backup_contract(
                            {
                                "status": "error",
                                "api_status": "error",
                                "message": f"Backup-Modul konnte nicht geladen werden: {str(e_mod)[:200]}",
                                "data": {},
                            },
                            "backup.restore_decrypt_module_failed",
                            "error",
                            {"reason": str(e_mod)[:200]},
                        ),
                    )
                restore_mod.rt.run_command = rt.run_command
                enc_method_restore = "gpg" if ".gpg" in work_archive.lower() else "openssl"
                ok_dec_r, _dec_out_r, err_dec_r = restore_mod.decrypt_backup(
                    work_archive,
                    restore_key,
                    enc_method_restore,
                    str(decrypted_restore_path),
                    "",
                )
                if not ok_dec_r or not decrypted_restore_path.exists():
                    rt.merge_backup_realtest_state(
                        last_failure_kind="restore_decrypt_fail",
                        last_failure_message=(err_dec_r or "")[:300],
                    )
                    return rt.json_response(
                        status_code=200,
                        content=rt.with_backup_contract(
                            {
                                "status": "error",
                                "api_status": "error",
                                "message": "Backup konnte nicht entschlüsselt werden.",
                                "data": {"error": (err_dec_r or "")[:300]},
                            },
                            "backup.restore_decrypt_failed",
                            "error",
                            {"reason": (err_dec_r or "")[:200]},
                        ),
                    )
                work_archive = str(decrypted_restore_path)

            # Analyse des Archivs – gemeinsam für Preview/Root
            try:
                analysis = rt.analyze_tar_members(work_archive)
            except Exception as e:
                # Kein last_preview_ok / last_dry_run_ok überschreiben: Analysefehler ist kein fehlgeschlagener Lauf.
                rt.merge_backup_realtest_state(
                    last_failure_kind="restore_analyze_fail",
                    last_failure_message=str(e)[:300],
                )
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "api_status": "error",
                            "message": f"Backup-Archiv konnte nicht analysiert werden: {str(e)}",
                            "data": {"analysis_error": str(e)[:300]},
                        },
                        "backup.restore_analyze_failed",
                        "error",
                        {"reason": str(e)[:300]},
                    ),
                )

            if analysis["blocked_entries"]:
                rt.logger().warning(
                    "Restore blockiert: problematische Archiv-Einträge",
                    extra={
                        "action": "backup_restore",
                        "path": str(bf),
                        "blocked_count": len(analysis.get("blocked_entries") or []),
                    },
                )
                # Gesperrte Archive: kein Extraktionsversuch — last_*_ok nicht zurücksetzen (vgl. Real-Test-Reihenfolge).
                rt.merge_backup_realtest_state(
                    last_failure_kind="restore_blocked_entries",
                    last_failure_message="Archiv enthält gesperrte Einträge",
                )
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "api_status": "error",
                            "message": "Backup-Archiv enthält problematische Einträge (Pfad-Traversal, absolute Pfade oder nicht unterstützte Sonderdateien).",
                            "data": {"analysis": analysis},
                            "analysis": analysis,
                        },
                        "backup.restore_blocked_entries",
                        "error",
                        {"diagnosis_id": "RESTORE-PATH-004"},
                    ),
                )

            # Preview-Modus: sicherer Test-Restore in eigenes Verzeichnis (Sandbox unter /tmp, kein sudo nötig)
            if mode == "preview":
                ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
                rt.restore_preview_base().mkdir(parents=True, exist_ok=True)
                preview_dir = rt.restore_preview_base() / ts
                preview_dir.mkdir(parents=True, exist_ok=True)

                restore_cmd = f"tar -xzf {shlex.quote(work_archive)} -C {shlex.quote(str(preview_dir))}"
                # Sandbox liegt unter /tmp/setuphelfer-restore-test – hier ist kein sudo erforderlich
                restore_result = await rt.run_command_async(restore_cmd, sudo=False, sudo_password=None, timeout=7200)

                if not restore_result.get("success"):
                    rt.logger().error(
                        "Preview-Restore fehlgeschlagen",
                        extra={
                            "action": "backup_restore_preview",
                            "path": str(bf),
                            "preview_dir": str(preview_dir),
                            "error": (restore_result.get("stderr") or restore_result.get("error") or "")[:200],
                        },
                    )
                    rt.merge_backup_realtest_state(
                        last_preview_ok=False,
                        last_preview_dir=str(preview_dir),
                        last_preview_backup=str(bf),
                        last_failure_kind="restore_preview_extract_fail",
                        last_failure_message=(restore_result.get("stderr") or restore_result.get("error") or "")[:300],
                    )
                    return rt.json_response(
                        status_code=200,
                        content=rt.with_backup_contract(
                            {
                                "status": "error",
                                "api_status": "error",
                                "message": f"Preview-Restore fehlgeschlagen: {restore_result.get('stderr', 'Unbekannter Fehler')[:200]}",
                                "data": {
                                    "preview_dir": str(preview_dir),
                                    "analysis": analysis,
                                },
                                "preview_dir": str(preview_dir),
                                "analysis": analysis,
                            },
                            "backup.restore_failed",
                            "error",
                        ),
                    )

                # Metadaten für Preview-Antwort
                total_entries = analysis["total_files"] + analysis["total_dirs"] + analysis["total_other"]
                rt.logger().info(
                    "Preview-Restore erfolgreich",
                    extra={
                        "action": "backup_restore_preview",
                        "path": str(bf),
                        "preview_dir": str(preview_dir),
                        "total_entries": total_entries,
                    },
                )
                rt.merge_backup_realtest_state(
                    last_preview_ok=True,
                    last_preview_dir=str(preview_dir),
                    last_preview_backup=str(bf),
                    last_failure_kind="",
                    last_failure_message="",
                )
                rt.cleanup_old_preview_dirs(preview_dir)
                private_tmp_isolation = rt.private_tmp_isolation_active()
                preview_visibility_note = (
                    "Preview-Dateien liegen im PrivateTmp-Namespace des Backend-Dienstes und sind im normalen Host-/tmp ggf. nicht sichtbar."
                    if private_tmp_isolation
                    else "Preview-Dateien liegen im normalen /tmp-Namespace."
                )
                private_tmp_hint_key = "backup.messages.preview_private_tmp_hint" if private_tmp_isolation else ""
                return rt.with_backup_contract(
                    {
                        "status": "success",
                        "api_status": "ok",
                        "mode": "preview",
                        "message": "Test-Restore erfolgreich. System wurde nicht überschrieben.",
                        "preview_dir": str(preview_dir),
                        "private_tmp_isolation": private_tmp_isolation,
                        "preview_dir_visibility_note": preview_visibility_note,
                        "service_private_tmp_hint": private_tmp_hint_key,
                        "analysis": analysis,
                        "total_entries": total_entries,
                        "data": {
                            "mode": "preview",
                            "preview_dir": str(preview_dir),
                            "private_tmp_isolation": private_tmp_isolation,
                            "preview_dir_visibility_note": preview_visibility_note,
                            "service_private_tmp_hint": private_tmp_hint_key,
                            "analysis": analysis,
                            "total_entries": total_entries,
                        },
                    },
                    "backup.restore_preview_ok",
                    "success",
                    {
                        "total_entries": total_entries,
                        "private_tmp_isolation": private_tmp_isolation,
                        "preview_dir_visibility_note": preview_visibility_note,
                        "service_private_tmp_hint": private_tmp_hint_key,
                    },
                )

            # Restore-Modus: target_dir ist Pflicht und wird strikt validiert.
            if not target_dir:
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "api_status": "error",
                            "message": "Restore-Zielpfad fehlt (target_dir ist bei mode=restore erforderlich).",
                            "data": {"mode": mode},
                        },
                        "backup.restore_target_missing",
                        "error",
                    ),
                )

            if target_dir.strip() == "/":
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "api_status": "error",
                            "message": "Restore-Ziel '/' ist aus Sicherheitsgründen gesperrt.",
                            "data": {"target_dir": target_dir},
                        },
                        "backup.restore_target_invalid",
                        "error",
                        {"diagnosis_id": "RESTORE-RUNTIME-006", "target": target_dir},
                    ),
                )

            try:
                validated_target_dir = rt.validate_restore_target_dir(target_dir)
            except Exception as ve:
                reason = str(ve)
                diagnosis_id = ""
                code = "backup.restore_target_invalid"
                if "PERM-GROUP-008" in reason or "not writable" in reason.lower() or "nicht beschreibbar" in reason.lower():
                    code = "backup.restore_not_writable"
                    diagnosis_id = "PERM-GROUP-008"
                elif "STORAGE-PROTECTION-005" in reason:
                    diagnosis_id = "STORAGE-PROTECTION-005"
                elif "STORAGE-PROTECTION-004" in reason:
                    diagnosis_id = "STORAGE-PROTECTION-004"
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "api_status": "error",
                            "message": f"Ungültiges Restore-Ziel: {reason}",
                            "data": {"target_dir": target_dir},
                        },
                        code,
                        "error",
                        {"reason": reason, "target": target_dir, "diagnosis_id": diagnosis_id},
                    ),
                )

            restore_cmd = f"tar -xzf {shlex.quote(work_archive)} -C {shlex.quote(str(validated_target_dir))}"
            restore_result = await rt.run_command_async(restore_cmd, sudo=False, sudo_password=None, timeout=7200)
            if not restore_result.get("success"):
                err_txt = str(restore_result.get("stderr") or restore_result.get("error") or restore_result.get("stdout") or "")
                if "Permission denied" in err_txt or "Keine Berechtigung" in err_txt:
                    return rt.json_response(
                        status_code=200,
                        content=rt.with_backup_contract(
                            {
                                "status": "error",
                                "api_status": "error",
                                "message": "Restore-Ziel ist nicht beschreibbar.",
                                "data": {"target_dir": validated_target_dir, "error": err_txt[:300]},
                            },
                            "backup.restore_not_writable",
                            "error",
                            {"diagnosis_id": "PERM-GROUP-008", "target": validated_target_dir},
                        ),
                    )
                return rt.json_response(
                    status_code=200,
                    content=rt.with_backup_contract(
                        {
                            "status": "error",
                            "api_status": "error",
                            "message": f"Restore fehlgeschlagen: {err_txt[:200] or 'Unbekannter Fehler'}",
                            "data": {"target_dir": validated_target_dir, "error": err_txt[:300]},
                        },
                        "backup.restore_failed",
                        "error",
                    ),
                )

            total_entries = analysis["total_files"] + analysis["total_dirs"] + analysis["total_other"]
            return rt.with_backup_contract(
                {
                    "status": "success",
                    "api_status": "ok",
                    "mode": "restore",
                    "message": "Restore erfolgreich ausgeführt.",
                    "target_dir": validated_target_dir,
                    "analysis": analysis,
                    "total_entries": total_entries,
                    "data": {
                        "mode": "restore",
                        "target_dir": validated_target_dir,
                        "analysis": analysis,
                        "total_entries": total_entries,
                    },
                },
                "backup.restore_success",
                "success",
                {"target_dir": validated_target_dir, "total_entries": total_entries},
            )
        finally:
            if decrypt_temp_dir:
                _shutil_restore.rmtree(decrypt_temp_dir, ignore_errors=True)
    except Exception as e:
        rt.logger().error(f"💥 Fehler bei Backup-Restore: {str(e)}", exc_info=True)
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {
                    "status": "error",
                    "api_status": "error",
                    "message": f"Fehler beim Restore: {str(e)}",
                    "data": {},
                },
                "backup.restore_failed",
                "error",
                {"detail": str(e)},
            ),
        )
