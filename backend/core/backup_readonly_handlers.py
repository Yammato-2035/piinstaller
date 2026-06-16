"""Backup readonly HTTP handlers (Phase B.2)."""

from __future__ import annotations

import asyncio
import shlex
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from fastapi.responses import JSONResponse

from core import backup_readonly_runtime as rt

async def backup_jobs_list():
    """Liste aller Backup-Jobs, insbesondere laufende"""
    for jid in list(rt.get_backup_jobs().keys()):
        rt.sync_stale_runner_job(jid)
    running = []
    for job_id, job in rt.get_backup_jobs().items():
        status = job.get("status", "")
        if status in ("queued", "running", "cancel_requested") or not status:
            running.append(rt.job_snapshot(job))
    return rt.with_backup_contract({"status": "success", "jobs": running}, "backup.jobs_list", "success")



async def backup_job_status(job_id: str):
    job_id = (job_id or "").strip()
    if job_id in rt.get_backup_jobs():
        rt.sync_stale_runner_job(job_id)
    runner_status = rt.read_backup_runner_status(job_id)
    if runner_status:
        rt.sync_ram_job_from_runner(job_id)
    j_ram = rt.get_backup_jobs().get(job_id)
    if j_ram and str(j_ram.get("status") or "") == "error":
        return rt.with_backup_contract({"status": "success", "job": rt.job_snapshot(j_ram)}, "backup.job_status", "success")
    if runner_status:
        return rt.with_backup_contract({"status": "success", "job": rt.runner_status_to_job(runner_status)}, "backup.job_status", "success")
    job = rt.get_backup_jobs().get(job_id)
    if not job:
        return JSONResponse(
            status_code=200,
            content=rt.with_backup_contract({"status": "error", "message": "Job nicht gefunden"}, "backup.job_not_found", "error"),
        )
    return rt.with_backup_contract({"status": "success", "job": rt.job_snapshot(job)}, "backup.job_status", "success")



async def backup_job_evidence_get(job_id: str):
    """Liest vorhandenes Evidence-Manifest (kein Backup-/Restore-Start)."""
    jid = (job_id or "").strip()
    if not rt.backup_job_id_re().fullmatch(jid):
        return JSONResponse(
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
    mp_path, manifest = rt.read_backup_evidence_manifest_disk(jid)
    ev = rt.normalize_evidence_api_payload(manifest, mp_path)
    if ev.get("evidence_status") == "not_available":
        return rt.with_backup_contract(
            {"status": "success", "evidence": ev},
            "backup.evidence.not_available",
            "info",
            {"job_id": jid},
        )
    return rt.with_backup_contract(
        {"status": "success", "evidence": ev},
        "backup.evidence.ok",
        "success",
        {"job_id": jid},
    )



async def backup_status():
    """Backup-Status abrufen"""
    try:
        # Prüfe installierte Backup-Tools
        data = {
            "rsync": {
                "installed": rt.check_installed("rsync"),
            },
            "tar": {
                "installed": rt.check_installed("tar"),
            },
            "backup_scripts": {
                "installed": rt.run_command("test -f /usr/local/bin/pi-backup")["success"],
            },
            "backups": [],
        }
        return rt.with_backup_contract(
            {
                "status": "success",
                "api_status": "ok",
                "message": "",
                "data": data,
                **data,
            },
            "backup.status_ok",
            "success",
        )
    except Exception as e:
        rt.logger().error(f"Fehler beim Lesen des Backup-Status: {e}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content=rt.with_backup_contract(
                {
                    "status": "error",
                    "api_status": "error",
                    "message": str(e),
                    "data": {},
                },
                "backup.status_failed",
                "error",
                {"detail": str(e)},
            ),
        )


# -------------------- Backup Settings + Scheduling --------------------


async def backup_get_settings():
    s = rt.read_backup_settings()
    # Timer status (per rule)
    statuses = {}
    for r in (s.get("schedules") or []):
        if not isinstance(r, dict) or not r.get("id"):
            continue
        svc = rt.systemd_timer_name(str(r["id"]))
        enabled = rt.run_command(f"systemctl is-enabled {svc}.timer 2>/dev/null").get("stdout", "").strip()
        active = rt.run_command(f"systemctl is-active {svc}.timer 2>/dev/null").get("stdout", "").strip()
        statuses[str(r["id"])] = {"enabled": enabled, "active": active}
    s["_timer_status"] = statuses
    return rt.with_backup_contract({"status": "success", "settings": s}, "backup.settings_loaded", "success")



