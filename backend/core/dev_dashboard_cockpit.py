"""
Development Control Cockpit — Runtime-Gates, Safe-Test-Mode, Strukturprüfungen, KI-Prompt-Export.

Read-only. Keine Service-Restarts, keine Deployments, kein apt.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc

EXPECTED_OPT_BACKEND = "/opt/setuphelfer/backend"
GATES_DIR = "docs/evidence/release-gates"
MATRIX_PATH = "docs/roadmap/STATUS_MATRIX.md"

FORBIDDEN_ARTIFACT_PATTERNS = (
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules/",
    ".env",
    "credentials.json",
    "*.pyc",
)

DANGEROUS_TEST_OPS = (
    "backup",
    "restore",
    "verify",
    "target_path_tests",
    "hardware_tests",
    "rescue_tests",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _safe_read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        if not path.is_file():
            return None, f"missing:{path}"
        return json.loads(path.read_text(encoding="utf-8", errors="replace")), None
    except Exception as exc:  # noqa: BLE001
        return None, f"read_error:{path}:{exc}"


def _systemd_unit_state(unit: str) -> dict[str, Any]:
    out: dict[str, Any] = {"unit": unit, "is_active": None, "load_state": None, "error": None}
    try:
        proc = subprocess.run(
            ["systemctl", "is-active", unit],
            capture_output=True,
            text=True,
            timeout=1.0,
            check=False,
        )
        out["is_active"] = (proc.stdout or "").strip() or None
        if proc.returncode not in (0, 3):
            out["error"] = (proc.stderr or "").strip()[:200] or f"exit_{proc.returncode}"
    except Exception as exc:  # noqa: BLE001
        out["error"] = str(exc)[:200]
    try:
        proc2 = subprocess.run(
            ["systemctl", "show", unit, "--property=LoadState", "--value"],
            capture_output=True,
            text=True,
            timeout=1.0,
            check=False,
        )
        if proc2.returncode == 0:
            out["load_state"] = (proc2.stdout or "").strip() or None
    except Exception:
        pass
    return out


def _dpkg_setuphelfer_installed() -> dict[str, Any]:
    info: dict[str, Any] = {"checked": True, "installed": False, "packages": [], "error": None}
    try:
        proc = subprocess.run(
            ["dpkg-query", "-W", "-f=${Package}\t${Version}\n", "setuphelfer", "setuphelfer-backend"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        lines = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()]
        if lines:
            info["installed"] = True
            info["packages"] = lines[:10]
        elif proc.returncode == 0:
            info["installed"] = False
    except FileNotFoundError:
        info["checked"] = False
        info["error"] = "dpkg_query_unavailable"
    except Exception as exc:  # noqa: BLE001
        info["error"] = str(exc)[:200]
    return info


def _normalize_ampel(raw: str | None) -> str:
    s = str(raw or "").strip().lower()
    mapping = {
        "grün": "green",
        "gruen": "green",
        "green": "green",
        "gelb": "yellow",
        "yellow": "yellow",
        "rot": "red",
        "red": "red",
        "schwarz": "gray",
        "gray": "gray",
        "grey": "gray",
        "blocked": "red",
        "failed": "red",
    }
    return mapping.get(s, "unknown")


def build_runtime_gate(
    *,
    consistency: dict[str, Any],
    deploy_drift: dict[str, Any],
    runtime: dict[str, Any],
    workspace: dict[str, Any],
    install_profile: str | None,
    app_edition: str | None,
) -> dict[str, Any]:
    """Phase-0-nahe Runtime-Gate-Auswertung (read-only, kein Shell-Gate-Aufruf)."""
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    bw = consistency.get("backend_workspace_match")
    checks.append({"id": "backend_workspace_match", "ok": bw is True, "value": bw})
    if bw is False:
        blockers.append("blocked_runtime_outdated")

    dd_status = str(deploy_drift.get("status") or "unknown").lower()
    manifest_match = deploy_drift.get("manifest_match")
    checks.append({"id": "deploy_drift_status", "ok": dd_status == "green", "value": dd_status})
    if dd_status == "yellow":
        sug = deploy_drift.get("suggested_actions") or []
        if isinstance(sug, list) and "deploy_backend_files" in sug:
            blockers.append("deploy_drift_backend_files")
    if dd_status == "gray":
        blockers.append("deploy_drift_unknown")
    if manifest_match is False:
        blockers.append("manifest_mismatch")

    brp = str(runtime.get("backend_runtime_path") or "").strip().rstrip("/")
    prof = str(install_profile or "").strip().lower()
    edition = str(app_edition or "").strip().lower()
    path_ok = True
    if prof == "opt" or edition == "release":
        path_ok = brp == EXPECTED_OPT_BACKEND.rstrip("/")
    checks.append({"id": "backend_runtime_path", "ok": path_ok, "value": brp})

    svc = _systemd_unit_state("setuphelfer-backend.service")
    svc_active = svc.get("is_active") == "active"
    checks.append({"id": "setuphelfer_backend_service", "ok": svc_active, "value": svc})

    cons_st = str(consistency.get("status") or "unknown")
    checks.append({"id": "consistency_status", "ok": cons_st == "green", "value": cons_st})

    passed = not blockers and all(c.get("ok") for c in checks if c.get("ok") is not None)
    # gray drift without explicit allow → not passed
    if dd_status == "gray":
        passed = False

    status = "green" if passed else ("yellow" if cons_st == "yellow" and not blockers else "red")
    if blockers:
        status = "red"

    return {
        "status": status,
        "passed": passed,
        "checks": checks,
        "blockers": sorted(set(blockers)),
        "workspace_version": workspace.get("workspace_version"),
        "runtime_version": runtime.get("backend_project_version"),
        "deploy_drift_status": dd_status,
        "manifest_match": manifest_match,
        "service": svc,
        "phase0_hint": "./scripts/check-runtime-deploy-gate.sh",
    }


def build_safe_test_mode(runtime_gate: dict[str, Any]) -> dict[str, Any]:
    locked = not runtime_gate.get("passed")
    mode = "LOCKED" if locked else "UNLOCKED"
    return {
        "mode": mode,
        "locked": locked,
        "reason": runtime_gate.get("blockers") or [],
        "blocked_operations": list(DANGEROUS_TEST_OPS) if locked else [],
        "message_key": "devDashboard.safeTestMode.locked" if locked else "devDashboard.safeTestMode.unlocked",
    }


def build_package_gate(repo: Path) -> dict[str, Any]:
    gap_path = repo / GATES_DIR / "apt_update_delivery_gap.json"
    gap, gerr = _safe_read_json(gap_path)
    dpkg = _dpkg_setuphelfer_installed()
    runtime_root = Path("/opt/setuphelfer")
    runtime_present = False
    try:
        runtime_present = runtime_root.is_dir()
    except OSError:
        runtime_present = False

    ampel = "unknown"
    summary = None
    if isinstance(gap, dict):
        ampel = _normalize_ampel(str(gap.get("ampel") or gap.get("status") or "unknown"))
        summary = gap.get("summary")

    update_available: bool | None = None
    if isinstance(gap, dict) and gap.get("ampel") in ("rot", "red"):
        update_available = True
    elif dpkg.get("installed"):
        update_available = None

    return {
        "status": ampel if ampel != "unknown" else "yellow",
        "deb_installed": dpkg.get("installed"),
        "dpkg": dpkg,
        "runtime_tree_present": runtime_present,
        "apt_repo_documented": isinstance(gap, dict),
        "update_available": update_available,
        "requires_confirmation": True,
        "summary": summary,
        "gap_path": str(gap_path.relative_to(repo)).replace("\\", "/") if gap_path.is_file() else None,
        "warnings": [gerr] if gerr else [],
        "forbidden_actions": ["apt_install", "apt_upgrade", "automatic_package_update"],
    }


def build_tests_evidence(repo: Path) -> dict[str, Any]:
    names = (
        "test_inventory.json",
        "current_failures.json",
        "release_readiness_gate.json",
        "backup_restore_release_gate.json",
    )
    files: dict[str, Any] = {}
    warnings: list[str] = []
    for name in names:
        p = repo / GATES_DIR / name
        data, err = _safe_read_json(p)
        entry: dict[str, Any] = {"path": str(p.relative_to(repo)).replace("\\", "/"), "exists": p.is_file()}
        if err:
            warnings.append(err)
            entry["status"] = "unknown"
        elif isinstance(data, dict):
            entry["status"] = "ok"
            entry["ampel"] = _normalize_ampel(str(data.get("ampel") or data.get("overall_status") or ""))
            entry["evidence_complete"] = data.get("evidence_complete")
            entry["id"] = data.get("id")
            if name == "current_failures.json":
                summ = data.get("summary") or {}
                entry["pytest_failed"] = summ.get("failed")
                entry["pytest_passed"] = summ.get("passed")
        else:
            entry["status"] = "unknown"
        files[name] = entry

    release_only_gates = frozenset(
        {"release_readiness_gate.json", "backup_restore_release_gate.json"},
    )
    overall = "green"
    if any(files[n].get("ampel") == "red" for n in names if files.get(n, {}).get("exists")):
        overall = "red"
    elif any(files[n].get("evidence_complete") is False for n in names if files.get(n, {}).get("exists")):
        overall = "yellow"

    # BR-001/Release-Gates rot ist erwartet — pytest/Inventory ok → nicht pauschal "rot" aggregieren.
    if overall == "red":
        red_names = [n for n in names if files.get(n, {}).get("ampel") == "red"]
        if red_names and all(n in release_only_gates for n in red_names):
            inv = files.get("test_inventory.json") or {}
            cf = files.get("current_failures.json") or {}
            hygiene_ok = inv.get("ampel") in ("green", "yellow", "gray") and cf.get("ampel") == "green"
            incomplete_non_release = any(
                files[n].get("evidence_complete") is False
                for n in names
                if n not in release_only_gates and files.get(n, {}).get("exists")
            )
            if hygiene_ok and not incomplete_non_release:
                overall = "yellow"

    return {"status": overall, "files": files, "warnings": warnings}


def _parse_status_matrix(repo: Path) -> tuple[list[dict[str, Any]], list[str]]:
    path = repo / MATRIX_PATH
    warns: list[str] = []
    items: list[dict[str, Any]] = []
    if not path.is_file():
        warns.append(f"missing:{MATRIX_PATH}")
        return items, warns
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        warns.append(f"read_error:{exc}")
        return items, warns

    row_re = re.compile(r"^\|\s*\*\*(.+?)\*\*\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")
    for line in text.splitlines():
        m = row_re.match(line.strip())
        if not m:
            continue
        title, ampel_raw, kurz, evidence = m.group(1), m.group(2), m.group(3), m.group(4)
        ampel = _normalize_ampel(ampel_raw.strip())
        category = "blocked"
        if ampel == "green":
            category = "created"
        elif ampel == "yellow":
            category = "in_progress"
        elif ampel in ("red", "unknown"):
            if "blocked" in kurz.lower() or "failed" in kurz.lower() or "rot" in ampel_raw.lower():
                category = "blocked"
            else:
                category = "planned"
        elif ampel == "gray":
            category = "planned"

        items.append(
            {
                "title": title.strip(),
                "status": ampel,
                "category": category,
                "source": MATRIX_PATH,
                "summary": kurz.strip()[:400],
                "evidence_refs": [x.strip() for x in re.split(r"[,`]", evidence) if x.strip() and "/" in x][:8],
                "last_updated": None,
                "hints": [],
            }
        )
    return items, warns


def build_roadmap(repo: Path, *, dashboard_context: dict[str, Any] | None = None) -> dict[str, Any]:
    from core.dev_dashboard_roadmap import build_dashboard_roadmap

    roadmap = build_dashboard_roadmap(repo_root=repo, dashboard_context=dashboard_context)
    if isinstance(roadmap, dict) and roadmap:
        return roadmap
    return {
        "status": "review_required",
        "tabs": {"created": [], "in_progress": [], "planned": [], "blocked": []},
        "counts": {"created": 0, "in_progress": 0, "planned": 0, "blocked": 0},
        "changed_to_green": {
            "available": False,
            "message": "Keine belastbare Änderungshistorie vorhanden",
            "items": [],
        },
        "green_without_evidence": [],
        "missing_matrix_entries": [],
        "warnings": ["roadmap_registry_unavailable"],
    }


def _git_hygiene(repo: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    detail: dict[str, Any] = {
        "dirty_count": None,
        "untracked_count": None,
        "forbidden_matches": [],
        "add_all_risk": False,
    }
    try:
        st = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        if st.returncode == 0:
            lines = [ln for ln in (st.stdout or "").splitlines() if ln.strip()]
            detail["dirty_count"] = len(lines)
            untracked = [ln for ln in lines if ln.startswith("??")]
            detail["untracked_count"] = len(untracked)
            if len(untracked) > 50:
                detail["add_all_risk"] = True
                findings.append(
                    {
                        "severity": "warning",
                        "id": "git_add_all_risk",
                        "message": f"Viele untracked Dateien ({len(untracked)}) — git add -A vermeiden",
                    }
                )
            for ln in lines:
                path_part = ln[3:].strip().split(" -> ")[-1]
                for pat in FORBIDDEN_ARTIFACT_PATTERNS:
                    if pat.rstrip("/") in path_part or path_part.endswith(".pyc"):
                        detail["forbidden_matches"].append(path_part)
                        findings.append(
                            {
                                "severity": "critical",
                                "id": "forbidden_artifact",
                                "message": f"Verbotenes Artefakt in Git-Status: {path_part}",
                                "path": path_part,
                            }
                        )
                        break
    except Exception as exc:  # noqa: BLE001
        detail["error"] = str(exc)[:200]
    return detail, findings


def build_structure_health(repo: Path, dashboard: dict[str, Any]) -> dict[str, Any]:
    critical: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    actions: list[str] = []

    git_h, git_findings = _git_hygiene(repo)
    critical.extend([f for f in git_findings if f.get("severity") == "critical"])
    warnings.extend([f for f in git_findings if f.get("severity") == "warning"])

    rg = dashboard.get("runtime_gate") or {}
    if not rg.get("passed"):
        critical.append(
            {
                "severity": "critical",
                "id": "runtime_gate_failed",
                "message": "Runtime-Gate nicht bestanden — Phase-0 blockiert",
                "blockers": rg.get("blockers"),
            }
        )
        actions.append("Führe ./scripts/check-runtime-deploy-gate.sh aus und behebe Drift/Version")

    roadmap = dashboard.get("roadmap") or {}
    for title in roadmap.get("green_without_evidence") or []:
        warnings.append(
            {
                "severity": "warning",
                "id": "green_without_evidence",
                "message": f"Matrix/Modul grün ohne Evidence-Verweis: {title}",
            }
        )

    te = dashboard.get("tests_evidence") or {}
    for fname, meta in (te.get("files") or {}).items():
        if isinstance(meta, dict) and meta.get("evidence_complete") is False:
            warnings.append(
                {
                    "severity": "warning",
                    "id": "evidence_incomplete",
                    "message": f"Evidence unvollständig: {fname}",
                }
            )
    if rg.get("passed"):
        br_gate = (te.get("files") or {}).get("backup_restore_release_gate.json") or {}
        if br_gate.get("ampel") == "red":
            warnings.append(
                {
                    "severity": "warning",
                    "id": "br001_offline_release_blocked",
                    "message": "BR-001-OFFLINE (Rettungsstick) rot — Release-Gate; keine Live-Desktop-BR-001-Retries als Gate",
                }
            )

    score = 100
    score -= len(critical) * 25
    score -= len(warnings) * 8
    score = max(0, min(100, score))

    if critical:
        status = "red"
    elif warnings:
        status = "yellow"
    else:
        status = "green"

    return {
        "status": status,
        "score": score,
        "critical_findings": critical,
        "warnings": warnings,
        "recommended_next_actions": actions[:12],
        "git_hygiene": git_h,
        "docs_consistency": {"matrix_exists": (repo / MATRIX_PATH).is_file()},
        "packaging_consistency": {
            "deploy_drift_status": (dashboard.get("deploy_drift") or {}).get("status"),
        },
    }


def build_prompt_findings(repo: Path, dashboard: dict[str, Any]) -> dict[str, Any]:
    sh = dashboard.get("structure_health") or {}
    rg = dashboard.get("runtime_gate") or {}
    stm = dashboard.get("safe_test_mode") or {}

    findings: list[dict[str, Any]] = []
    for item in sh.get("critical_findings") or []:
        findings.append({**item, "priority": "P0"})
    for item in sh.get("warnings") or []:
        findings.append({**item, "priority": "P1"})

    affected_files: list[str] = []
    dd = dashboard.get("deploy_drift") or {}
    for row in dd.get("checked_files") or []:
        if isinstance(row, dict) and row.get("matches") is False:
            rel = row.get("relative_path")
            if rel:
                affected_files.append(str(rel))

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "findings": findings,
        "affected_files": sorted(set(affected_files))[:40],
        "risks": list(rg.get("blockers") or []),
        "priorities": sorted({f.get("priority") for f in findings if f.get("priority")}),
        "forbidden_actions": list(stm.get("blocked_operations") or []) + ["apt_install", "apt_upgrade", "git_add_all", "automatic_deploy"],
        "runtime_gate_passed": rg.get("passed"),
        "safe_test_mode": stm.get("mode"),
    }


def build_cursor_meta_prompt(repo: Path, findings_payload: dict[str, Any]) -> dict[str, Any]:
    lines = [
        "# Setuphelfer Development Control Cockpit — Cursor Meta-Prompt",
        "",
        "## Kontext",
        f"Repository: {repo}",
        f"Generiert: {findings_payload.get('generated_at')}",
        "",
        "## Verbotene Aktionen (STRICT)",
    ]
    for act in findings_payload.get("forbidden_actions") or []:
        lines.append(f"- {act}")
    lines.append("")
    lines.append("## Runtime / Safe Test Mode")
    lines.append(f"- runtime_gate_passed: {findings_payload.get('runtime_gate_passed')}")
    lines.append(f"- safe_test_mode: {findings_payload.get('safe_test_mode')}")
    lines.append("")
    lines.append("## Findings (priorisiert)")
    for f in findings_payload.get("findings") or []:
        lines.append(f"- [{f.get('priority', '?')}] {f.get('id')}: {f.get('message')}")
    lines.append("")
    lines.append("## Betroffene Dateien")
    for p in findings_payload.get("affected_files") or []:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("## Recommended Cursor Work Order (Core Recovery Test Return)")
    if findings_payload.get("runtime_gate_passed"):
        lines.extend(
            [
                "1. Evidence/Release-Gates konsistent halten (kein Fake-Grün für BR-001)",
                "2. CI/pytest lokal und remote abgleichen (current_failures, test_inventory)",
                "3. BR-001: externes Backup auf freigegebenem Medium — außerhalb Cockpit",
                "4. Verify gegen echtes Archiv (nach BR-001)",
                "5. Restore Preview / Sandbox",
                "6. Hardware E2E (nach Gate + Evidence)",
                "7. Boot-/Service-Recovery",
                "8. Rescue-Stick-Ausbau erst danach",
            ]
        )
    else:
        lines.extend(
            [
                "1. ./scripts/check-runtime-deploy-gate.sh (Exit 0)",
                "2. Deploy/Workspace-Drop-in — keine Runtime-Tests vor grünem Gate",
            ]
        )
    lines.append("")
    lines.append("## Gewünschtes Cursor-Format")
    lines.append("- Nur fokussierte Änderungen; keine git add -A")
    lines.append("- Phase 0: check-runtime-deploy-gate.sh vor Runtime-Tests")
    lines.append("- Abschlussbericht bei Gate-Fehler: blocked_runtime_outdated")
    lines.append("- BR-001-OFFLINE (Rettungsstick) = Release-Gate; BR-001-LIVE experimentell, keine Live-Gate-Retries")

    body = "\n".join(lines)
    return {
        "format": "cursor_meta_prompt_v1",
        "prompt": body,
        "findings": findings_payload,
    }


def build_br001_gates(repo: Path) -> dict[str, Any]:
    """BR-001-LIVE (experimentell) vs. BR-001-OFFLINE (Release-Gate) — read-only aus Gate-JSON."""
    gate_path = repo / GATES_DIR / "backup_restore_release_gate.json"
    gate, _err = _safe_read_json(gate_path)
    nested = (gate or {}).get("br001_gates") if isinstance(gate, dict) else None
    if isinstance(nested, dict) and nested:
        live = nested.get("live") or {}
        offline = nested.get("offline") or {}
        return {
            "primary_release_gate": str(gate.get("release_gate_primary") or "BR-001-OFFLINE"),
            "live": {
                "id": str(live.get("id") or "BR-001-LIVE"),
                "release_gate": bool(live.get("release_gate", False)),
                "role": str(live.get("role") or "experimental"),
                "status": _normalize_ampel(str(live.get("ampel") or "red")),
                "summary": live.get("summary"),
                "policy": live.get("policy"),
            },
            "offline": {
                "id": str(offline.get("id") or "BR-001-OFFLINE"),
                "release_gate": bool(offline.get("release_gate", True)),
                "role": str(offline.get("role") or "release_gate"),
                "status": _normalize_ampel(str(offline.get("ampel") or "red")),
                "summary": offline.get("summary"),
            },
            "gate_path": str(gate_path.relative_to(repo)).replace("\\", "/"),
            "pivot_evidence": "docs/evidence/release-gates/BR-001_offline_gate_pivot_2026-05-20.md",
        }
    return {
        "primary_release_gate": "BR-001-OFFLINE",
        "live": {
            "id": "BR-001-LIVE",
            "release_gate": False,
            "role": "experimental",
            "status": "red",
            "summary": "Live Full-Root kein Release-Gate",
            "policy": "no_live_desktop_retry_as_release_gate",
        },
        "offline": {
            "id": "BR-001-OFFLINE",
            "release_gate": True,
            "role": "release_gate",
            "status": "red",
            "summary": "Rettungsstick Offline-Full-Backup",
        },
        "gate_path": str(gate_path.relative_to(repo)).replace("\\", "/"),
        "pivot_evidence": "docs/evidence/release-gates/BR-001_offline_gate_pivot_2026-05-20.md",
    }


def build_rescue_stick_board(repo: Path) -> dict[str, Any]:
    """Kompakte RS-/BR-001-OFFLINE-Übersicht für Development Cockpit."""
    inv_path = repo / "docs/evidence/runtime-results/handoff/rescue_stick_component_inventory.json"
    inv, _ = _safe_read_json(inv_path)
    counts = (inv or {}).get("counts") if isinstance(inv, dict) else {}
    components = (inv or {}).get("components") if isinstance(inv, dict) else []
    missing_mvp = [
        str(c.get("component_id"))
        for c in components
        if isinstance(c, dict) and c.get("status") == "missing" and c.get("required_for_mvp")
    ]
    rs_matrix = repo / "docs/testing/RESCUE_STICK_TEST_MATRIX.md"
    br001 = build_br001_gates(repo)
    return {
        "br001_offline_status": (br001.get("offline") or {}).get("status"),
        "br001_live_status": (br001.get("live") or {}).get("status"),
        "br001_live_release_gate": (br001.get("live") or {}).get("release_gate"),
        "component_inventory_path": str(inv_path.relative_to(repo)).replace("\\", "/") if inv_path.is_file() else None,
        "component_counts": counts,
        "missing_mvp_component_ids": missing_mvp[:12],
        "rs_matrix_exists": rs_matrix.is_file(),
        "rs_tests_all_red": True,
        "notes": "Release-Gate nur BR-001-OFFLINE; Live-Desktop-Retries nicht als Gate.",
    }


def enrich_dashboard_cockpit(body: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    """Erweitert build_dashboard_status-Body um Cockpit-Felder."""
    repo = repo_root or _repo_root()
    consistency = body.get("consistency") or {}
    deploy_drift = body.get("deploy_drift") or {}
    runtime = body.get("runtime") or {}
    workspace = body.get("workspace") or {}

    runtime_gate = build_runtime_gate(
        consistency=consistency,
        deploy_drift=deploy_drift,
        runtime=runtime,
        workspace=workspace,
        install_profile=body.get("install_profile"),
        app_edition=body.get("app_edition"),
    )
    safe_test_mode = build_safe_test_mode(runtime_gate)
    package_gate = build_package_gate(repo)
    tests_evidence = build_tests_evidence(repo)
    roadmap = build_roadmap(repo, dashboard_context=body)

    body["runtime_gate"] = runtime_gate
    body["safe_test_mode"] = safe_test_mode
    body["package_gate"] = package_gate
    body["tests_evidence"] = tests_evidence
    body["roadmap"] = roadmap
    body["updated_at"] = datetime.now(tz=UTC).isoformat()

    structure_health = build_structure_health(repo, body)
    body["structure_health"] = structure_health
    body["br001_gates"] = build_br001_gates(repo)
    body["rescue_stick_board"] = build_rescue_stick_board(repo)
    offline_st = str((body["br001_gates"].get("offline") or {}).get("status") or "red")
    body["release_gate_primary"] = body["br001_gates"].get("primary_release_gate")
    body["release_gate_br001_offline_status"] = offline_st
    return body
