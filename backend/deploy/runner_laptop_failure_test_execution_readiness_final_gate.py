from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_RUNTIME_EVIDENCE = (_REPO_ROOT / "docs/evidence/runtime-results").resolve(strict=False)
_ROUTES = _REPO_ROOT / "backend" / "deploy" / "routes.py"
_APP = _REPO_ROOT / "backend" / "app.py"
_OUT_REL = "docs/evidence/runtime-results/handoff/laptop_failure_test_execution_readiness_gate.json"
_REPORT_DE = _REPO_ROOT / "docs" / "evidence" / "LAPTOP_FAILURE_TEST_READINESS_REPORT_DE.md"
_REPORT_EN = _REPO_ROOT / "docs" / "evidence" / "LAPTOP_FAILURE_TEST_READINESS_REPORT_EN.md"
_MAX_OUTPUT_BYTES = 768 * 1024

_EXPECTED_RUNBOOKS = (
    "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
    "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
    "RUNBOOK_ROLLBACK_RUNTIME",
)
_CHAIN_MODULES = (
    "runner_manual_runtime_precheck.py",
    "runner_manual_runtime_result_template.py",
    "runner_manual_runtime_result_validator_handoff_gate.py",
    "runner_manual_runtime_result_validator_dryrun_from_handoff.py",
    "runner_manual_runtime_laptop_failure_operator_runorder.py",
    "runner_manual_runtime_laptop_failure_execution_log_template.py",
    "runner_manual_runtime_laptop_failure_execution_log_validator.py",
    "runner_manual_runtime_laptop_failure_test_summary.py",
    "runner_manual_runtime_laptop_failure_final_report.py",
)


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


def _http_json(method: str, url: str, body: dict[str, Any] | None, timeout_s: float) -> tuple[int | None, Any | None, str]:
    try:
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            raw = json.dumps(body).encode("utf-8")
            data = raw
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            code = int(getattr(resp, "status", 200) or 200)
            txt = resp.read().decode("utf-8", errors="replace")
            try:
                return code, json.loads(txt), ""
            except json.JSONDecodeError:
                return code, {"_non_json": txt[:2000]}, "READINESS_HTTP_NON_JSON"
    except urllib.error.HTTPError as e:
        try:
            payload = e.read().decode("utf-8", errors="replace")
            return int(e.code), json.loads(payload), ""
        except Exception:
            return int(e.code), None, str(e)[:300]
    except Exception as e:
        return None, None, str(e)[:300]


def _run_readonly_cmd(argv: list[str], timeout_s: float = 8.0) -> tuple[int | None, str, str]:
    try:
        p = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        return int(p.returncode), (p.stdout or "")[:120_000], (p.stderr or "")[:4000]
    except Exception as e:
        return None, "", str(e)[:400]


def _traffic_light(ok: bool, partial: bool, bad: bool) -> str:
    if bad:
        return "red"
    if ok and not partial:
        return "green"
    if ok or partial:
        return "yellow"
    return "red"


def _scan_deploy_routes_forbidden_laptop_block() -> tuple[bool, list[str]]:
    """True if no @router.post line for laptop-failure paths contains forbidden verb segments."""
    if not _ROUTES.is_file():
        return False, ["ROUTES_FILE_MISSING"]
    hits: list[str] = []
    for ln in _ROUTES.read_text(encoding="utf-8", errors="replace").splitlines():
        low = ln.lower()
        if "laptop-failure" not in low or "@router.post" not in low:
            continue
        for bad in ("/execute", "/apply", "/install", "/delete", "/release", "/publish"):
            if bad in low:
                hits.append(f"{bad}:{ln.strip()[:160]}")
    return len(hits) == 0, hits


def _repo_component_score() -> tuple[int, int, list[str]]:
    """Count present / expected repo artefacts (no live assumptions)."""
    notes: list[str] = []
    present = 0
    total = 0
    deploy_dir = _REPO_ROOT / "backend" / "deploy"
    for name in _CHAIN_MODULES:
        total += 1
        p = deploy_dir / name
        if p.is_file():
            present += 1
        else:
            notes.append(f"missing_module:{name}")
    total += len(_EXPECTED_RUNBOOKS)
    tpl = deploy_dir / "runner_manual_runtime_result_template.py"
    if tpl.is_file():
        ttxt = tpl.read_text(encoding="utf-8", errors="replace")
        for rb in _EXPECTED_RUNBOOKS:
            if rb in ttxt:
                present += 1
            else:
                notes.append(f"runbook_not_in_template_constants:{rb}")
    return present, total, notes