async def backup_cloud_list(rule_id: str = ""):
    """
    Listet externe Backups im konfigurierten WebDAV-Ziel (Seafile).
    Nutzt gespeicherte Settings (backup.json unter get_config_dir()).
    """
    settings = rt.read_backup_settings()
    cloud = settings.get("cloud") or {}
    if not cloud.get("enabled"):
        return rt.with_backup_contract(
            {"status": "success", "backups": [], "message": "Cloud-Upload ist deaktiviert"},
            "backup.cloud_list_disabled",
            "info",
        )
    provider = cloud.get("provider") or "seafile_webdav"
    
    # Versuche Backup-Modul zu verwenden für alle Provider
    try:
        backup_mod = rt.get_backup_module()
        backup_mod.rt.run_command = rt.run_command
        
        # Für WebDAV: Verwende bestehende Logik
        if provider in ("seafile_webdav", "webdav", "nextcloud_webdav"):
            pass  # Weiter mit WebDAV-Logik unten
        # Für S3: Versuche S3-Liste
        elif provider in ("s3", "s3_compatible"):
            bucket = cloud.get("bucket") or ""
            if not bucket:
                return rt.with_backup_contract(
                    {"status": "success", "backups": [], "message": "S3-Bucket nicht konfiguriert"},
                    "backup.cloud_list_s3_unconfigured",
                    "warning",
                )
            # TODO: S3-Liste implementieren
            return rt.with_backup_contract(
                {"status": "success", "backups": [], "message": "S3-Liste wird noch nicht unterstützt"},
                "backup.cloud_list_s3_unsupported",
                "info",
            )
        # Für andere Provider: Noch nicht unterstützt
        else:
            return rt.with_backup_contract(
                {"status": "success", "backups": [], "message": f"Provider '{provider}' wird für Cloud-Liste noch nicht unterstützt"},
                "backup.cloud_list_provider_unsupported",
                "info",
                {"provider": provider},
            )
    except Exception as e:
        rt.logger().error(f"Fehler beim Abrufen der Cloud-Backups: {str(e)}", exc_info=True)
        # Fallback auf WebDAV
    
    # Unterstütze WebDAV-basierte Provider (Fallback)
    if provider not in ("seafile_webdav", "webdav", "nextcloud_webdav"):
        return rt.with_backup_contract(
            {"status": "success", "backups": [], "message": f"Provider '{provider}' wird für Cloud-Liste nicht unterstützt"},
            "backup.cloud_list_provider_unsupported",
            "info",
            {"provider": provider},
        )

    url = (cloud.get("webdav_url") or "").strip().rstrip("/")
    user = (cloud.get("username") or "").strip()
    pw = (cloud.get("password") or "").strip()
    remote_path = (cloud.get("remote_path") or "").strip().strip("/")

    if not url or not user or not pw:
        return JSONResponse(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": "WebDAV URL + Username + Passwort fehlen"},
                "backup.cloud_list_credentials_missing",
                "error",
            ),
        )

    base = f"{url}/{remote_path}" if remote_path else url
    # Ensure trailing slash for collection listing
    if not base.endswith("/"):
        base = base + "/"

    # PROPFIND Depth:1 to list directory contents
    cmd = (
        "curl -sS "
        f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
        "-X PROPFIND -H 'Depth: 1' "
        f"{shlex.quote(base)}"
    )
    res = rt.run_command(cmd)
    if not res.get("success"):
        return JSONResponse(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": (res.get("stderr") or res.get("error") or "Request fehlgeschlagen")[:300]},
                "backup.cloud_list_request_failed",
                "error",
            ),
        )

    xml_text = (res.get("stdout") or "").strip()
    if not xml_text:
        return rt.with_backup_contract({"status": "success", "backups": []}, "backup.cloud_list_ok", "success")

    rid = (rule_id or "").strip()
    backups = []
    try:
        # Parse DAV XML. Be tolerant with namespaces.
        root = ET.fromstring(xml_text)
        ns_dav = "{DAV:}"

        def _text(el, path):
            try:
                n = el.find(path)
                return (n.text or "").strip() if n is not None else ""
            except Exception:
                return ""

        for resp in root.findall(f".//{ns_dav}response"):
            href = _text(resp, f"{ns_dav}href")
            if not href:
                continue
            # skip directory itself
            if href.rstrip("/") == base.rstrip("/"):
                continue
            # We only care about backup files (inkl. verschlüsselte)
            name = href.split("/")[-1]
            if not (name.endswith(".tar.gz") or name.endswith(".tar.gz.gpg") or name.endswith(".tar.gz.enc")):
                continue
            if rid and f"-{rid}-" not in name:
                # only filter those that encode rule id in filename
                continue

            size = None
            last_modified = None
            for propstat in resp.findall(f"{ns_dav}propstat"):
                prop = propstat.find(f"{ns_dav}prop")
                if prop is None:
                    continue
                cl = prop.find(f"{ns_dav}getcontentlength")
                lm = prop.find(f"{ns_dav}getlastmodified")
                if cl is not None and cl.text:
                    try:
                        size = int(cl.text.strip())
                    except Exception:
                        size = None
                if lm is not None and lm.text:
                    last_modified = lm.text.strip()
            backup_info = {"name": name, "href": href, "size_bytes": size, "last_modified": last_modified}
            # Markiere verschlüsselte Backups
            if name.endswith(".gpg") or name.endswith(".enc"):
                backup_info["encrypted"] = True
            backup_info["location"] = "Cloud"
            backups.append(backup_info)

        # sort newest first if possible
        backups.sort(key=lambda b: (b.get("last_modified") or "", b.get("name") or ""), reverse=True)
    except Exception:
        # fallback: if parsing fails, return empty but not error (avoid breaking UI)
        backups = []

    return rt.with_backup_contract(
        {"status": "success", "backups": backups, "base_url": base},
        "backup.cloud_list_ok",
        "success",
        {"count": len(backups)},
    )



