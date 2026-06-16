"""Backup execute handlers — first POST slice (Phase B.4)."""

from __future__ import annotations

import os
import shlex
import shutil
import signal
import threading
from pathlib import Path
from typing import Any, Optional

from fastapi import Request

from core import backup_readonly_runtime as rt
from core.backup_profiles import build_profile_preview


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