def _count_handoff_json() -> tuple[int, list[str]]:
    ev: list[str] = []
    if not _HANDOFF_ROOT.is_dir():
        return 0, ["HANDOFF_DIR_MISSING"]
    n = 0
    for p in sorted(_HANDOFF_ROOT.glob("*.json")):
        if p.is_file() and not p.is_symlink():
            n += 1
    ev.append(f"handoff_json_count:{n}")
    return n, ev


def _phase2_runorder_steps(
    probe_live: bool,
    live_base: str,
    api_results: dict[str, Any],
    repo_score: tuple[int, int, list[str]],
    handoff_n: int,
) -> list[dict[str, Any]]:
    present, total, _ = repo_score
    chain_ok = present >= total

    def step(
        name: str,
        ready: bool,
        reason: str,
        fix: str,
        evidence: list[str],
    ) -> dict[str, Any]:
        return {
            "step": name,
            "ready": bool(ready),
            "blocking_reason": reason,
            "required_fix": fix,
            "evidence": list(evidence),
        }

    ar = api_results.get("aggregate") if isinstance(api_results, dict) else {}
    live_ok = bool(ar.get("live_reachable")) if probe_live else False

    return [
        step(
            "1_backup_finden",
            handoff_n > 0 or live_ok,
            "" if (handoff_n > 0 or live_ok) else "Kein lokaler Handoff-Nachweis und API nicht verifiziert.",
            "Backups listen oder Live-API mit gueltigem backup_file pruefen.",
            [f"handoff_json_files={handoff_n}", f"live_probe={probe_live}"],
        ),
        step(
            "2_verify_basic",
            live_ok,
            "" if live_ok else ("Live-API nicht geprueft" if not probe_live else "Verify-Endpunkt nicht erreichbar."),
            "POST /api/backup/verify mit erlaubtem Pfad (basic) ausfuehren.",
            api_results.get("verify_basic", {}).get("evidence", []) if isinstance(api_results, dict) else [],
        ),
        step(
            "3_verify_deep",
            live_ok,
            "" if live_ok else ("Live-API nicht geprueft" if not probe_live else "Verify deep nicht verifiziert."),
            "POST /api/backup/verify mode=deep nur mit zugelassenem Archiv.",
            api_results.get("verify_deep", {}).get("evidence", []) if isinstance(api_results, dict) else [],
        ),
        step(
            "4_restore_preview",
            live_ok,
            "" if live_ok else ("Live-API nicht geprueft" if not probe_live else "Restore-Preview nicht verifiziert."),
            "POST /api/backup/restore mode=preview nur nach Safety-Gates.",
            api_results.get("restore_preview", {}).get("evidence", []) if isinstance(api_results, dict) else [],
        ),
        step(
            "5_runtime_result_template",
            chain_ok,
            "" if chain_ok else "Pflichtmodule/Runbook-Referenzen fehlen im Repo.",
            "Fehlende Deploy-Runner-Dateien ergaenzen.",
            [f"repo_chain_score={present}/{total}"],
        ),
        step(
            "6_runtime_result_validator",
            chain_ok,
            "" if chain_ok else "Validator-Kette im Repo unvollstaendig.",
            "Handoff-Validator und Dry-Run-Pfade pruefen.",
            [f"repo_chain_score={present}/{total}"],
        ),
        step(
            "7_evidence_ingestion",
            handoff_n > 0,
            "" if handoff_n > 0 else "Keine JSON-Handoffs unter runtime-results/handoff.",
            "Mind. ein Handoff-Artefakt erzeugen (z. B. Precheck/Matrix).",
            _count_handoff_json()[1],
        ),
        step(
            "8_final_summary_report",
            _REPO_ROOT.joinpath("backend/deploy/runner_manual_runtime_laptop_failure_final_report.py").is_file(),
            "" if _REPO_ROOT.joinpath("backend/deploy/runner_manual_runtime_laptop_failure_final_report.py").is_file() else "Final-Report-Runner fehlt.",
            "runner_manual_runtime_laptop_failure_final_report bereitstellen.",
            ["final_report_runner_present"],
        ),
    ]