async def backup_cloud_quota():
    """Gibt verfügbaren Speicherplatz für Cloud-Backups zurück"""
    try:
        settings = rt.read_backup_settings()
        cloud = settings.get("cloud") or {}
        if not cloud.get("enabled"):
            return rt.with_backup_contract(
                {"status": "success", "quota": None, "message": "Cloud-Upload ist deaktiviert"},
                "backup.cloud_quota_disabled",
                "info",
            )
        
        provider = cloud.get("provider") or "seafile_webdav"
        url = (cloud.get("webdav_url") or "").strip().rstrip("/")
        user = (cloud.get("username") or "").strip()
        pw = (cloud.get("password") or "").strip()
        
        if not url or not user or not pw:
            return rt.with_backup_contract(
                {"status": "success", "quota": None, "message": "Cloud-Settings unvollständig"},
                "backup.cloud_quota_incomplete_settings",
                "warning",
            )
        
        # Versuche Quota-Informationen zu erhalten (WebDAV QUOTA Property)
        # Für Seafile/Nextcloud: PROPFIND mit Quota-Property
        base = url.rstrip("/")
        cmd = (
            "curl -sS "
            f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
            "-X PROPFIND -H 'Depth: 0' "
            f"{shlex.quote(base)}"
        )
        res = rt.run_command(cmd)
        
        if not res.get("success"):
            return rt.with_backup_contract(
                {"status": "success", "quota": None, "message": "Quota-Informationen nicht verfügbar"},
                "backup.cloud_quota_unavailable",
                "info",
            )
        
        xml_text = (res.get("stdout") or "").strip()
        if not xml_text:
            return rt.with_backup_contract(
                {"status": "success", "quota": None, "message": "Keine Quota-Informationen"},
                "backup.cloud_quota_empty_response",
                "info",
            )
        
        # Parse XML für Quota-Informationen
        try:
            root = ET.fromstring(xml_text)
            ns_dav = "{DAV:}"
            
            # Suche nach quota-used und quota-available
            quota_used = None
            quota_available = None
            
            for propstat in root.findall(f".//{ns_dav}propstat"):
                prop = propstat.find(f"{ns_dav}prop")
                if prop is None:
                    continue
                
                # Seafile/Nextcloud verwenden verschiedene Namespaces
                for ns in ["{DAV:}", "{http://owncloud.org/ns}", "{http://nextcloud.org/ns}"]:
                    used_el = prop.find(f"{ns}quota-used-bytes")
                    avail_el = prop.find(f"{ns}quota-available-bytes")
                    
                    if used_el is not None and used_el.text:
                        try:
                            quota_used = int(used_el.text.strip())
                        except Exception:
                            pass
                    if avail_el is not None and avail_el.text:
                        try:
                            quota_available = int(avail_el.text.strip())
                        except Exception:
                            pass
            
            if quota_used is not None or quota_available is not None:
                def human(n: int) -> str:
                    for unit in ["B", "KB", "MB", "GB", "TB"]:
                        if n < 1024:
                            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
                        n /= 1024
                    return f"{n:.1f} TB"
                
                total = (quota_used or 0) + (quota_available or 0) if quota_available is not None else None
                
                return rt.with_backup_contract(
                    {
                        "status": "success",
                        "quota": {
                            "used_bytes": quota_used,
                            "available_bytes": quota_available,
                            "total_bytes": total,
                            "used_human": human(quota_used) if quota_used is not None else None,
                            "available_human": human(quota_available) if quota_available is not None else None,
                            "total_human": human(total) if total else None,
                            "used_percent": round((quota_used / total * 100), 1) if (quota_used and total and total > 0) else None,
                        },
                    },
                    "backup.cloud_quota_ok",
                    "success",
                )
        except Exception as e:
            rt.logger().debug(f"Quota-Parsing fehlgeschlagen: {str(e)}")
        
        return rt.with_backup_contract(
            {"status": "success", "quota": None, "message": "Quota-Informationen nicht verfügbar für diesen Provider"},
            "backup.cloud_quota_provider_unsupported",
            "info",
        )
    except Exception as e:
        rt.logger().error(f"Fehler beim Abrufen der Cloud-Quota: {str(e)}", exc_info=True)
        return rt.with_backup_contract({"status": "error", "message": str(e)}, "backup.cloud_quota_failed", "error", {"detail": str(e)})



