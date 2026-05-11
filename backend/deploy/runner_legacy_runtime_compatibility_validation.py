from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)

_ALIAS_REL = "docs/evidence/runtime-results/handoff/compatibility_aliases.json"
_ZERO_STATE_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_zero_state_verification.json"
_BRANDING_REL = "docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json"
_LEGACY_INV_REL = "docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json"

_OUT_INV = "docs/evidence/runtime-results/handoff/legacy_runtime_compatibility_inventory.json"
_OUT_COEX = "docs/evidence/runtime-results/handoff/legacy_runtime_coexistence_analysis.json"
_OUT_REC = "docs/evidence/runtime-results/handoff/legacy_runtime_safe_migration_recommendations.json"
_OUT_MATRIX = "docs/evidence/runtime-results/handoff/legacy_upgrade_path_matrix.json"
_MAX_OUTPUT_BYTES = 512 * 1024


def _resolve_handoff(rel_path: str, prefix: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, f"{prefix}_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, f"{prefix}_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, f"{prefix}_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, f"{prefix}_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _load_json_handoff(rel: str, prefix: str) -> tuple[Any | None, str | None]:
    p, err = _resolve_handoff(rel, prefix)
    if err or p is None or not p.is_file():
        return None, err or f"{prefix}_MISSING"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception:
        return None, f"{prefix}_JSON_INVALID"


def _gate_statuses(zero: dict[str, Any] | None, brand: dict[str, Any] | None) -> dict[str, str]:
    zs = str(zero.get("zero_state_status") or "") if isinstance(zero, dict) else ""
    bg = str(brand.get("branding_guard_status") or "") if isinstance(brand, dict) else ""
    return {"zero_state_status": zs, "branding_guard_status": bg}


def _token_blob(tokens: list[str]) -> str:
    return " ".join(t.lower() for t in tokens)


def _classify_legacy_runtime_row(path: str, tokens: list[str]) -> list[str]:
    pl = path.replace("\\", "/").lower()
    tb = _token_blob(tokens)
    blob = pl + " " + tb
    cats: list[str] = []

    if "de.pi-installer.app" in blob or ".local/share" in pl and "pi-installer" in blob:
        cats.append("legacy_appdata")
    if ("localstorage" in blob or "local_storage" in blob) and ("pi-installer" in blob or "pi_installer" in blob):
        cats.append("local_storage_keys")
    if (pl.endswith(".desktop") or ".desktop" in pl) and ("pi-installer" in blob or "pi_installer" in blob):
        cats.append("desktop_files")
    if ".service" in pl or "pi-installer.service" in blob or "systemd" in pl:
        cats.append("service_files")
    if "pi-installer" in pl and (".env" in pl or pl.endswith(".env") or "env" in pl.split("/")):
        cats.append("env_files")
    if "pi_installer_" in tb or "pi_installer_" in pl:
        if ".env" in pl or "env" in pl or "environment" in pl:
            cats.append("env_files")
    if "/opt/pi-installer" in blob or "opt/pi-installer" in pl:
        cats.append("opt_pi_installer_paths")
    if re.search(r"[/\\]logs?([/\\]|$)", pl) or "/log/" in pl or pl.endswith(".log"):
        cats.append("logs")
    if "backup" in pl or "backup" in tb or "/mnt/" in pl and "backup" in blob:
        cats.append("backup_paths")
    if "config" in pl and "pi-installer" in blob and cats.count("env_files") == 0:
        cats.append("configs")
    if "pi-installer" in blob and not cats:
        if any(x in pl for x in ("config", "conf", "settings")):
            cats.append("configs")

    return list(dict.fromkeys(cats))


def _append_category(
    buckets: dict[str, list[dict[str, Any]]],
    cats: list[str],
    row: dict[str, Any],
) -> None:
    for c in cats:
        buckets.setdefault(c, []).append(row)


def build_legacy_runtime_compatibility_inventory(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    key_status = "legacy_runtime_compatibility_inventory_status"
    key_body = "legacy_runtime_compatibility_inventory"
    out_path, oerr = _resolve_handoff(_OUT_INV, "LEGACY_RT_INV")
    if oerr or out_path is None:
        return _emit_inv("blocked", {}, [oerr or "LEGACY_RT_INV_OUTPUT_INVALID"], [], wrote_file=False)
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _emit_inv("blocked", {}, ["LEGACY_RT_INV_EXISTS_NO_OVERWRITE"], [], wrote_file=False)

    inv, ierr = _load_json_handoff(_LEGACY_INV_REL, "INV")
    zero, zerr = _load_json_handoff(_ZERO_STATE_REL, "ZERO")
    brand, berr = _load_json_handoff(_BRANDING_REL, "BRAND")
    alias, aerr = _load_json_handoff(_ALIAS_REL, "ALIAS")

    errors: list[str] = []
    warnings: list[str] = []
    if ierr or not isinstance(inv, dict):
        errors.append(str(ierr or "LEGACY_RT_INV_INPUT_INVENTORY_MISSING"))
    if zerr or not isinstance(zero, dict):
        warnings.append(str(zerr or "LEGACY_RT_INV_ZERO_STATE_MISSING"))
        zero = {}
    if berr or not isinstance(brand, dict):
        warnings.append(str(berr or "LEGACY_RT_INV_BRANDING_GUARD_MISSING"))
        brand = {}
    if aerr:
        warnings.append(str(aerr or "LEGACY_RT_INV_ALIAS_MISSING"))

    buckets: dict[str, list[dict[str, Any]]] = {
        "legacy_appdata": [],
        "local_storage_keys": [],
        "desktop_files": [],
        "service_files": [],
        "env_files": [],
        "opt_pi_installer_paths": [],
        "logs": [],
        "configs": [],
        "backup_paths": [],
    }

    if isinstance(inv, dict):
        findings = inv.get("findings")
        if isinstance(findings, list):
            for raw in findings:
                if not isinstance(raw, dict):
                    continue
                path = str(raw.get("path") or "").replace("\\", "/")
                toks = raw.get("tokens")
                tokens = [str(x) for x in toks] if isinstance(toks, list) else []
                cats = _classify_legacy_runtime_row(path, tokens)
                if not cats:
                    continue
                entry = {
                    "path": path,
                    "line": raw.get("line"),
                    "classification": str(raw.get("classification") or ""),
                    "tokens": tokens,
                    "categories": cats,
                    "source": "legacy_identifier_inventory",
                }
                _append_category(buckets, cats, entry)

    gates = _gate_statuses(zero if isinstance(zero, dict) else None, brand if isinstance(brand, dict) else None)
    total = sum(len(v) for v in buckets.values())

    inv_status = "ok"
    if errors:
        inv_status = "blocked"
    elif total > 0:
        inv_status = "review_required"

    body: dict[str, Any] = {
        "legacy_runtime_compatibility_inventory_schema_version": 1,
        "strict_mode": "legacy_runtime_compatibility_inventory",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "inventory_status": inv_status,
        "gates": gates,
        "categories": buckets,
        "summary": {
            "total_classified_signals": total,
            "per_category_counts": {k: len(v) for k, v in buckets.items()},
        },
        "inputs": {
            "compatibility_aliases": _ALIAS_REL,
            "runtime_identifier_zero_state_verification": _ZERO_STATE_REL,
            "setuphelfer_branding_guard_check": _BRANDING_REL,
            "legacy_identifier_inventory": _LEGACY_INV_REL,
        },
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit_inv("blocked", {}, ["LEGACY_RT_INV_OUTPUT_TOO_LARGE"], warnings, wrote_file=False)
    if errors:
        return _emit_inv("blocked", body, errors, warnings, wrote_file=False)
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _emit_inv("blocked", {}, ["LEGACY_RT_INV_WRITE_FAILED"], warnings, wrote_file=False)
    return _emit_inv(inv_status, body, [], warnings, wrote_file=True)


def _emit_inv(
    status: str, body: dict[str, Any], errors: list[str], warnings: list[str], *, wrote_file: bool
) -> dict[str, Any]:
    return {
        "legacy_runtime_compatibility_inventory_status": status,
        "legacy_runtime_compatibility_inventory_file_path": _OUT_INV,
        "legacy_runtime_compatibility_inventory": body,
        "legacy_runtime_handoff_written": wrote_file,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def analyze_legacy_runtime_coexistence(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_OUT_COEX, "LEGACY_RT_COEX")
    if oerr or out_path is None:
        return _emit_coex("blocked", {}, [oerr or "LEGACY_RT_COEX_OUTPUT_INVALID"], [], wrote_file=False)
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _emit_coex("blocked", {}, ["LEGACY_RT_COEX_EXISTS_NO_OVERWRITE"], [], wrote_file=False)

    inv_body, ierr = _load_json_handoff(_OUT_INV, "RTINV")
    zero, _zerr = _load_json_handoff(_ZERO_STATE_REL, "ZERO")
    brand, _berr = _load_json_handoff(_BRANDING_REL, "BRAND")

    errors: list[str] = []
    warnings: list[str] = []
    if ierr or not isinstance(inv_body, dict):
        errors.append(str(ierr or "LEGACY_RT_COEX_INVENTORY_HANDOFF_MISSING"))

    conflicts: list[dict[str, Any]] = []
    gates = _gate_statuses(zero if isinstance(zero, dict) else None, brand if isinstance(brand, dict) else None)

    if gates.get("zero_state_status") == "blocked":
        conflicts.append(
            {"type": "zero_state_blocked", "severity": "high", "detail": "Zero-State-Verifikation blockiert Koexistenz-Freigabe."}
        )
    if gates.get("branding_guard_status") == "blocked":
        conflicts.append(
            {
                "type": "branding_guard_blocked",
                "severity": "high",
                "detail": "Branding-Guard meldet aktive Legacy-Marken in Runtime-Kontexten.",
            }
        )

    cats = inv_body.get("categories") if isinstance(inv_body, dict) else None
    svc = desktop = opt = env = 0
    if isinstance(cats, dict):
        svc = len(cats.get("service_files") or [])
        desktop = len(cats.get("desktop_files") or [])
        opt = len(cats.get("opt_pi_installer_paths") or [])
        env = len(cats.get("env_files") or [])

    legacy_svc = False
    setup_svc = False
    if isinstance(cats, dict):
        for row in cats.get("service_files") or []:
            if not isinstance(row, dict):
                continue
            tb = _token_blob(list(row.get("tokens") or []))
            pl = str(row.get("path") or "").lower()
            if "setuphelfer" in tb or "setuphelfer.service" in pl:
                setup_svc = True
            if "pi-installer" in tb or "pi_installer" in tb or "pi-installer.service" in pl:
                legacy_svc = True

    if legacy_svc and setup_svc:
        conflicts.append(
            {
                "type": "duplicate_runtime",
                "severity": "high",
                "detail": "Legacy- und Setuphelfer-Service-Signale gleichzeitig — parallele Runtime riskant.",
            }
        )

    if desktop > 1:
        conflicts.append(
            {"type": "duplicate_desktop_entries", "severity": "medium", "detail": "Mehrere Desktop-Eintraege mit Legacy-Bezug."}
        )

    if env > 0 and gates.get("branding_guard_status") != "blocked":
        conflicts.append(
            {"type": "legacy_env_files", "severity": "low", "detail": "Alte ENV-Dateien mit Legacy-Bezug — manuelle Pruefung.",}
        )

    coex_status = "ok"
    high_n = sum(1 for c in conflicts if c.get("severity") == "high")
    if errors:
        coex_status = "blocked"
    elif high_n > 0:
        coex_status = "blocked"
    elif (
        sum(1 for c in conflicts if c.get("severity") == "medium") > 0
        or env > 0
        or (isinstance(cats, dict) and sum(len(v or []) for v in cats.values()) > 0)
    ):
        coex_status = "review_required"

    body: dict[str, Any] = {
        "legacy_runtime_coexistence_schema_version": 1,
        "strict_mode": "legacy_runtime_coexistence_analysis",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "coexistence_status": coex_status,
        "gates": gates,
        "conflicts": conflicts,
        "signals": {"service_files": svc, "desktop_files": desktop, "opt_pi_installer_paths": opt, "env_files": env},
        "inputs": {"legacy_runtime_compatibility_inventory": _OUT_INV},
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit_coex("blocked", {}, ["LEGACY_RT_COEX_OUTPUT_TOO_LARGE"], warnings, wrote_file=False)
    if errors:
        return _emit_coex("blocked", body, errors, warnings, wrote_file=False)
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _emit_coex("blocked", {}, ["LEGACY_RT_COEX_WRITE_FAILED"], warnings, wrote_file=False)
    return _emit_coex(coex_status, body, [], warnings, wrote_file=True)


def _emit_coex(
    status: str, body: dict[str, Any], errors: list[str], warnings: list[str], *, wrote_file: bool
) -> dict[str, Any]:
    return {
        "legacy_runtime_coexistence_analysis_status": status,
        "legacy_runtime_coexistence_analysis_file_path": _OUT_COEX,
        "legacy_runtime_coexistence_analysis": body,
        "legacy_runtime_handoff_written": wrote_file,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_safe_legacy_runtime_migration_recommendations(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_OUT_REC, "LEGACY_RT_REC")
    if oerr or out_path is None:
        return _emit_rec("blocked", {}, [oerr or "LEGACY_RT_REC_OUTPUT_INVALID"], [], wrote_file=False)
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _emit_rec("blocked", {}, ["LEGACY_RT_REC_EXISTS_NO_OVERWRITE"], [], wrote_file=False)

    inv_body, ierr = _load_json_handoff(_OUT_INV, "RTINV")
    coex, cerr = _load_json_handoff(_OUT_COEX, "COEX")
    errors: list[str] = []
    warnings: list[str] = []
    if ierr or not isinstance(inv_body, dict):
        errors.append(str(ierr or "LEGACY_RT_REC_INVENTORY_MISSING"))
    if cerr or not isinstance(coex, dict):
        errors.append(str(cerr or "LEGACY_RT_REC_COEXISTENCE_MISSING"))

    recs: list[dict[str, Any]] = []
    cats = inv_body.get("categories") if isinstance(inv_body, dict) else {}
    bucket_keys = (
        "legacy_appdata",
        "local_storage_keys",
        "desktop_files",
        "service_files",
        "env_files",
        "opt_pi_installer_paths",
        "logs",
        "configs",
        "backup_paths",
    )
    has_signals = isinstance(cats, dict) and sum(len(cats.get(k) or []) for k in bucket_keys) > 0
    if isinstance(cats, dict) and has_signals:
        if cats.get("desktop_files"):
            recs.append(
                {
                    "id": "desktop_hide_not_delete",
                    "action": "advisory",
                    "summary": "Desktop-Dateien mit Legacy-Bezug voruebergehend deaktivieren (Hidden/NoDisplay) statt loeschen.",
                }
            )
        if cats.get("env_files"):
            recs.append(
                {
                    "id": "env_readonly_archive",
                    "action": "advisory",
                    "summary": "Alte ENV-Dateien read-only setzen oder archivieren; keine aktive Sourcing-Kette zu PI_INSTALLER_.",
                }
            )
        if cats.get("configs"):
            recs.append(
                {
                    "id": "config_archive",
                    "action": "advisory",
                    "summary": "Legacy-Config in ein Archiv unter Evidence verschieben (manuell), Quellsystem unangetastet lassen bis Review.",
                }
            )
        if cats.get("local_storage_keys"):
            recs.append(
                {
                    "id": "local_storage_migration",
                    "action": "advisory",
                    "summary": "LocalStorage-Schluessel dokumentiert migrieren; keine automatische Browser-Loeschung.",
                }
            )
        if cats.get("service_files"):
            recs.append(
                {
                    "id": "systemd_disable_not_delete",
                    "action": "advisory",
                    "summary": "Legacy-Units mit systemctl disable (ohne delete) stufenweise abloesen — nur nach Operator-Freigabe.",
                }
            )
        if cats.get("opt_pi_installer_paths"):
            recs.append(
                {
                    "id": "opt_path_migration",
                    "action": "advisory",
                    "summary": "Nach Daten-Backup /opt/pi-installer-Inhalt pruefen; Umzug nach /opt/setuphelfer nur manuell.",
                }
            )
        if cats.get("backup_paths"):
            recs.append(
                {
                    "id": "backup_target_migration",
                    "action": "advisory",
                    "summary": "Backup-Ziele auf setuphelfer-Pfade umstellen; alte Pfade in Read-only-Archiv referenzieren.",
                }
            )
        if cats.get("logs"):
            recs.append(
                {
                    "id": "log_path_separation",
                    "action": "advisory",
                    "summary": "Log-Pfade von Legacy und Setuphelfer trennen; Rotation nur nach Review.",
                }
            )
        recs.append(
            {
                "id": "alias_forwarding",
                "action": "advisory",
                "summary": "PI_INSTALLER_-Alias nur ueber compatibility_aliases.json und dokumentierte Umleitung halten.",
            }
        )
    else:
        recs.append(
            {
                "id": "baseline_no_legacy_handoff_signals",
                "action": "informational",
                "summary": "Keine klassifizierten Legacy-Runtime-Signale im Kompatibilitaets-Inventar-Handoff.",
            }
        )

    coex_status = str(coex.get("coexistence_status") or "") if isinstance(coex, dict) else ""
    rec_status = "ok"
    if errors:
        rec_status = "blocked"
    elif coex_status == "blocked":
        rec_status = "blocked"
    elif coex_status == "review_required" or has_signals:
        rec_status = "review_required"

    body: dict[str, Any] = {
        "legacy_runtime_safe_migration_recommendations_schema_version": 1,
        "strict_mode": "legacy_runtime_safe_migration_recommendations",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "recommendations_status": rec_status,
        "recommendations": recs,
        "disclaimer": "Nur Empfehlungen — keine automatische Migration, kein Loeschen, kein systemctl aus diesem Runner.",
        "inputs": {
            "legacy_runtime_compatibility_inventory": _OUT_INV,
            "legacy_runtime_coexistence_analysis": _OUT_COEX,
        },
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit_rec("blocked", {}, ["LEGACY_RT_REC_OUTPUT_TOO_LARGE"], warnings, wrote_file=False)
    if errors:
        return _emit_rec("blocked", body, errors, warnings, wrote_file=False)
    if rec_status == "blocked":
        return _emit_rec("blocked", body, ["LEGACY_RT_REC_COEXISTENCE_BLOCKED"], warnings, wrote_file=False)
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _emit_rec("blocked", {}, ["LEGACY_RT_REC_WRITE_FAILED"], warnings, wrote_file=False)
    return _emit_rec(rec_status, body, [], warnings, wrote_file=True)


def _emit_rec(
    status: str, body: dict[str, Any], errors: list[str], warnings: list[str], *, wrote_file: bool
) -> dict[str, Any]:
    return {
        "legacy_runtime_safe_migration_recommendations_status": status,
        "legacy_runtime_safe_migration_recommendations_file_path": _OUT_REC,
        "legacy_runtime_safe_migration_recommendations": body,
        "legacy_runtime_handoff_written": wrote_file,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_legacy_upgrade_path_matrix(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_OUT_MATRIX, "LEGACY_RT_MATRIX")
    if oerr or out_path is None:
        return _emit_matrix("blocked", {}, [oerr or "LEGACY_RT_MATRIX_OUTPUT_INVALID"], [], wrote_file=False)
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _emit_matrix("blocked", {}, ["LEGACY_RT_MATRIX_EXISTS_NO_OVERWRITE"], [], wrote_file=False)

    rec_body, rerr = _load_json_handoff(_OUT_REC, "REC")
    coex, cerr = _load_json_handoff(_OUT_COEX, "COEX")
    errors: list[str] = []
    warnings: list[str] = []
    if rerr or not isinstance(rec_body, dict):
        errors.append(str(rerr or "LEGACY_RT_MATRIX_RECOMMENDATIONS_MISSING"))
    if cerr or not isinstance(coex, dict):
        warnings.append(str(cerr or "LEGACY_RT_MATRIX_COEXISTENCE_MISSING"))

    paths = [
        {
            "path_id": 1,
            "key": "pi_installer_to_setuphelfer_clean",
            "title": "pi-installer -> Setuphelfer clean migration",
            "preconditions": ["Zero-State ok", "Branding-Guard ok", "Keine high-Konflikte"],
            "risk_level": "medium",
        },
        {
            "path_id": 2,
            "key": "parallel_coexistence",
            "title": "Parallele Koexistenz",
            "preconditions": ["Nur low-Severity-Konflikte", "Getrennte Ports/Pfade dokumentiert"],
            "risk_level": "high",
        },
        {
            "path_id": 3,
            "key": "damaged_legacy_install",
            "title": "Beschaedigte Altinstallation",
            "preconditions": ["Evidence-Inventar", "Backup verifiziert"],
            "risk_level": "high",
        },
        {
            "path_id": 4,
            "key": "partial_migration",
            "title": "Teilweise Migration",
            "preconditions": ["Desktop/ENV bereits bereinigt", "Dienste noch offen"],
            "risk_level": "medium",
        },
        {
            "path_id": 5,
            "key": "setuphelfer_only",
            "title": "Setuphelfer-only",
            "preconditions": ["Keine Legacy-Signale", "Gates gruen"],
            "risk_level": "low",
        },
        {
            "path_id": 6,
            "key": "rollback_legacy",
            "title": "Rollback auf Altzustand",
            "preconditions": ["Archivierte Legacy-Configs", "Operator-Entscheid"],
            "risk_level": "medium",
        },
    ]

    coex_status = str(coex.get("coexistence_status") or "") if isinstance(coex, dict) else ""
    rec_status = str(rec_body.get("recommendations_status") or "") if isinstance(rec_body, dict) else ""
    mat_status = "ok"
    if errors:
        mat_status = "blocked"
    elif coex_status == "blocked" or rec_status == "blocked":
        mat_status = "blocked"
    elif coex_status == "review_required" or rec_status == "review_required":
        mat_status = "review_required"

    body: dict[str, Any] = {
        "legacy_upgrade_path_matrix_schema_version": 1,
        "strict_mode": "legacy_upgrade_path_matrix",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "matrix_status": mat_status,
        "upgrade_paths": paths,
        "inputs": {
            "legacy_runtime_safe_migration_recommendations": _OUT_REC,
            "legacy_runtime_coexistence_analysis": _OUT_COEX,
        },
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit_matrix("blocked", {}, ["LEGACY_RT_MATRIX_OUTPUT_TOO_LARGE"], warnings, wrote_file=False)
    if errors:
        return _emit_matrix("blocked", body, errors, warnings, wrote_file=False)
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _emit_matrix("blocked", {}, ["LEGACY_RT_MATRIX_WRITE_FAILED"], warnings, wrote_file=False)
    return _emit_matrix(mat_status, body, [], warnings, wrote_file=True)


def _emit_matrix(
    status: str, body: dict[str, Any], errors: list[str], warnings: list[str], *, wrote_file: bool
) -> dict[str, Any]:
    return {
        "legacy_upgrade_path_matrix_status": status,
        "legacy_upgrade_path_matrix_file_path": _OUT_MATRIX,
        "legacy_upgrade_path_matrix": body,
        "legacy_runtime_handoff_written": wrote_file,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
