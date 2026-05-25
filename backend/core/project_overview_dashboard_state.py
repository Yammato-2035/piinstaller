"""
Read-only Projektuebersicht fuer das Development Dashboard.

Aggregiert Runtime/Deploy/Update/Rescue/Packaging sowie Roadmap-, Evidence-,
Monolith- und Testregister-Hinweise ohne gefaehrliche Aktionen.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.deploy_job_state import build_deploy_job_state
from core.packaging_readiness_state import build_packaging_readiness_state
from core.rescue_iso_build_state import build_rescue_iso_dashboard_state
from core.update_check import build_update_status

UTC = timezone.utc


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _normalize_status(raw: Any, *, fallback: str = "gray") -> str:
    text = str(raw or "").strip().lower()
    mapping = {
        "ok": "green",
        "success": "green",
        "green": "green",
        "pre_chroot_ok": "green",
        "blocked": "red",
        "failed": "red",
        "error": "red",
        "red": "red",
        "deploy_required": "yellow",
        "review_required": "yellow",
        "operator_required": "yellow",
        "yellow": "yellow",
        "pending": "yellow",
        "not_started": "yellow",
        "idle": "yellow",
        "unknown": "gray",
        "gray": "gray",
    }
    return mapping.get(text, fallback)


def _roadmap_overview(repo: Path) -> dict[str, Any]:
    md_rel = "docs/roadmap/MASTER_ROADMAP_2026_2030.md"
    json_rel = "docs/roadmap/master_roadmap_status.json"
    md_path = repo / md_rel
    json_path = repo / json_rel
    data = _read_json(json_path) or {}
    status = _normalize_status(data.get("overall_status"), fallback="green" if md_path.is_file() and json_path.is_file() else "yellow")
    if not (md_path.is_file() and json_path.is_file()):
        status = "yellow"
    return {
        "overall_status": status,
        "summary": str(data.get("summary") or "Roadmap-Uebersicht vorhanden." if md_path.is_file() else "Roadmap-Uebersicht fehlt."),
        "files_present": {
            md_rel: md_path.is_file(),
            json_rel: json_path.is_file(),
        },
    }


def _monolith_overview(repo: Path) -> dict[str, Any]:
    md_rel = "docs/architecture/MONOLITH_BOUNDARY_MAP.md"
    json_rel = "docs/architecture/monolith_boundary_status.json"
    md_path = repo / md_rel
    json_path = repo / json_rel
    data = _read_json(json_path) or {}
    status = _normalize_status(data.get("overall_status"), fallback="yellow" if md_path.is_file() else "gray")
    if md_path.is_file() and status == "green":
        status = "yellow"
    return {
        "overall_status": status,
        "summary": str(data.get("summary") or "Monolith-Map read-only dokumentiert; Entkopplung bleibt offen."),
        "files_present": {
            md_rel: md_path.is_file(),
            json_rel: json_path.is_file(),
        },
    }


def _tests_overview(repo: Path) -> dict[str, Any]:
    md_rel = "docs/evidence/TEST_FAILURE_REGISTER.md"
    json_rel = "docs/evidence/test_failure_register.json"
    md_path = repo / md_rel
    json_path = repo / json_rel
    data = _read_json(json_path) or {}
    summary = str(data.get("summary") or "Test-Register als Uebersicht vorhanden; offene Testfelder bleiben separat bewertet.")
    return {
        "summary_status": "green" if md_path.is_file() and json_path.is_file() else "yellow",
        "summary": summary,
        "files_present": {
            md_rel: md_path.is_file(),
            json_rel: json_path.is_file(),
        },
        "open_failures_status": _normalize_status(data.get("open_failures_status"), fallback="yellow"),
    }


def _evidence_overview(repo: Path) -> dict[str, Any]:
    md_rel = "docs/evidence/EVIDENCE_INDEX.md"
    json_rel = "docs/evidence/evidence_index.json"
    md_path = repo / md_rel
    json_path = repo / json_rel
    data = _read_json(json_path) or {}
    status = "green" if md_path.is_file() and json_path.is_file() else "yellow"
    return {
        "overall_status": status,
        "summary": str(data.get("summary") or "Evidence-Index vorhanden." if md_path.is_file() else "Evidence-Index unvollstaendig."),
        "files_present": {
            md_rel: md_path.is_file(),
            json_rel: json_path.is_file(),
        },
    }


def _rescue_overview(rescue: dict[str, Any]) -> dict[str, Any]:
    dpkg = dict(rescue.get("dpkg_preflight") or {})
    bundle = dict(rescue.get("temp_runtime_bundle") or {})
    tree = dict(rescue.get("build_tree") or {})
    stale = dict(rescue.get("stale_state") or {})
    iso_build = dict(rescue.get("iso_build") or {})

    dpkg_status = _normalize_status(dpkg.get("status"), fallback="gray")
    if stale.get("needs_sudo_clean"):
        overall = "yellow"
        summary = "Rescue-ISO-Prebuild bereit, aber sudo clean fuer Stale-State erforderlich."
    elif bundle.get("status") == "ok" and tree.get("validator_status") == "ok" and dpkg_status == "green":
        overall = "yellow" if not iso_build.get("iso_found") else "green"
        summary = "Rescue-ISO-Prebuild ist gruen; echter ISO-Build bleibt separat review_required."
    elif rescue.get("path_status") != "ok":
        overall = "red"
        summary = "Rescue-ISO-Pfadvertrag ist nicht bereit."
    else:
        overall = _normalize_status(rescue.get("status"), fallback="yellow")
        summary = str(rescue.get("summary") or "Rescue-ISO-Status verfuegbar.")

    return {
        "overall_status": overall,
        "summary": summary,
        "dpkg_preflight_status": dpkg.get("status"),
        "temp_runtime_bundle_status": bundle.get("status"),
        "build_tree_status": tree.get("validator_status"),
        "iso_build_status": iso_build.get("status"),
        "next_operator_action": ((rescue.get("next_operator_action") or {}).get("type")),
    }


def build_project_overview_dashboard_state(*, repo_root: Path | None = None) -> dict[str, Any]:
    repo = (repo_root or _repo_root()).resolve(strict=False)
    deploy = build_deploy_job_state()
    update = build_update_status()
    rescue = build_rescue_iso_dashboard_state(repo_root=repo)
    packaging = build_packaging_readiness_state()
    roadmap = _roadmap_overview(repo)
    monolith = _monolith_overview(repo)
    tests = _tests_overview(repo)
    evidence = _evidence_overview(repo)

    runtime_status = "green" if ((deploy.get("runtime_gate") or {}).get("exit_code")) == 0 else "red"
    deploy_status = "green" if str((deploy.get("last_job") or {}).get("status") or "").lower() == "success" else _normalize_status(deploy.get("status"))
    update_status = "green" if update.get("status") == "ok" and not update.get("deploy_required") else _normalize_status(update.get("status"), fallback="yellow")
    rescue_status = _rescue_overview(rescue)
    dpkg_status = _normalize_status(((rescue.get("dpkg_preflight") or {}).get("status")), fallback="gray")
    usb_gate_status = (
        "green"
        if bool(((rescue.get("usb_write") or {}).get("allowed"))) is False
        and bool(((rescue.get("forbidden_actions") or {}).get("usb_write_allowed"))) is False
        else "red"
    )

    section_statuses = [
        runtime_status,
        deploy_status,
        update_status,
        rescue_status["overall_status"],
        dpkg_status,
        _normalize_status(packaging.get("status")),
        roadmap["overall_status"],
        tests["summary_status"],
        monolith["overall_status"],
        evidence["overall_status"],
    ]
    if any(status == "red" for status in section_statuses):
        overall_status = "red"
    elif any(status == "yellow" for status in section_statuses):
        overall_status = "yellow"
    elif any(status == "gray" for status in section_statuses):
        overall_status = "gray"
    else:
        overall_status = "green"

    return {
        "status": overall_status,
        "generated_at": _now_iso(),
        "runtime": {
            "overall_status": runtime_status,
            "summary": (deploy.get("runtime_gate") or {}).get("summary"),
            "exit_code": (deploy.get("runtime_gate") or {}).get("exit_code"),
        },
        "deploy_helper": {
            "overall_status": deploy_status,
            "summary": (deploy.get("last_job") or {}).get("summary"),
            "last_job_status": (deploy.get("last_job") or {}).get("status"),
        },
        "update_check": {
            "overall_status": update_status,
            "summary": update.get("status"),
            "deploy_required": update.get("deploy_required"),
            "automatic_update_allowed": update.get("automatic_update_allowed"),
            "package_manager_update_allowed": update.get("package_manager_update_allowed"),
        },
        "rescue_iso": rescue_status,
        "dpkg_preflight": {
            "overall_status": dpkg_status,
            "summary": ((rescue.get("dpkg_preflight") or {}).get("summary")),
        },
        "usb_write_gate": {
            "overall_status": usb_gate_status,
            "summary": "USB-Write bleibt absichtlich blockiert.",
            "allowed": ((rescue.get("usb_write") or {}).get("allowed")),
        },
        "packaging": {
            "overall_status": _normalize_status(packaging.get("status"), fallback="yellow"),
            "summary": packaging.get("summary"),
            "install_test_passed": packaging.get("install_test_passed"),
        },
        "roadmap": roadmap,
        "tests": tests,
        "monolith": monolith,
        "evidence": evidence,
    }