async def backup_targets():
    """Liste sinnvoller Backup-Ziele (z.B. USB-Sticks / gemountete Datenträger)."""
    try:
        data = rt.lsblk_tree()
        targets = []
        if data:
            try:
                devices = data.get("blockdevices", []) or []

                system_mounts = {"/", "/boot", "/boot/firmware", "[SWAP]"}

                def add_target(d, mp, extra=None):
                    payload = {
                        "name": d.get("name"),
                        "label": d.get("label"),
                        "size": d.get("size"),
                        "fstype": d.get("fstype"),
                        "mountpoint": mp,
                        "rm": d.get("rm"),
                        "model": d.get("model"),
                        "tran": d.get("tran"),
                        "device": f"/dev/{d.get('name')}" if d.get("name") else None,
                        "mounted": bool(mp),
                    }
                    if extra:
                        payload.update(extra)
                    targets.append(payload)

                def walk(items, disk_ctx=None):
                    for d in items:
                        dtype = d.get("type")
                        if dtype == "disk":
                            disk_ctx = d

                        name = d.get("name")
                        mps = d.get("mountpoints")
                        mp = d.get("mountpoint")

                        # mounted items
                        if isinstance(mps, list) and mps:
                            for one in mps:
                                if one and one not in system_mounts:
                                    add_target(d, one, {"mounted": True})
                        elif mp and mp not in system_mounts:
                            add_target(d, mp, {"mounted": True})

                        # unmounted USB/Removable partitions → anzeigen, damit der Stick "erkannt" wird
                        if dtype == "part" and disk_ctx and name:
                            dtran = disk_ctx.get("tran") or d.get("tran")
                            drm = disk_ctx.get("rm") if disk_ctx.get("rm") is not None else d.get("rm")
                            is_usb = dtran == "usb"
                            is_rm = bool(drm)
                            has_mount = bool(mp) or (isinstance(mps, list) and len(mps) > 0)
                            if (is_usb or is_rm) and not has_mount:
                                add_target(d, None, {"mounted": False, "tran": dtran, "rm": drm, "model": disk_ctx.get("model")})

                        if d.get("children"):
                            walk(d["children"], disk_ctx)

                walk(devices, None)
            except Exception:
                # Ignorieren - targets bleibt leer
                pass

        # Ergänzung: Mounts unter /mnt/pi-installer-usb sicher aufnehmen (auch wenn lsblk nichts liefert)
        try:
            for fs in rt.findmnt_mounts():
                tgt = (fs.get("target") or "").strip()
                if tgt.startswith("/mnt/pi-installer-usb/"):
                    # Doppelte vermeiden
                    if not any(t.get("mountpoint") == tgt for t in targets):
                        targets.append({
                            "name": None,
                            "label": None,
                            "size": None,
                            "fstype": fs.get("fstype"),
                            "mountpoint": tgt,
                            "rm": None,
                            "model": None,
                            "tran": None,
                        })
        except Exception:
            pass

        # Fallback: typische Pfade (ohne Garantie)
        common = ["/mnt", "/mnt/pi-installer-usb", "/media", "/run/media"]
        return rt.with_backup_contract(
            {"status": "success", "targets": targets, "common_roots": common},
            "backup.targets_ok",
            "success",
            {"count": len(targets)},
        )
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content=rt.with_backup_contract(
                {
                    "status": "error",
                    "message": str(e),
                    "targets": [],
                    "common_roots": ["/mnt", "/mnt/pi-installer-usb", "/media", "/run/media"],
                },
                "backup.targets_failed",
                "error",
                {"detail": str(e)},
            ),
        )