def _live_api_probe(base: str, probe: bool) -> dict[str, Any]:
    out: dict[str, Any] = {"probe_live_system": bool(probe), "base_url": base.rstrip("/")}
    if not probe:
        out["aggregate"] = {"live_reachable": False, "note": "LIVE_PROBE_DISABLED_STRICT_NO_ASSUMPTION"}
        return out

    def one(
        key: str,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = base.rstrip("/") + path
        code, js, err = _http_json(method, url, body, 3.0)
        ev = [f"http_code={code}", f"url={url}"]
        if err:
            ev.append(f"error={err}")
        return {"http_status": code, "json": js, "error": err, "evidence": ev}

    out["version"] = one("version", "GET", "/api/version")
    out["health_primary"] = one("health", "GET", "/api/health")
    if (out["health_primary"].get("http_status") or 0) == 404 or out["health_primary"].get("error"):
        out["health_fallback"] = one("health_root", "GET", "/health")
    out["network"] = one("network", "GET", "/api/system/network")
    out["preflight_sources"] = one("preflight", "GET", "/api/preflight/sources")
    out["verify_basic"] = one("verify", "POST", "/api/backup/verify", {})
    out["verify_deep"] = one(
        "verify_deep",
        "POST",
        "/api/backup/verify",
        {"backup_file": "__missing_for_contract_probe__", "mode": "deep"},
    )
    out["restore_preview"] = one(
        "restore_preview",
        "POST",
        "/api/backup/restore",
        {"file": "__missing_for_contract_probe__", "mode": "preview"},
    )

    pre_body = {
        "selected_runbook": "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
        "next_phase_gate": {"allowed_next_phases": ["NEXT_PHASE_MANUAL_RUNTIME_TESTS"]},
        "operator_confirmations": {
            "full_backup_confirmed": True,
            "local_control_confirmed": True,
            "single_test_media_confirmed": True,
            "productive_media_removed_confirmed": True,
            "stop_conditions_acknowledged": True,
            "no_remote_without_local_control_confirmed": True,
            "no_auto_retry_confirmed": True,
            "operator_understands_data_loss": True,
        },
        "hardware_gate_report": {},
        "real_write_guard_report": {},
        "runtime_context": {},
    }
    out["manual_runtime_precheck"] = one("precheck", "POST", "/api/deploy/runner/manual-runtime/precheck", pre_body)
    out["manual_runtime_template"] = one("template", "POST", "/api/deploy/runner/manual-runtime/result-template", {"precheck": {}, "explicit_overwrite": False})

    ver_ok = out["version"].get("http_status") == 200
    net_ok = out["network"].get("http_status") == 200
    hl = out.get("health_fallback") or out["health_primary"]
    health_ok = (out["health_primary"].get("http_status") == 200) or (hl.get("http_status") == 200)
    out["aggregate"] = {
        "live_reachable": bool(ver_ok and health_ok and net_ok),
        "version_ok": ver_ok,
        "health_ok": health_ok,
        "network_ok": net_ok,
    }
    return out


def _storage_probe(probe: bool) -> dict[str, Any]:
    out: dict[str, Any] = {"probed": bool(probe)}
    if not probe:
        out["note"] = "STORAGE_SUBSYSTEM_NOT_PROBED"
        return out
    rc, stdout, stderr = _run_readonly_cmd(["lsblk", "-J"], 6.0)
    out["lsblk"] = {"returncode": rc, "stderr_tail": stderr[-800:], "parsed": None}
    if rc == 0 and stdout.strip():
        try:
            out["lsblk"]["parsed"] = json.loads(stdout)
        except json.JSONDecodeError:
            out["lsblk"]["parse_error"] = "lsblk_json_invalid"
    rc2, out2, err2 = _run_readonly_cmd(["findmnt", "-J"], 6.0)
    out["findmnt"] = {"returncode": rc2, "stderr_tail": err2[-800:], "parsed": None}
    if rc2 == 0 and out2.strip():
        try:
            out["findmnt"]["parsed"] = json.loads(out2)
        except json.JSONDecodeError:
            out["findmnt"]["parse_error"] = "findmnt_json_invalid"
    return out


def _journal_tail(probe: bool) -> dict[str, Any]:
    if not probe:
        return {"probed": False}
    rc, stdout, stderr = _run_readonly_cmd(
        ["journalctl", "-u", "setuphelfer-backend.service", "-n", "40", "--no-pager"],
        8.0,
    )
    return {"probed": True, "returncode": rc, "stdout_tail": stdout[-6000:], "stderr_tail": stderr[-800:]}


def build_laptop_failure_test_execution_readiness_final_gate(
    *,
    explicit_overwrite: bool = False,
    probe_live_system: bool = False,
    live_base_url: str | None = None,
) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_OUT_REL, "LAPTOP_READINESS")
    if oerr or out_path is None:
        return _emit("blocked", {}, [oerr or "LAPTOP_READINESS_OUTPUT_INVALID"], [], wrote_file=False)
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _emit("blocked", {}, ["LAPTOP_READINESS_EXISTS_NO_OVERWRITE"], [], wrote_file=False)

    base = str(live_base_url or os.environ.get("SETUPHELFER_READINESS_BASE_URL") or "http://127.0.0.1:8000").strip()
    if not base.startswith("http://") and not base.startswith("https://"):
        base = "http://127.0.0.1:8000"

    brand, _ = _load_json_handoff("docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json", "BRAND")
    branding_blocked = isinstance(brand, dict) and str(brand.get("branding_guard_status") or "") == "blocked"

    handoff_n, handoff_ev = _count_handoff_json()
    repo_present, repo_total, repo_notes = _repo_component_score()
    routes_safe, forbidden_hits = _scan_deploy_routes_forbidden_laptop_block()

    api_results = _live_api_probe(base, bool(probe_live_system))
    storage = _storage_probe(bool(probe_live_system))
    journal = _journal_tail(bool(probe_live_system))

    phase1: dict[str, Any] = {
        "repo_root": str(_REPO_ROOT),
        "runtime_evidence_dir_exists": _RUNTIME_EVIDENCE.is_dir(),
        "handoff_json_count": handoff_n,
        "deploy_chain_modules": f"{repo_present}/{repo_total}",
        "deploy_routes_laptop_failure_forbidden_scan_ok": routes_safe,
        "branding_guard_handoff_blocked": branding_blocked,
        "notes": repo_notes + handoff_ev,
    }

    phase3 = {
        "live_probe_enabled": bool(probe_live_system),
        "results": api_results,
        "health_path_note": "/api/health nicht registriert — Fallback /health laut app.py pruefen.",
    }

    phase4 = {
        "storage_probe": storage,
        "journalctl_setuphelfer_backend": journal,
        "safety_note": "Kein Restore, kein Low-Level-Block-Write, kein zusaetzlicher Mount-Umfang durch diesen Runner.",
    }

    phase5 = {
        "runtime_result_chain_repo_score": f"{repo_present}/{repo_total}",
        "laptop_failure_route_forbidden_hits": forbidden_hits,
        "explicit_overwrite_pattern": "Handoff-Runner verwenden explicit_overwrite wie in Deploy-Spezifikation.",
    }

    live_agg = api_results.get("aggregate") if isinstance(api_results, dict) else {}
    live_reachable = bool(live_agg.get("live_reachable")) if probe_live_system else False

    recovery_core_ok = _RUNTIME_EVIDENCE.is_dir() and repo_present >= repo_total and routes_safe
    verify_chain_ok = live_reachable and probe_live_system
    restore_preview_ok = live_reachable and probe_live_system
    runtime_val_ok = recovery_core_ok and not branding_blocked
    device_safety_ok = probe_live_system and storage.get("lsblk", {}).get("returncode") == 0
    bootstick_ok = handoff_n > 0

    snap = {
        "recovery_core": _traffic_light(recovery_core_ok, not recovery_core_ok, branding_blocked or not routes_safe),
        "verify_chain": _traffic_light(verify_chain_ok, probe_live_system and not verify_chain_ok, False),
        "restore_preview": _traffic_light(restore_preview_ok, probe_live_system and not restore_preview_ok, False),
        "runtime_validation": _traffic_light(runtime_val_ok, branding_blocked, not routes_safe),
        "device_safety": _traffic_light(device_safety_ok, probe_live_system and not device_safety_ok, False),
        "bootstick_foundation": _traffic_light(bootstick_ok, handoff_n == 0, False),
        "remaining_blockers": [],
        "next_required_phase": "",
    }

    blockers: list[dict[str, Any]] = []
    if branding_blocked:
        blockers.append(
            {
                "severity": "high",
                "problem": "Branding-Guard Handoff meldet blockiert.",
                "root_cause": "Aktive Legacy-Marken laut letztem Branding-Check.",
                "fix_recommendation": "Legacy-Identifier und Branding-Gate erneut ausfuehren.",
                "estimated_effort": "mittel",
            }
        )
    if not routes_safe:
        blockers.append(
            {
                "severity": "critical",
                "problem": "Verdaechtige Subrouten in Laptop-Failure-Deploy-Region.",
                "root_cause": str(forbidden_hits),
                "fix_recommendation": "routes.py Laptop-Bereich bereinigen.",
                "estimated_effort": "niedrig",
            }
        )
    if repo_present < repo_total:
        blockers.append(
            {
                "severity": "medium",
                "problem": "Runtime-Result-Kette im Repo unvollstaendig.",
                "root_cause": "Fehlende Module oder Runbook-Referenzen.",
                "fix_recommendation": "Fehlende Dateien aus score-Liste ergaenzen.",
                "estimated_effort": "mittel",
            }
        )
    if probe_live_system and not live_reachable:
        blockers.append(
            {
                "severity": "high",
                "problem": "Live-API unter Basis-URL nicht erreichbar oder nicht JSON-faehig.",
                "root_cause": str(live_agg),
                "fix_recommendation": "Dienst starten oder korrekte SETUPHELFER_READINESS_BASE_URL setzen.",
                "estimated_effort": "variabel",
            }
        )
    if not probe_live_system:
        blockers.append(
            {
                "severity": "low",
                "problem": "Live-Subsystem nicht geprueft.",
                "root_cause": "probe_live_system=false (STRICT, keine Annahmen).",
                "fix_recommendation": "Mit probe_live_system=true und laeufigem Backend erneut ausfuehren.",
                "estimated_effort": "gering",
            }
        )

    snap["remaining_blockers"] = [b.get("problem", "") for b in blockers]
    if branding_blocked or not routes_safe:
        snap["next_required_phase"] = "BLOCKER_REMEDIATION"
    elif not probe_live_system:
        snap["next_required_phase"] = "LIVE_PROBE_FOR_FULL_SIGNOFF"
    elif not live_reachable:
        snap["next_required_phase"] = "API_BRINGUP"
    else:
        snap["next_required_phase"] = "OPERATOR_FIELD_LAPTOP_CHAIN"

    pct_core = int(round(100 * repo_present / max(1, repo_total)))
    pct_boot = min(100, handoff_n * 4)
    pct_prov = 35 if _APP.is_file() else 0
    pct_installer = 40 if (_REPO_ROOT / "frontend").is_dir() else 0
    pct_cloud = 0

    steps = _phase2_runorder_steps(bool(probe_live_system), base, api_results, (repo_present, repo_total, repo_notes), handoff_n)

    critical = sum(1 for b in blockers if b.get("severity") == "critical")
    high = sum(1 for b in blockers if b.get("severity") == "high")
    gate_status = "ok"
    if critical or not routes_safe or branding_blocked:
        gate_status = "blocked"
    elif high or not probe_live_system or not live_reachable:
        gate_status = "review_required"

    abnahme = "fail"
    if (
        gate_status == "ok"
        and not branding_blocked
        and verify_chain_ok
        and restore_preview_ok
        and routes_safe
        and probe_live_system
    ):
        abnahme = "pass"
    elif gate_status == "review_required" and not branding_blocked and routes_safe:
        abnahme = "conditional_review"

    body: dict[str, Any] = {
        "laptop_failure_test_execution_readiness_gate_schema_version": 1,
        "strict_mode": "laptop_failure_test_execution_readiness_final_gate",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_status": gate_status,
        "abnahme_decision": abnahme,
        "phase1_ist_analysis": phase1,
        "phase2_failure_runorder": steps,
        "phase3_api_contract": phase3,
        "phase4_storage_safety": phase4,
        "phase5_runtime_result_chain": phase5,
        "phase6_rescue_readiness_snapshot": snap,
        "phase7_blockers": blockers,
        "percent_estimates": {
            "recovery_core_pct": pct_core,
            "bootstick_basis_pct": pct_boot,
            "provisioning_layer_pct": pct_prov,
            "installer_layer_pct": pct_installer,
            "cloud_orchestration_pct": pct_cloud,
            "percent_method": "Repo-Dateien und Handoff-Anzahl; Cloud=0 bis Pilot; keine erfundenen Werte.",
        },
        "outputs": {
            "handoff_json": _OUT_REL,
            "report_de": "docs/evidence/LAPTOP_FAILURE_TEST_READINESS_REPORT_DE.md",
            "report_en": "docs/evidence/LAPTOP_FAILURE_TEST_READINESS_REPORT_EN.md",
        },
    }

    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit("blocked", {}, ["LAPTOP_READINESS_OUTPUT_TOO_LARGE"], [], wrote_file=False)
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _emit("blocked", {}, ["LAPTOP_READINESS_WRITE_FAILED"], [], wrote_file=False)

    _write_markdown_reports(body)
    return _emit(gate_status, body, [], [], wrote_file=True)


