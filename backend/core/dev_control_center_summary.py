"""
Read-only Control Center summary aggregator for the Development Dashboard.

No jobs, no backup/restore, no rescue build, no SSH actions.
Missing data surfaces as unknown/not_available — never fake green.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc

_DE_EN_PAIR_RE = re.compile(r"^(?P<base>.+)_(DE|EN)\.md$", re.I)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _count_md_files(base: Path, *, max_files: int = 5000) -> int:
    if not base.is_dir():
        return 0
    count = 0
    try:
        for root, _dirs, files in os.walk(base):
            for fn in files:
                if fn.endswith(".md"):
                    count += 1
                    if count >= max_files:
                        return count
    except OSError:
        return count
    return count


def _scan_translation_pairs(repo: Path) -> dict[str, Any]:
    missing_de: list[str] = []
    missing_en: list[str] = []
    complete = 0
    bases: dict[str, set[str]] = {}
    docs = repo / "docs"
    if not docs.is_dir():
        return {
            "complete": 0,
            "missing_de": [],
            "missing_en": [],
            "warnings": ["docs_dir_missing"],
        }
    try:
        for fp in docs.rglob("*.md"):
            m = _DE_EN_PAIR_RE.match(fp.name)
            if not m:
                continue
            rel = str(fp.relative_to(docs)).replace("\\", "/")
            base_key = f"{fp.parent.relative_to(docs)}/{m.group('base')}".replace("\\", "/")
            lang = fp.name.rsplit("_", 1)[-1][:2].upper()
            bases.setdefault(base_key, set()).add(lang)
    except OSError as exc:
        return {"complete": 0, "missing_de": [], "missing_en": [], "warnings": [f"scan_error:{exc}"]}

    for base_key, langs in sorted(bases.items()):
        if "DE" in langs and "EN" in langs:
            complete += 1
        elif "EN" in langs:
            missing_de.append(base_key)
        elif "DE" in langs:
            missing_en.append(base_key)

    warnings: list[str] = []
    if missing_de or missing_en:
        warnings.append("translation_pairs_incomplete")
    return {
        "complete": complete,
        "missing_de": missing_de[:40],
        "missing_en": missing_en[:40],
        "warnings": warnings,
    }


def build_documentation_stats(repo_root: Path | None = None) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    docs = repo / "docs"
    pairs = _scan_translation_pairs(repo)
    return {
        "status": "available" if docs.is_dir() else "not_available",
        "docs_total": _count_md_files(docs),
        "faq_total": _count_md_files(docs / "faq"),
        "kb_total": _count_md_files(docs / "knowledge-base"),
        "architecture_total": _count_md_files(docs / "architecture"),
        "runbooks_total": _count_md_files(docs / "runbooks"),
        "evidence_total": _count_md_files(docs / "evidence"),
        "translation_pairs": pairs,
        "warnings": list(pairs.get("warnings") or []),
    }


def build_diagnostics_stats(repo_root: Path | None = None) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    warnings: list[str] = []
    code_count = 0
    catalog_available = False
    try:
        from core.diagnostics.registry import DIAGNOSTIC_CATALOG

        code_count = len(DIAGNOSTIC_CATALOG)
        catalog_available = code_count > 0
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"catalog_import_error:{exc}")

    test_count = 0
    tests_dir = repo / "backend" / "tests"
    if tests_dir.is_dir():
        test_count = sum(
            1 for fp in tests_dir.glob("test*.py") if "diagnostic" in fp.name.lower()
        )

    kb_count = _count_md_files(repo / "docs" / "knowledge-base" / "diagnostics")
    data_diag = repo / "data" / "diagnostics"
    data_available = data_diag.is_dir()

    if not catalog_available:
        warnings.append("diagnostics_catalog_unavailable")

    return {
        "status": "available" if catalog_available else "unknown",
        "catalog_available": catalog_available,
        "code_count": code_count,
        "test_count": test_count,
        "kb_count": kb_count,
        "data_catalog_dir": data_available,
        "warnings": warnings,
    }


def build_dev_server_section() -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    try:
        from devserver.config import load_dev_server_config
        from devserver.storage import DevServerStorage

        config = load_dev_server_config()
        storage = DevServerStorage(config.storage_root)
        storage_ok = storage.storage_ok()
        try:
            from core.developer_capability import is_dev_server_host_locally_allowed

            host_locally_allowed = is_dev_server_host_locally_allowed()
        except Exception:
            host_locally_allowed = False
        nodes = storage.list_nodes() if config.enabled else []
        reports = storage.list_reports(limit=50) if config.enabled else []

        online = sum(1 for n in nodes if n.get("status") == "online")
        busy = sum(1 for n in nodes if n.get("status") == "busy")
        err_n = sum(1 for n in nodes if n.get("status") == "error")

        latest_report = reports[0] if reports else None
        agent_reports = [r for r in reports if str(r.get("report_type") or "") == "rescue"]
        latest_agent = agent_reports[0] if agent_reports else None

        if not storage_ok and config.enabled:
            errors.append("storage_not_writable")

        agent_findings = [
            {
                "report_id": r.get("report_id"),
                "node_id": r.get("node_id"),
                "report_type": r.get("report_type"),
                "created_at": r.get("created_at"),
                "source": "dev_server_agent_upload",
            }
            for r in reports[:5]
        ]
        return {
            "status": "available",
            "enabled": config.enabled,
            "mode": config.mode,
            "host_locally_allowed": host_locally_allowed,
            "capability_gated": not config.enabled and host_locally_allowed,
            "storage_ok": storage_ok,
            "ssh_allowed": config.ssh_allowed,
            "public_uploads_allowed": config.public_uploads_allowed,
            "node_count": len(nodes),
            "online_count": online,
            "busy_count": busy,
            "error_count": err_n,
            "reports_last_24h": storage.reports_last_24h_count() if config.enabled else 0,
            "latest_findings": agent_findings,
            "latest_findings_note": "agent_uploads_not_repo_evidence",
            "latest_report": latest_report,
            "agent_last_report": latest_agent,
            "agent_status": "report_available" if latest_agent else ("no_reports" if config.enabled else "disabled"),
            "warnings": warnings,
            "errors": errors,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "not_available",
            "enabled": False,
            "mode": "unknown",
            "storage_ok": False,
            "ssh_allowed": False,
            "public_uploads_allowed": False,
            "warnings": [f"dev_server_unavailable:{exc}"],
            "errors": [],
        }


def build_rescue_developer_section(repo_root: Path | None = None) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    warnings: list[str] = []
    items: list[dict[str, Any]] = []

    def _evidence_status(rel: str) -> str:
        return "green" if (repo / rel).is_file() else "pending"

    items.append({
        "id": "dev_server_mvp",
        "label": "Development Server MVP",
        "status": _evidence_status("docs/evidence/dev-server/DEV_SERVER_MVP_IMPLEMENTATION.md"),
        "evidence": "docs/evidence/dev-server/",
    })
    items.append({
        "id": "dev_agent_mvp",
        "label": "Development Rescue Agent MVP",
        "status": _evidence_status("docs/evidence/dev-server/DEV_RESCUE_AGENT_MVP_IMPLEMENTATION.md"),
        "evidence": "docs/evidence/dev-server/",
    })
    profile_evidence = repo / "docs/evidence/dev-server/DEV_AGENT_RESCUE_PROFILE_INTEGRATION.md"
    profile_status = "green" if profile_evidence.is_file() else "pending"
    items.append({
        "id": "rescue_developer_profile",
        "label": "Rescue Developer Profile",
        "status": profile_status,
        "evidence": str(profile_evidence.relative_to(repo)).replace("\\", "/") if profile_evidence.is_file() else None,
    })

    public_guard_ok = False
    developer_ok = False
    try:
        from devserver_agent.rescue_profile import (
            default_developer_profile_root,
            default_public_profile_root,
            validate_developer_profile,
            validate_public_profile_guard,
        )

        dev_val = validate_developer_profile(default_developer_profile_root(repo))
        pub_val = validate_public_profile_guard(default_public_profile_root(repo))
        developer_ok = bool(dev_val.get("ok"))
        public_guard_ok = bool(pub_val.get("ok"))
        if not developer_ok:
            warnings.extend(dev_val.get("errors") or [])
        if not public_guard_ok:
            warnings.extend(pub_val.get("errors") or [])
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"profile_validation_error:{exc}")

    items.append({
        "id": "public_profile_guard",
        "label": "Public Profile Guard",
        "status": "green" if public_guard_ok else ("yellow" if profile_status == "green" else "pending"),
        "evidence": "build/rescue/profiles/public/",
    })

    iso_evidence = list((repo / "docs/evidence/runtime-results/rescue").glob("*iso*")) if (repo / "docs/evidence/runtime-results/rescue").is_dir() else []
    items.append({
        "id": "rescue_iso_dry_build",
        "label": "Rescue ISO Dry-Build",
        "status": "pending",
        "evidence": None,
        "note": "No ISO build in this phase",
    })

    next_step = "RESCUE DEVELOPER ISO DRY-BUILD WITH DEV AGENT PROFILE GUARD"
    if not developer_ok or not public_guard_ok:
        next_step = "FIX RESCUE DEVELOPER AGENT PROFILE GUARD"

    return {
        "status": "available",
        "items": items,
        "developer_profile_valid": developer_ok,
        "public_guard_valid": public_guard_ok,
        "next_step": next_step,
        "iso_build_status": "pending",
        "warnings": warnings,
    }


def build_roadmap_section(
    repo_root: Path | None = None,
    *,
    dashboard_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    try:
        from core.dev_dashboard_roadmap import load_roadmap_registry_bundle

        bundle = load_roadmap_registry_bundle(repo_root=repo, dashboard_context=dashboard_context)
        roadmap = bundle.get("roadmap") or {}
        areas = roadmap.get("areas") or []
        summary = roadmap.get("summary") or {}
        recommended = roadmap.get("recommended_prompt") or {}
        if not areas:
            return {
                "status": "unknown",
                "overall_status": summary.get("overall_status") or "unknown",
                "area_count": 0,
                "recommended_prompt": recommended,
                "status_counts": summary.get("status_counts") or {},
                "warnings": list(bundle.get("validation_errors") or []) + ["roadmap_areas_empty"],
            }
        return {
            "status": "available",
            "overall_status": summary.get("overall_status") or "unknown",
            "area_count": len(areas),
            "recommended_prompt": recommended,
            "status_counts": summary.get("status_counts") or {},
            "recent_milestones": [
                {
                    "id": a.get("id"),
                    "title_de": a.get("title_de"),
                    "status": a.get("status"),
                }
                for a in areas[:12]
            ],
            "warnings": list(bundle.get("validation_errors") or []),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "unknown",
            "overall_status": "unknown",
            "area_count": 0,
            "recommended_prompt": {},
            "status_counts": {},
            "warnings": [f"roadmap_unavailable:{exc}"],
        }


def build_evidence_section(repo_root: Path | None = None) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    warnings: list[str] = []
    try:
        from core.dev_dashboard_recent_evidence import build_recent_evidence_for_summary

        feed = build_recent_evidence_for_summary(repo)
        recent_reports = list(feed.get("recent_reports") or [])
        recent_tests = list(feed.get("recent_tests") or [])
        warnings.extend(feed.get("warnings") or [])

        # Legacy file index (mtime-only); capped — not used as primary "reports" source.
        recent_files: list[dict[str, Any]] = []
        try:
            from core import dev_dashboard as dd

            index = dd.build_evidence_index(repo_root=repo, max_files=120)
            for bucket in index.get("buckets") or []:
                for f in (bucket.get("files") or []):
                    recent_files.append({
                        "path": f.get("path"),
                        "mtime_iso": f.get("mtime_iso"),
                        "bucket": bucket.get("root"),
                    })
            recent_files.sort(key=lambda x: str(x.get("mtime_iso") or ""), reverse=True)
            warnings.extend(index.get("warnings") or [])
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"evidence_index_legacy:{exc}")

        return {
            "status": "available" if recent_reports else "unknown",
            "bucket_count": len({r.get("category") for r in recent_reports}),
            "recent_reports": recent_reports,
            "recent_tests": recent_tests,
            "report_filters": feed.get("report_filters") or {},
            "default_limit": feed.get("default_limit") or 5,
            "total_report_count": feed.get("total_reports_unfiltered") or 0,
            "recent_files": recent_files[:5],
            "warnings": warnings,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "not_available",
            "recent_reports": [],
            "recent_tests": [],
            "recent_files": [],
            "warnings": [f"evidence_feed_error:{exc}"],
        }


def build_runtime_section(dashboard: dict[str, Any] | None) -> dict[str, Any]:
    if not dashboard:
        return {"status": "unknown", "warnings": ["dashboard_context_missing"]}
    rg = dashboard.get("runtime_gate") or {}
    dd = dashboard.get("deploy_drift") or {}
    stm = dashboard.get("safe_test_mode") or {}
    runtime = dashboard.get("runtime") or {}
    return {
        "status": "available",
        "runtime_gate_passed": rg.get("passed"),
        "runtime_gate_status": rg.get("status") or "unknown",
        "deploy_drift_status": dd.get("status") or "unknown",
        "safe_test_mode": stm.get("mode") or "unknown",
        "version": dashboard.get("backend_version") or runtime.get("project_version") or "unknown",
        "backend_runtime_path": runtime.get("backend_runtime_path"),
        "release_gate_status": dashboard.get("release_gate_status") or "unknown",
        "blockers": list(rg.get("blockers") or [])[:8],
        "warnings": list(dashboard.get("warnings") or [])[:12],
        "errors": list(dashboard.get("errors") or [])[:8],
    }


def build_next_prompts(
    roadmap: dict[str, Any],
    rescue: dict[str, Any],
) -> list[dict[str, Any]]:
    prompts: list[dict[str, Any]] = []
    rec = roadmap.get("recommended_prompt") or {}
    if rec.get("id"):
        prompts.append({
            "id": str(rec.get("id")),
            "title": rec.get("title_de") or rec.get("title_en") or rec.get("id"),
            "status": "recommended",
            "blocked": False,
        })
    next_rescue = rescue.get("next_step")
    if next_rescue:
        prompts.append({
            "id": "rescue_pipeline_next",
            "title": str(next_rescue),
            "status": "pending",
            "blocked": not rescue.get("developer_profile_valid"),
        })
    return prompts


def build_control_center_summary(
    *,
    repo_root: Path | None = None,
    dashboard: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Aggregate read-only Control Center summary."""
    repo = repo_root or _repo_root()
    warnings: list[str] = []
    errors: list[str] = []

    runtime = build_runtime_section(dashboard)
    roadmap = build_roadmap_section(repo, dashboard_context=dashboard)
    dev_server = build_dev_server_section()
    rescue = build_rescue_developer_section(repo)
    documentation = build_documentation_stats(repo)
    diagnostics = build_diagnostics_stats(repo)
    evidence = build_evidence_section(repo)
    next_prompts = build_next_prompts(roadmap, rescue)

    for section in (runtime, roadmap, dev_server, rescue, documentation, diagnostics, evidence):
        warnings.extend(section.get("warnings") or [])
        errors.extend(section.get("errors") or [])

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "runtime": runtime,
        "roadmap": roadmap,
        "dev_server": dev_server,
        "rescue_developer": rescue,
        "documentation": documentation,
        "diagnostics": diagnostics,
        "evidence": evidence,
        "next_prompts": next_prompts,
        "warnings": warnings[:30],
        "errors": errors[:20],
    }