async def backup_external_targets_list():
    """Read-only: externe USB/removable-Kandidaten für /media/setuphelfer/<label>."""
    try:
        from core.backup_target_auto_prepare import discover_external_backup_candidates

        items = [c.to_public_dict() for c in discover_external_backup_candidates()]
        return rt.with_backup_contract(
            {"status": "success", "candidates": items, "count": len(items)},
            "backup.external_targets_ok",
            "success",
            {"count": len(items)},
        )
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": str(e), "candidates": []},
                "backup.external_targets_failed",
                "error",
                {"detail": str(e)},
            ),
        )



async def backup_profiles_list_get():
    return rt.backup_profiles_list_payload()



async def backup_usb_info(mountpoint: str = "", device: str = ""):
    """Gibt Infos zum ausgewählten USB-Mountpoint zurück (Device, FS, Label, Safety Flags)."""
    try:
        node = rt.find_lsblk_by_mountpoint(mountpoint) if mountpoint else None
        # Fallback: manchmal ist lsblk nicht synchron / mountpoint kommt nicht zurück -> findmnt SOURCE nutzen
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
            return JSONResponse(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "USB-Gerät nicht gefunden (Mountpoint/Device)"},
                    "backup.usb_not_found",
                    "error",
                ),
            )

        name = node.get("name")
        pk = node.get("pkname")  # parent disk
        disk_name = pk or (name if node.get("type") == "disk" else None)
        if not disk_name:
            return JSONResponse(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": "Konnte Disk nicht bestimmen"},
                    "backup.usb_disk_unknown",
                    "error",
                ),
            )

        disk = rt.find_disk_by_name(disk_name)
        if not disk:
            return JSONResponse(
                status_code=200,
                content=rt.with_backup_contract({"status": "error", "message": "Disk nicht gefunden"}, "backup.usb_disk_not_found", "error"),
            )

        info = {
            "status": "success",
            "mountpoint": mountpoint or None,
            "partition": f"/dev/{name}" if name else None,
            "disk": f"/dev/{disk_name}",
            "fstype": node.get("fstype"),
            "label": node.get("label"),
            "size": node.get("size"),
            "rm": disk.get("rm"),
            "ro": node.get("ro") or disk.get("ro"),
            "tran": disk.get("tran"),
            "model": disk.get("model"),
            "is_usb": (disk.get("tran") == "usb"),
            "is_removable": bool(disk.get("rm")),
            "is_system_disk": rt.disk_is_system(disk),
        }
        return rt.with_backup_contract(info, "backup.usb_info_ok", "success")
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content=rt.with_backup_contract({"status": "error", "message": str(e)}, "backup.usb_info_failed", "error", {"detail": str(e)}),
        )



