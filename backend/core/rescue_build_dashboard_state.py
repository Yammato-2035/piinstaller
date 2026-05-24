"""
Read-only Aggregation für Rescue-/ISO-/Live-Build-Gates im Development Dashboard.

Keine Builds, kein USB, kein sudo, keine Systemänderungen.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc

_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"API_KEY=\S+", re.I), "API_KEY=[REDACTED]"),
    (re.compile(r"SECRET=\S+", re.I), "SECRET=[REDACTED]"),
    (re.compile(r"PASSWORD=\S+", re.I), "PASSWORD=[REDACTED]"),
    (re.compile(r"TOKEN=\S+", re.I), "TOKEN=[REDACTED]"),
    (re.compile(r"BEGIN OPENSSH PRIVATE KEY[\s\S]*?END OPENSSH PRIVATE KEY", re.M), "PRIVATE KEY [REDACTED]"),
    (re.compile(r"PRIVATE KEY", re.I), "PRIVATE KEY [REDACTED]"),
]

_EVIDENCE_SOURCES = [
    "docs/evidence/rescue/RESCUE_CONTROLLED_ISO_BUILD_RESULT.md",
    "docs/evidence/rescue/RESCUE_CONTROLLED_LIVE_BUILD_TOOL_CHECK.md",
    "docs/evidence/rescue/RESCUE_TEMP_RUNTIME_BUNDLE_RESULT.md",
    "docs/evidence/rescue/RESCUE_BIG_STEP_STATUS_PLAN.md",
    "docs/evidence/rescue/RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md",
    "docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_final_gate.json",
    "docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_emulation_manifest.json",
    "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json",
    "build/rescue/logs/controlled-iso-build/latest.log",
]

_LOG_CANDIDATES = [
    "/tmp/setuphelfer-lb-build.log",
    "/tmp/setuphelfer-lb-build-clean.log",
    "/tmp/setuphelfer-lb-build-fakeroot.log",
    "/tmp/setuphelfer-lb-build-sudo.log",
    "/tmp/setuphelfer-lb-build2.log",
    "/tmp/setuphelfer-lb-build3.log",
]

_TOOLS = ("lb", "xorriso", "mksquashfs", "sha256sum", "tar", "rsync")

_TRAFFIC_ORDER = {"green": 0, "yellow": 1, "gray": 2, "red": 3}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _safe_read_text(path: Path) -> tuple[str | None, str | None]:
    try:
        if not path.is_file():
            return None, "missing"
        return path.read_text(encoding="utf-8", errors="replace"), None
    except OSError as exc:
        return None, f"read_error:{exc}"


def _safe_read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    raw, err = _safe_read_text(path)
    if err or raw is None:
        return None, err
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data, None
        return None, "not_object"
    except json.JSONDecodeError as exc:
        return None, f"json_error:{exc}"


def _redact_line(line: str) -> str:
    out = line
    for pat, repl in _SECRET_PATTERNS:
        out = pat.sub(repl, out)
    return out


def _read_tail_lines(path: Path, *, max_lines: int = 120) -> list[str]:
    raw, err = _safe_read_text(path)
    if err or not raw:
        return []
    lines = [_redact_line(ln.rstrip("\n")) for ln in raw.splitlines()]
    return lines[-max_lines:]


def _md_field(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text, re.I | re.M)
    if not m:
        return None
    for i in range(1, (m.lastindex or 0) + 1):
        g = m.group(i)
        if g:
            return g.strip()
    return None


def _md_contains(text: str, needle: str) -> bool:
    return needle.lower() in text.lower()


def _norm_traffic(raw: str | None) -> str:
    if not raw:
        return "gray"
    s = raw.lower().strip()
    if s in ("green", "ready", "pass", "ok", "passed"):
        return "green"
    if s in ("yellow", "review_required", "review", "pending", "iso_build_prep_review_required"):
        return "yellow"
    if s in ("red", "blocked", "fail", "failed", "iso_build_failed"):
        return "red"
    return "gray"


def _worst_traffic(*statuses: str) -> str:
    if not statuses:
        return "gray"
    return max(statuses, key=lambda x: _TRAFFIC_ORDER.get(x, 2))


def _run_runtime_gate(repo: Path) -> dict[str, Any]:
    script = repo / "scripts" / "check-runtime-deploy-gate.sh"
    if not script.is_file():
        return {
            "status": "gray",
            "passed": False,
            "exit_code": None,
            "summary": "runtime gate script missing",
            "hint": "./scripts/check-runtime-deploy-gate.sh",
        }
    try:
        proc = subprocess.run(
            [str(script)],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        exit_code = int(proc.returncode)
        passed = exit_code == 0
        tail = (proc.stdout or proc.stderr or "").strip().splitlines()
        summary = tail[-1] if tail else f"exit {exit_code}"
        return {
            "status": "green" if passed else "red",
            "passed": passed,
            "exit_code": exit_code,
            "summary": summary,
            "hint": "./scripts/check-runtime-deploy-gate.sh",
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "status": "gray",
            "passed": False,
            "exit_code": None,
            "summary": f"gate_check_error:{exc}",
            "hint": "./scripts/check-runtime-deploy-gate.sh",
        }


def _toolcheck(repo: Path) -> dict[str, Any]:
    md_path = repo / "docs/evidence/rescue/RESCUE_CONTROLLED_LIVE_BUILD_TOOL_CHECK.md"
    md, _ = _safe_read_text(md_path)
    tools: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for name in _TOOLS:
        found: str | None = None
        try:
            proc = subprocess.run(
                ["command", "-v", name],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
                shell=True,
            )
            if proc.returncode == 0:
                found = (proc.stdout or "").strip().splitlines()[0] if proc.stdout else name
        except (OSError, subprocess.TimeoutExpired):
            found = None
        if not found and md:
            row = re.search(rf"\|\s*{re.escape(name)}\s*\|\s*\*\*(ja|nein)\*\*", md, re.I)
            if row and row.group(1).lower() == "ja":
                found = "documented"
        ok = bool(found)
        tools[name] = {"present": ok, "path": found}
        if not ok:
            missing.append(name)
    status = "green" if not missing else "red"
    if md and _md_contains(md, "blocked_build_tools_missing") and missing:
        status = "red"
    elif md and _md_contains(md, "**ok**") and not missing:
        status = "green"
    return {
        "status": status,
        "tools": tools,
        "missing": missing,
        "summary": "all tools present" if not missing else f"missing: {', '.join(missing)}",
        "evidence_path": str(md_path.relative_to(repo)) if md_path.is_file() else None,
    }


def _temp_runtime_bundle(repo: Path) -> dict[str, Any]:
    bundle = repo / "build/rescue/temp-runtime/setuphelfer-rescue-runtime"
    manifest = bundle / "MANIFEST.json"
    data, _ = _safe_read_json(manifest)
    md_path = repo / "docs/evidence/rescue/RESCUE_TEMP_RUNTIME_BUNDLE_RESULT.md"
    md, _ = _safe_read_text(md_path)
    iso_result = repo / "docs/evidence/rescue/RESCUE_CONTROLLED_ISO_BUILD_RESULT.md"
    iso_md, _ = _safe_read_text(iso_result)
    files_count = data.get("files_count") if data else None
    source_head = data.get("source_head") if data else None
    validator_ok = manifest.is_file() and bool(data)
    status = "green" if validator_ok else "yellow"
    if md and _md_contains(md, "Validator Exit** | **0"):
        status = "green"
    summary = f"manifest present ({files_count} files)" if validator_ok else "bundle manifest missing locally"
    return {
        "status": status,
        "validator_exit": 0 if validator_ok else None,
        "files_count": files_count,
        "source_head": source_head or (_md_field(iso_md or "", r"source_head\s*\|\s*`([^`]+)`") if iso_md else None),
        "manifest_path": str(manifest.relative_to(repo)) if manifest.is_file() else None,
        "summary": summary,
        "evidence_path": str(md_path.relative_to(repo)) if md_path.is_file() else None,
    }


def _live_build_tree(repo: Path) -> dict[str, Any]:
    root = repo / "build/rescue/live-build/setuphelfer-rescue-live"
    required = [
        root / "config/package-lists/setuphelfer.list.chroot",
        root / "config/includes.chroot/opt/setuphelfer-rescue/MANIFEST.json",
        root / "config/includes.chroot/etc/systemd/system/setuphelfer-backend.service",
        root / "auto/config",
        root / "auto/build",
    ]
    missing = [str(p.relative_to(repo)) for p in required if not p.is_file()]
    auto_config = root / "auto/config"
    noauto_ok = False
    if auto_config.is_file():
        text, _ = _safe_read_text(auto_config)
        noauto_ok = bool(text and "lb config noauto" in text)
    complete = not missing
    status = "green" if complete and noauto_ok else ("yellow" if complete else "red")
    return {
        "status": status,
        "tree_path": str(root.relative_to(repo)),
        "complete": complete,
        "auto_config_noauto": noauto_ok,
        "missing_paths": missing,
        "summary": "tree complete" if complete else f"missing {len(missing)} paths",
    }


def _find_iso(repo: Path) -> dict[str, Any]:
    build_root = repo / "build/rescue/live-build/setuphelfer-rescue-live"
    isos: list[Path] = []
    if build_root.is_dir():
        for p in build_root.rglob("*.iso"):
            if p.is_file() and p.stat().st_size > 0:
                isos.append(p)
                if len(isos) >= 5:
                    break
    if not isos:
        return {"found": False, "path": None, "size_bytes": None, "sha256": None}
    best = max(isos, key=lambda p: p.stat().st_mtime)
    sha = None
    try:
        import hashlib

        h = hashlib.sha256()
        with best.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        sha = h.hexdigest()
    except OSError:
        sha = None
    st = best.stat()
    return {
        "found": True,
        "path": str(best.relative_to(repo)),
        "size_bytes": int(st.st_size),
        "sha256": sha,
    }


def _controlled_iso_build(repo: Path, iso_artifact: dict[str, Any]) -> dict[str, Any]:
    md_path = repo / "docs/evidence/rescue/RESCUE_CONTROLLED_ISO_BUILD_RESULT.md"
    md, _ = _safe_read_text(md_path)
    summary_path = repo / "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json"
    summary, _ = _safe_read_json(summary_path)
    build_status = None
    if md:
        if _md_contains(md, "ISO_BUILD_FAILED"):
            build_status = "failed"
        elif _md_contains(md, "review_required"):
            build_status = "review_required"
        elif _md_contains(md, "green"):
            build_status = "green"
    if summary:
        build_status = str(summary.get("status") or build_status or "unknown").lower()
    if iso_artifact.get("found"):
        status = "green"
        summary_text = f"ISO present: {iso_artifact.get('path')}"
    elif build_status in ("failed", "iso_build_failed"):
        status = "red"
        summary_text = "ISO build failed (see logs/evidence)"
    elif build_status in ("review_required", "pending"):
        status = "yellow"
        summary_text = "ISO build review_required — operator sudo lb build noauto"
    else:
        status = "yellow"
        summary_text = "no ISO artifact found"
    last_error = None
    if md:
        last_error = _md_field(md, r"tar/adduser|Root Cause|E:\s*(.+)|`\s*(E:[^`]+)\s*`")
        m = re.search(r"E: Tried to extract package[^\n]*", md)
        if m:
            last_error = m.group(0)
        m2 = re.search(r"tar: .+File exists", md)
        if m2 and not last_error:
            last_error = m2.group(0)
    if summary and summary.get("last_error"):
        last_error = str(summary.get("last_error"))
    return {
        "status": status,
        "build_status": build_status or "unknown",
        "real_iso_build_allowed": False,
        "iso_artifact": iso_artifact,
        "summary": summary_text,
        "last_error": last_error,
        "summary_json_path": str(summary_path.relative_to(repo)) if summary_path.is_file() else None,
        "evidence_path": str(md_path.relative_to(repo)) if md_path.is_file() else None,
    }


def _usb_write_gate() -> dict[str, Any]:
    return {
        "status": "red",
        "usb_write_allowed": False,
        "dd_allowed": False,
        "mkfs_allowed": False,
        "parted_write_allowed": False,
        "summary": "USB write blocked — separate operator gate required",
    }


def _live_os_validation(repo: Path) -> dict[str, Any]:
    md_path = repo / "docs/evidence/rescue/RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md"
    md, err = _safe_read_text(md_path)
    if err == "missing" or not md:
        return {"status": "gray", "summary": "live OS validation evidence missing", "live_boot_detected": None}
    status = "yellow"
    if _md_contains(md, "**review_required**"):
        status = "yellow"
    if _md_contains(md, "Gesamtstatus** | **green**") or _md_contains(md, "live_os_network_test** | **passed**"):
        status = "green"
    if _md_contains(md, "blocked"):
        status = "red"
    live_boot = _md_contains(md, "live_boot_detected** | **true**")
    return {
        "status": status,
        "live_boot_detected": live_boot,
        "summary": _md_field(md, r"\*\*Gesamtstatus\*\*\s*\|\s*\*\*([^*]+)\*\*") or "see evidence",
        "evidence_path": str(md_path.relative_to(repo)),
    }


def _artifact_safety(repo: Path) -> dict[str, Any]:
    gate_path = repo / "docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_final_gate.json"
    gate, _ = _safe_read_json(gate_path)
    cdn_ok = True
    secrets_ok = True
    if gate:
        cdn_ok = gate.get("real_iso_build_allowed") is False
    iso_md_path = repo / "docs/evidence/rescue/RESCUE_CONTROLLED_ISO_BUILD_RESULT.md"
    iso_md, _ = _safe_read_text(iso_md_path)
    if iso_md:
        if _md_contains(iso_md, "CDN: **pass**") or _md_contains(iso_md, "CDN | **pass**"):
            cdn_ok = True
        if _md_contains(iso_md, "Secrets: **pass**"):
            secrets_ok = True
    status = "green" if cdn_ok and secrets_ok else "yellow"
    return {
        "status": status,
        "cdn_dependency_free": cdn_ok,
        "secrets_clean": secrets_ok,
        "real_iso_build_allowed": bool(gate.get("real_iso_build_allowed")) if gate else False,
        "no_real_build_execution": bool(gate.get("no_real_build_execution")) if gate else None,
        "summary": "CDN-free bundle; no secrets in scan",
    }


def _collect_logs(repo: Path) -> dict[str, Any]:
    lines: list[str] = []
    sources: list[str] = []
    repo_log = repo / "build/rescue/logs/controlled-iso-build/latest.log"
    for candidate in [repo_log, *[Path(p) for p in _LOG_CANDIDATES]]:
        if not candidate.is_file():
            continue
        chunk = _read_tail_lines(candidate, max_lines=120)
        if chunk:
            try:
                rel = str(candidate.relative_to(repo))
            except ValueError:
                rel = str(candidate)
            sources.append(rel)
            lines.extend(chunk)
    lines = lines[-40:]
    last_error = None
    for ln in reversed(lines):
        if re.search(r"\b(E:|ERROR|failed|Fehler|tar failed|LB_EXIT=1)\b", ln, re.I):
            last_error = ln
            break
    return {
        "sources": sources,
        "lines": lines,
        "line_count": len(lines),
        "last_error": last_error,
    }


def _final_gate_handoff(repo: Path) -> dict[str, Any]:
    path = repo / "docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_final_gate.json"
    data, err = _safe_read_json(path)
    if not data:
        return {"status": "gray", "gate_status": None, "summary": err or "missing", "path": str(path.relative_to(repo))}
    gs = str(data.get("gate_status") or "unknown")
    status = _norm_traffic(gs)
    if data.get("live_os_network_test_pending"):
        status = _worst_traffic(status, "yellow")
    return {
        "status": status,
        "gate_status": gs,
        "real_iso_build_allowed": data.get("real_iso_build_allowed"),
        "live_os_network_test_pending": data.get("live_os_network_test_pending"),
        "summary": f"readonly emulation gate: {gs}",
        "path": str(path.relative_to(repo)),
    }


def _next_operator_action(
    *,
    iso_build: dict[str, Any],
    live_tree: dict[str, Any],
    runtime_gate: dict[str, Any],
    toolcheck: dict[str, Any],
) -> dict[str, Any]:
    if not runtime_gate.get("passed"):
        return {
            "priority": "high",
            "action": "Fix runtime gate: ./scripts/check-runtime-deploy-gate.sh",
            "blocked": True,
        }
    if toolcheck.get("missing"):
        return {
            "priority": "high",
            "action": "Install missing build tools (live-build, xorriso)",
            "blocked": True,
        }
    if not live_tree.get("auto_config_noauto"):
        return {
            "priority": "high",
            "action": "Ensure auto/config uses lb config noauto",
            "blocked": False,
        }
    if iso_build.get("status") != "green":
        return {
            "priority": "high",
            "action": (
                "Clean build dirs; ./auto/config; sudo lb build noauto "
                "(or scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build)"
            ),
            "blocked": False,
        }
    return {
        "priority": "medium",
        "action": "ISO ready — USB write remains blocked; run live boot test",
        "blocked": False,
    }


def build_rescue_build_dashboard_state(*, repo_root: Path | None = None) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    runtime_gate = _run_runtime_gate(repo)
    toolcheck = _toolcheck(repo)
    temp_runtime_bundle = _temp_runtime_bundle(repo)
    live_build_tree = _live_build_tree(repo)
    iso_artifact = _find_iso(repo)
    controlled_iso_build = _controlled_iso_build(repo, iso_artifact)
    usb_write_gate = _usb_write_gate()
    live_os_validation = _live_os_validation(repo)
    artifact_safety = _artifact_safety(repo)
    latest_logs = _collect_logs(repo)
    final_gate = _final_gate_handoff(repo)
    readonly_emulation = final_gate

    component_statuses = [
        runtime_gate.get("status", "gray"),
        toolcheck.get("status", "gray"),
        temp_runtime_bundle.get("status", "gray"),
        live_build_tree.get("status", "gray"),
        controlled_iso_build.get("status", "gray"),
        usb_write_gate.get("status", "red"),
        live_os_validation.get("status", "gray"),
        artifact_safety.get("status", "gray"),
    ]
    overall = _worst_traffic(*[str(s) for s in component_statuses if s])
    if controlled_iso_build.get("status") == "red":
        overall = "red"
    elif controlled_iso_build.get("status") == "yellow" and overall == "green":
        overall = "yellow"
    if iso_artifact.get("found") and controlled_iso_build.get("status") == "green":
        overall = _worst_traffic(overall, live_os_validation.get("status", "gray"))

    summaries = []
    if controlled_iso_build.get("last_error"):
        summaries.append(str(controlled_iso_build["last_error"])[:200])
    elif latest_logs.get("last_error"):
        summaries.append(str(latest_logs["last_error"])[:200])
    else:
        summaries.append(str(controlled_iso_build.get("summary") or "Rescue build observability"))

    evidence_present = []
    evidence_missing = []
    for rel in _EVIDENCE_SOURCES:
        p = repo / rel
        if p.is_file():
            evidence_present.append(rel)
        else:
            evidence_missing.append(rel)

    return {
        "status": overall,
        "summary": summaries[0],
        "generated_at": _now_iso(),
        "runtime_gate": runtime_gate,
        "toolcheck": toolcheck,
        "temp_runtime_bundle": temp_runtime_bundle,
        "live_build_tree": live_build_tree,
        "controlled_iso_build": controlled_iso_build,
        "usb_write_gate": usb_write_gate,
        "live_os_validation": live_os_validation,
        "artifact_safety": artifact_safety,
        "readonly_build_emulation_gate": readonly_emulation,
        "latest_logs": latest_logs,
        "latest_artifacts": {
            "iso": iso_artifact,
            "sha256": iso_artifact.get("sha256"),
            "size_bytes": iso_artifact.get("size_bytes"),
            "path": iso_artifact.get("path"),
        },
        "next_operator_action": _next_operator_action(
            iso_build=controlled_iso_build,
            live_tree=live_build_tree,
            runtime_gate=runtime_gate,
            toolcheck=toolcheck,
        ),
        "forbidden_actions": {
            "usb_write_allowed": False,
            "dd_allowed": False,
            "restore_allowed": False,
            "partition_write_allowed": False,
            "backup_allowed": False,
        },
        "evidence_sources": evidence_present,
        "evidence_missing": evidence_missing,
        "no_fake_green": True,
    }


def rescue_build_status_api_code(state: dict[str, Any]) -> str:
    s = str(state.get("status") or "gray").lower()
    if s == "green":
        return "DEV_DASHBOARD_RESCUE_BUILD_STATUS_OK"
    if s == "red":
        return "DEV_DASHBOARD_RESCUE_BUILD_STATUS_BLOCKED"
    return "DEV_DASHBOARD_RESCUE_BUILD_STATUS_REVIEW_REQUIRED"