def _write_markdown_reports(body: dict[str, Any]) -> None:
    snap = body.get("phase6_rescue_readiness_snapshot") if isinstance(body.get("phase6_rescue_readiness_snapshot"), dict) else {}
    gate = str(body.get("gate_status") or "")
    ab = str(body.get("abnahme_decision") or "")
    gen = str(body.get("generated_at") or "")
    de = f"""# Laptop Failure Test Execution Readiness (DE)

**STRICT / evidenzbasiert** — generiert: `{gen}`  
**Gate-Status:** `{gate}` — **Abnahme:** `{ab}`

Dieser Report wird aus dem Gate-Runner befuellt. Keine simulierten Greens: Live-API und Storage sind nur bewertet, wenn `probe_live_system=true` gesetzt wurde.

## Snapshot (Phase 6)

| Dimension | Ampel |
|-----------|-------|
| recovery_core | {snap.get("recovery_core")} |
| verify_chain | {snap.get("verify_chain")} |
| restore_preview | {snap.get("restore_preview")} |
| runtime_validation | {snap.get("runtime_validation")} |
| device_safety | {snap.get("device_safety")} |
| bootstick_foundation | {snap.get("bootstick_foundation")} |

**Naechste Phase:** `{snap.get("next_required_phase")}`

## Rohdaten

Vollstaendiges JSON: `docs/evidence/runtime-results/handoff/laptop_failure_test_execution_readiness_gate.json`

## Hinweis

Kein Restore, kein Device-Write, keine Low-Level-Formatierung — nur Readiness-Diagnose.
"""
    en = f"""# Laptop Failure Test Execution Readiness (EN)

**STRICT / evidence-based** — generated: `{gen}`  
**Gate status:** `{gate}` — **Acceptance:** `{ab}`

This report is filled by the gate runner. No simulated greens: live API and storage are only scored when `probe_live_system=true`.

## Snapshot (phase 6)

| Dimension | light |
|-----------|-------|
| recovery_core | {snap.get("recovery_core")} |
| verify_chain | {snap.get("verify_chain")} |
| restore_preview | {snap.get("restore_preview")} |
| runtime_validation | {snap.get("runtime_validation")} |
| device_safety | {snap.get("device_safety")} |
| bootstick_foundation | {snap.get("bootstick_foundation")} |

**Next phase:** `{snap.get("next_required_phase")}`

## Raw data

Full JSON: `docs/evidence/runtime-results/handoff/laptop_failure_test_execution_readiness_gate.json`

## Note

No restore, no device write, no low-level formatting — readiness diagnostics only.
"""
    _REPORT_DE.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(_REPORT_DE, de)
    _atomic_write(_REPORT_EN, en)


def _emit(
    status: str,
    body: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    *,
    wrote_file: bool,
) -> dict[str, Any]:
    return {
        "laptop_failure_test_execution_readiness_gate_status": status,
        "laptop_failure_test_execution_readiness_gate_file_path": _OUT_REL,
        "laptop_failure_test_execution_readiness_gate": body,
        "laptop_failure_readiness_handoff_written": bool(wrote_file),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