async def list_backups(backup_dir: str = "/mnt/setuphelfer/backups"):
    """Liste aller Backups"""
    try:
        rt.logger().info("backup_list start", extra={"action": "backup_list", "backup_dir": str(backup_dir)})
        details = {}
        try:
            backup_dir, details = rt.validate_backup_list_dir(backup_dir)
        except Exception as ve:
            rt.logger().error("backup_list validate_error", extra={"action": "backup_list", "backup_dir": str(backup_dir), "error": str(ve)[:300]})
            reason = str(ve)
            diagnosis_id = ""
            if "STORAGE-PROTECTION-005" in reason:
                diagnosis_id = "STORAGE-PROTECTION-005"
            elif "STORAGE-PROTECTION-004" in reason:
                diagnosis_id = "STORAGE-PROTECTION-004"
            return JSONResponse(
                status_code=200,
                content=rt.with_backup_contract(
                    {"status": "error", "message": f"Ungültiges Backup-Ziel: {str(ve)}", "backups": []},
                    "backup.path_invalid",
                    "error",
                    {
                        "reason": reason,
                        "diagnosis_id": diagnosis_id,
                        "target": details.get("target", backup_dir),
                        "validation_mode": "read_only",
                    },
                ),
            )

        try:
            idx = await asyncio.wait_for(asyncio.to_thread(rt.load_backup_index), timeout=1.0)
        except TimeoutError:
            return JSONResponse(
                status_code=200,
                content=rt.with_backup_contract(
                    {
                        "status": "error",
                        "message": "Backup-Index konnte nicht rechtzeitig gelesen werden.",
                        "backups": [],
                    },
                    "backup.list_timeout",
                    "error",
                    {"path": backup_dir, "phase": "index_read", "timeout_seconds": 1},
                ),
            )

        if not idx:
            return rt.with_backup_contract(
                {
                    "status": "success",
                    "backups": [],
                    "count": 0,
                    "path": backup_dir,
                    "validation_mode": "read_only",
                    "index_available": False,
                    "message": "Noch kein Backup-Index vorhanden",
                },
                "backup.list_ok",
                "success",
            )

        wanted_prefix = backup_dir.rstrip("/") + "/"
        matched = []
        for e in idx:
            bf = str(e.get("backup_file") or "")
            sp = str(e.get("storage_path") or "")
            if not bf:
                continue
            if not (sp == backup_dir or bf.startswith(wanted_prefix)):
                continue
            ext_ok = bf.endswith(".tar.gz") or bf.endswith(".tar.gz.gpg") or bf.endswith(".tar.gz.enc")
            if not ext_ok:
                continue
            row = {
                "file": bf,
                "size_bytes": int(e.get("size_bytes") or 0),
                "date": str(e.get("created_at") or ""),
                "encrypted": bool(e.get("encrypted")),
                "location": "Lokal",
                "status": "unknown",
                "type": str(e.get("type") or ""),
            }
            try:
                exists = await asyncio.wait_for(asyncio.to_thread(Path(bf).exists), timeout=0.2)
                row["status"] = "available" if exists else "missing"
            except TimeoutError:
                row["status"] = "unknown"
            matched.append(row)

        rt.logger().info("backup_list index_ok", extra={"action": "backup_list", "count": len(matched), "backup_dir": backup_dir})
        return rt.with_backup_contract(
            {
                "status": "success",
                "backups": matched,
                "count": len(matched),
                "path": backup_dir,
                "validation_mode": "read_only",
                "index_available": True,
            },
            "backup.list_ok",
            "success",
        )
    except Exception as e:
        rt.logger().error("Backup-Liste fehlgeschlagen", extra={"action": "backup_list", "error": str(e)[:300]}, exc_info=True)
        err_code = "backup.list_failed"
        detail = str(e)[:300]
        cmd = ""
        tsec = None
        if "Command" in detail and "timed out" in detail:
            err_code = "backup.list_timeout"
            cmd = detail
            tsec = 3
        return JSONResponse(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": str(e)[:500], "backups": []},
                err_code,
                "error",
                {"detail": detail, "command": cmd, "timeout_seconds": tsec},
            ),
        )


async def clone_disk_info(request: Request, refresh: int = 0):
    """Quell- und Ziel-Laufwerke für System-Clone auflisten. POST mit sudo_password nutzt dieses für blkid. refresh=1 umgeht Cache."""
    try:
        
        if refresh:
            rt.invalidate_clone_disk_info_cache()
        sudo_password = (rt.sudo_store().get_password() or "") or ""
        if request.method == "POST":
            try:
                body = await request.json()
                pw = (body.get("sudo_password") or "").strip()
                if pw:
                    sudo_password = pw
                    if not rt.sudo_store().has_password():
                        rt.sudo_store().store_password(pw)
            except Exception:
                pass
        info = rt.clone_disk_info(sudo_password=sudo_password)
        return rt.with_backup_contract({"status": "success", **info}, "backup.clone_disk_info_ok", "success")
    except Exception as e:
        rt.logger().exception("clone disk-info failed")
        return rt.json_response(
            status_code=200,
            content=rt.with_backup_contract(
                {"status": "error", "message": str(e), "source": {}, "boot": {}, "targets": []},
                "backup.clone_disk_info_failed",
                "error",
                {"detail": str(e)},
            ),
        )
