"""Read-only diagnostic export for local lab / QEMU / fleet sessions (redacted)."""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.fleet_session_state import (
    FleetSessionError,
    fleet_sessions_enabled,
    get_fleet_session,
    utc_now_iso,
)

UTC = timezone.utc

QEMU_EVIDENCE_REL = Path("docs/evidence/runtime-results/rescue/qemu")
SERIAL_HEAD_LINES = 80
SERIAL_TAIL_LINES = 160
MAX_LINE_CHARS = 2000

SHARING_WARNING = "Internal development data. Do not publish."

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("api_key", re.compile(r"(?i)(api[_-]?key|x-api-key)\s*[:=]\s*['\"]?\S+", re.M)),
    ("bearer_token", re.compile(r"(?i)bearer\s+[a-z0-9._\-]+", re.M)),
    ("private_key", re.compile(r"-----BEGIN[A-Z ]*PRIVATE KEY-----[\s\S]*?-----END[A-Z ]*PRIVATE KEY-----", re.M)),
    ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("generic_token", re.compile(r"(?i)(token|secret|password)\s*[:=]\s*['\"]?\S{8,}", re.M)),
]

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


class DevDiagnosticExportError(Exception):
    def __init__(self, code: str, errors: list[str] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.errors = errors or [code]


def dev_diagnostics_enabled() -> bool:
    try:
        from core.install_profile import get_install_profile_state

        return get_install_profile_state().dev_diagnostics_enabled
    except Exception:
        pass
    env = os.environ.get("SETUPHELFER_DEV_DIAGNOSTICS_ENABLED", "").strip().lower()
    if env in {"1", "true", "yes", "on"}:
        return True
    if env in {"0", "false", "no", "off"}:
        return False
    if os.environ.get("PI_INSTALLER_DEV", "").strip().lower() in {"1", "true", "yes"}:
        return True
    return fleet_sessions_enabled()


def _repo_root(repo_root: Path | None = None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    env = os.environ.get("SETUPHELFER_REPO_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent.parent


def _read_json_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file() or path.is_symlink():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _read_text_excerpt(path: Path, *, head_lines: int, tail_lines: int) -> tuple[str, str, int]:
    if not path.is_file() or path.is_symlink():
        return "", "", 0
    try:
        size = path.stat().st_size
        if size == 0:
            return "", "", 0
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "", "", 0
    lines = text.splitlines()
    head = "\n".join(lines[:head_lines]) if head_lines > 0 else ""
    if tail_lines > 0:
        tail = "\n".join(lines[-tail_lines:]) if len(lines) > (head_lines if head_lines > 0 else 0) else ""
    else:
        tail = ""
    return head, tail, size


def _truncate_line(text: str) -> str:
    if len(text) <= MAX_LINE_CHARS:
        return text
    return text[:MAX_LINE_CHARS] + "…[truncated]"


def redact_diagnostic_export(export: dict[str, Any]) -> dict[str, Any]:
    """Deep-copy redact secrets and mask emails in string values."""

    rules: list[str] = []
    secrets_detected = False
    warnings: list[str] = []

    def scrub_str(s: str) -> str:
        nonlocal secrets_detected
        out = s
        for name, pat in SECRET_PATTERNS:
            if pat.search(out):
                secrets_detected = True
                rules.append(name)
                out = pat.sub(f"[REDACTED:{name}]", out)
        if EMAIL_PATTERN.search(out):
            rules.append("email_masked")
            out = EMAIL_PATTERN.sub("[REDACTED:email]", out)
        return _truncate_line(out)

    def walk(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: walk(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [walk(v) for v in obj]
        if isinstance(obj, str):
            return scrub_str(obj)
        return obj

    redacted = walk(json.loads(json.dumps(export, default=str)))
    redacted.setdefault("redaction", {})
    redacted["redaction"] = {
        "rules_applied": sorted(set(rules)),
        "secrets_detected": secrets_detected,
        "warnings": warnings,
    }
    redacted["redacted"] = True
    return redacted


def collect_evidence_index(
    run_id: str,
    session_id: str | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    repo = _repo_root(repo_root)
    run_dir = repo / QEMU_EVIDENCE_REL / run_id
    paths: list[dict[str, Any]] = []
    missing: list[str] = []

    expected = [
        "qemu_autopilot_result.json",
        "qemu-serial.log",
        "qemu-gtk-stderr.log",
        "qemu-gtk-stdout.log",
        "dev_server_summary_before.json",
        "dev_server_summary_after.json",
        "dev_server_reports_after.json",
        "qemu_gtk_pid.txt",
    ]
    for name in expected:
        rel = str(QEMU_EVIDENCE_REL / run_id / name)
        full = run_dir / name
        if full.is_file() and not full.is_symlink():
            try:
                paths.append({"path": rel, "size_bytes": full.stat().st_size, "exists": True})
            except OSError:
                missing.append(rel)
        else:
            missing.append(rel)

    bundle_available = run_dir.is_dir() and bool(paths)
    return {
        "run_id": run_id,
        "session_id": session_id,
        "run_dir": str(QEMU_EVIDENCE_REL / run_id),
        "paths": paths,
        "missing_paths": missing,
        "bundle_available": bundle_available,
    }


def _runtime_snapshot(repo: Path) -> dict[str, Any]:
    version_block: dict[str, Any] = {}
    vf = repo / "config" / "version.json"
    if vf.is_file():
        vdata = _read_json_file(vf)
        if vdata:
            version_block = {
                "project_version": vdata.get("project_version"),
                "build_id": vdata.get("build_id"),
            }
    return {
        "gate_status": "not_re_evaluated_in_export",
        "backend_active": None,
        "api_version": version_block,
        "openapi_fleet_paths_visible": fleet_sessions_enabled(),
    }


def _load_autopilot_result(run_dir: Path) -> dict[str, Any]:
    data = _read_json_file(run_dir / "qemu_autopilot_result.json")
    return data or {}


def _devserver_ingest_from_evidence(run_dir: Path, autopilot: dict[str, Any]) -> dict[str, Any]:
    before = _read_json_file(run_dir / "dev_server_summary_before.json") or {}
    after = _read_json_file(run_dir / "dev_server_summary_after.json") or {}
    report_new = bool(autopilot.get("dev_server_report_new"))
    if not report_new:
        rb = before.get("reports_last_24h")
        ra = after.get("reports_last_24h")
        if isinstance(rb, int) and isinstance(ra, int):
            report_new = ra > rb

    guest_raw = autopilot.get("guest_smoke_from_serial")
    guest_found = guest_raw is not None and guest_raw != {}

    latest: list[dict[str, Any]] = []
    for src in (after, before):
        lf = src.get("latest_findings")
        if isinstance(lf, list) and lf:
            latest = [x for x in lf[:5] if isinstance(x, dict)]
            break

    return {
        "report_new": report_new,
        "guest_found": guest_found,
        "node_created": False,
        "node_updated": False,
        "reports_last_24h": after.get("reports_last_24h"),
        "node_count": after.get("node_count"),
        "latest_findings": latest,
    }


def classify_qemu_smoke_failure(export: dict[str, Any]) -> dict[str, Any]:
    qemu = export.get("qemu_smoke") or {}
    ingest = export.get("devserver_ingest") or {}
    fleet = export.get("fleet_session") or {}
    serial_size = qemu.get("serial_size_bytes")
    if serial_size is None:
        serial_size = (export.get("fleet_session") or {}).get("serial", {}).get("size_bytes", 0)

    report_new = ingest.get("report_new", False)
    guest_found = ingest.get("guest_found", False)
    autopilot_exit = qemu.get("qemu_exit_code")
    fleet_exit = (fleet.get("qemu") or {}).get("exit_code")

    primary = "inconclusive_evidence_missing"
    secondary: list[str] = []
    confidence = "medium"

    serial_empty = serial_size == 0
    head = (qemu.get("serial_excerpt_head") or "").strip()
    tail = (qemu.get("serial_excerpt_tail") or "").strip()
    serial_text = f"{head}\n{tail}".lower()

    if serial_empty:
        primary = "serial_empty_boot_unknown"
        confidence = "high"
        secondary.append("agent_not_observed")
        secondary.append("network_not_observed")
    elif re.search(r"module not found.*devserver_agent|modulenotfounderror", serial_text, re.I):
        primary = "module_path_error_devserver_agent"
        confidence = "high"
    elif re.search(r"setuphelfer_autopilot_start", serial_text, re.I):
        if not report_new:
            primary = "agent_started_network_failed" if re.search(
                r"curl|connection refused|timed out|10\.0\.2\.2", serial_text, re.I
            ) else "devserver_ingest_missing"
            confidence = "medium"
    elif not report_new and not guest_found:
        primary = "qemu_wrapper_ok_guest_no_report"
        confidence = "medium"

    if not report_new and "devserver_ingest_missing" not in secondary:
        secondary.append("devserver_ingest_missing")

    if fleet.get("finished_at") and fleet_exit is None and autopilot_exit == 124:
        secondary.append("fleet_finish_missing")

    if primary == "inconclusive_evidence_missing" and autopilot_exit == 124 and serial_empty:
        primary = "serial_empty_boot_unknown"
        confidence = "high"

    secondary = list(dict.fromkeys(secondary))
    return {"primary": primary, "secondary": secondary, "confidence": confidence}


def _export_shell(
    *,
    run_id: str,
    session_id: str | None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    return {
        "export_id": f"diag-{run_id}-{uuid.uuid4().hex[:12]}",
        "created_at": utc_now_iso(),
        "redacted": False,
        "scope": "local_lab_only",
        "sharing_warning": SHARING_WARNING,
        "run_id": run_id,
        "session_id": session_id or f"fleet-{run_id}",
        "classification": {"primary": "inconclusive_evidence_missing", "secondary": [], "confidence": "low"},
        "runtime": _runtime_snapshot(_repo_root(repo_root)),
        "fleet_session": {},
        "qemu_smoke": {},
        "devserver_ingest": {},
        "evidence": {},
        "redaction": {"rules_applied": [], "secrets_detected": False, "warnings": []},
    }


def build_qemu_smoke_diagnostic_export(
    run_id: str,
    *,
    redacted: bool = True,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    rid = run_id.strip()
    if not rid or ".." in rid or "/" in rid or "\\" in rid:
        raise DevDiagnosticExportError("DEV_DIAGNOSTIC_NOT_FOUND", ["invalid_run_id"])

    repo = _repo_root(repo_root)
    run_dir = repo / QEMU_EVIDENCE_REL / rid
    session_id = f"fleet-{rid}"
    export = _export_shell(run_id=rid, session_id=session_id, repo_root=repo)

    try:
        fleet_resp = get_fleet_session(session_id, repo_root=repo)
        export["fleet_session"] = fleet_resp.get("session") or {}
    except FleetSessionError:
        export["fleet_session"] = {"session_id": session_id, "status": "not_found_in_registry"}

    autopilot = _load_autopilot_result(run_dir)
    serial_path = run_dir / "qemu-serial.log"
    head, tail, serial_size = _read_text_excerpt(
        serial_path, head_lines=SERIAL_HEAD_LINES, tail_lines=SERIAL_TAIL_LINES
    )
    stderr_path = run_dir / "qemu-gtk-stderr.log"
    _, stderr_tail, _ = _read_text_excerpt(stderr_path, head_lines=0, tail_lines=20)

    proxy_bind = ""
    if autopilot.get("lab_proxy_enabled"):
        proxy_bind = "0.0.0.0"
    host_url = str(autopilot.get("host_dev_server_url") or "")
    proxy_port = 8001 if ":8001" in host_url else None

    export["qemu_smoke"] = {
        "autopilot_result": autopilot,
        "qemu_exit_code": autopilot.get("qemu_exit_code"),
        "timeout_seconds": (export.get("fleet_session") or {}).get("qemu", {}).get("timeout_seconds"),
        "kvm_enabled": (export.get("fleet_session") or {}).get("host", {}).get("kvm_enabled"),
        "proxy_bind": proxy_bind,
        "proxy_port": proxy_port,
        "guest_url": host_url,
        "serial_size_bytes": serial_size,
        "serial_excerpt_head": head,
        "serial_excerpt_tail": tail,
        "stderr_excerpt_tail": stderr_tail,
        "status": autopilot.get("status"),
    }
    export["devserver_ingest"] = _devserver_ingest_from_evidence(run_dir, autopilot)
    export["evidence"] = collect_evidence_index(rid, session_id, repo_root=repo)

    export["classification"] = classify_qemu_smoke_failure(export)

    if redacted:
        export = redact_diagnostic_export(export)
    else:
        export["redacted"] = False

    return export


def build_fleet_session_diagnostic_export(
    session_id: str,
    *,
    redacted: bool = True,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    sid = session_id.strip()
    try:
        fleet_resp = get_fleet_session(sid, repo_root=repo_root)
    except FleetSessionError as exc:
        raise DevDiagnosticExportError("DEV_DIAGNOSTIC_NOT_FOUND", exc.errors) from exc

    session = fleet_resp.get("session") or {}
    run_id = str(session.get("run_id") or "")
    if not run_id and sid.startswith("fleet-"):
        run_id = sid[len("fleet-") :]
    if not run_id:
        raise DevDiagnosticExportError("DEV_DIAGNOSTIC_NOT_FOUND", ["run_id_missing"])

    export = build_qemu_smoke_diagnostic_export(run_id, redacted=False, repo_root=repo_root)
    export["fleet_session"] = session
    export["session_id"] = sid
    export["classification"] = classify_qemu_smoke_failure(export)
    if redacted:
        export = redact_diagnostic_export(export)
    else:
        export["redacted"] = False
    return export


def build_diagnostic_summary_text(export: dict[str, Any]) -> str:
    """Short plain-text block for clipboard (Copy Summary)."""
    clf = export.get("classification") or {}
    qemu = export.get("qemu_smoke") or {}
    ingest = export.get("devserver_ingest") or {}
    fleet = export.get("fleet_session") or {}
    lines = [
        f"Setuphelfer Lab Diagnostic — {export.get('run_id', '?')}",
        export.get("sharing_warning", SHARING_WARNING),
        "",
        f"session_id: {export.get('session_id')}",
        f"fleet_status: {fleet.get('status', '—')}",
        f"classification.primary: {clf.get('primary', '—')}",
        f"qemu_exit_code: {qemu.get('qemu_exit_code', '—')}",
        f"serial_size_bytes: {qemu.get('serial_size_bytes', '—')}",
        f"report_new: {ingest.get('report_new')}",
        f"guest_found: {ingest.get('guest_found')}",
        f"proxy: {qemu.get('guest_url', '—')} bind={qemu.get('proxy_bind') or '127.0.0.1'}",
        "",
        f"findings: {', '.join(fleet.get('findings') or []) or '—'}",
        f"evidence: {export.get('evidence', {}).get('run_dir', '—')}",
    ]
    return "\n".join(lines)


def build_markdown_diagnostic_report(export: dict[str, Any]) -> str:
    clf = export.get("classification") or {}
    qemu = export.get("qemu_smoke") or {}
    ingest = export.get("devserver_ingest") or {}
    fleet = export.get("fleet_session") or {}
    serial_size = qemu.get("serial_size_bytes", 0)

    md: list[str] = [
        "# Setuphelfer Lab Diagnostic Report",
        "",
        f"> {export.get('sharing_warning', SHARING_WARNING)}",
        "",
        "## Identification",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| export_id | `{export.get('export_id', '')}` |",
        f"| created_at | {export.get('created_at', '')} |",
        f"| run_id | `{export.get('run_id', '')}` |",
        f"| session_id | `{export.get('session_id', '')}` |",
        f"| scope | {export.get('scope', '')} |",
        f"| redacted | {export.get('redacted', True)} |",
        "",
        "## Classification",
        "",
        f"- **primary:** `{clf.get('primary', '')}`",
        f"- **secondary:** {', '.join(f'`{x}`' for x in (clf.get('secondary') or [])) or '—'}",
        f"- **confidence:** {clf.get('confidence', '')}",
        "",
        "## Fleet session",
        "",
        f"- status: `{fleet.get('status', '—')}`",
        f"- severity: `{fleet.get('severity', '—')}`",
        f"- finished_at: {fleet.get('finished_at', '—')}",
        f"- qemu.exit_code (fleet): `{((fleet.get('qemu') or {}).get('exit_code'))}`",
        f"- serial.size_bytes (fleet): `{(fleet.get('serial') or {}).get('size_bytes', '—')}`",
        "",
        "## QEMU smoke",
        "",
        f"- autopilot status: `{qemu.get('status', '—')}`",
        f"- qemu_exit_code: `{qemu.get('qemu_exit_code', '—')}`",
        f"- serial_size_bytes: `{serial_size}`",
        f"- guest_url: `{qemu.get('guest_url', '—')}`",
        f"- proxy_bind (lab): `{qemu.get('proxy_bind') or '—'}`",
        "",
        "## Devserver ingest",
        "",
        f"- report_new: **{ingest.get('report_new')}**",
        f"- guest_found: **{ingest.get('guest_found')}**",
        f"- reports_last_24h: {ingest.get('reports_last_24h', '—')}",
        "",
    ]

    if serial_size == 0:
        md.extend(["## Serial", "", "_Serial log empty (0 bytes)._", ""])
    else:
        md.extend(["## Serial excerpt (head)", "", "```", qemu.get("serial_excerpt_head", "")[:8000], "```", ""])

    ev = export.get("evidence") or {}
    if ev.get("paths"):
        md.extend(["## Evidence index", ""])
        for p in ev.get("paths") or []:
            if isinstance(p, dict):
                md.append(f"- `{p.get('path')}` ({p.get('size_bytes', 0)} B)")
        md.append("")

    missing = ev.get("missing_paths") or []
    if missing:
        md.extend(["### Missing paths", ""])
        for m in missing[:20]:
            md.append(f"- `{m}`")
        md.append("")

    return "\n".join(md)
