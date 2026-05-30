"""FastAPI-Routen für den Setuphelfer Development Server."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query

from devserver.actions import execute_ssh_profile_action
from devserver.config import DevServerConfig, load_dev_server_config
from devserver.ingest import ingest_report
from devserver.models import utc_now_iso
from devserver.prompt_candidates import build_prompt_candidate_from_reports
from devserver.schemas import IngestReportRequest, PromptCandidateFromReportsRequest
from devserver.storage import DevServerStorage

router = APIRouter(prefix="/api/dev-server", tags=["dev-server"])


def _get_config() -> DevServerConfig:
    return load_dev_server_config()


def _get_storage(config: DevServerConfig | None = None) -> DevServerStorage:
    cfg = config or _get_config()
    return DevServerStorage(cfg.storage_root)


def _project_version() -> str:
    try:
        from core.versioning import get_project_version
        return get_project_version()
    except Exception:
        return "unknown"


@router.get("/health")
async def dev_server_health() -> dict[str, Any]:
    config = _get_config()
    storage = _get_storage(config)
    warnings: list[str] = []
    errors: list[str] = []
    storage_ok = storage.storage_ok()
    if not storage_ok:
        errors.append("storage_not_writable")
    if config.enabled and config.require_token and not config.token:
        warnings.append("token_required_but_not_configured")
    return {
        "enabled": config.enabled,
        "mode": config.mode,
        "storage_ok": storage_ok,
        "ssh_allowed": config.ssh_allowed,
        "public_uploads_allowed": config.public_uploads_allowed,
        "version": _project_version(),
        "warnings": warnings,
        "errors": errors,
    }


@router.get("/nodes")
async def dev_server_list_nodes() -> dict[str, Any]:
    config = _get_config()
    if not config.enabled:
        raise HTTPException(status_code=403, detail={"code": "DEV_SERVER_DISABLED"})
    storage = _get_storage(config)
    nodes = storage.list_nodes()
    reports = storage.list_reports(limit=500)
    last_report_by_node: dict[str, dict[str, Any]] = {}
    for r in reports:
        nid = str(r.get("node_id") or "")
        if nid and nid not in last_report_by_node:
            last_report_by_node[nid] = r

    enriched = []
    for n in nodes:
        nid = str(n.get("node_id") or "")
        lr = last_report_by_node.get(nid)
        enriched.append({
            **n,
            "last_report_type": lr.get("report_type") if lr else None,
            "last_report_at": lr.get("created_at") if lr else None,
        })
    return {"code": "DEV_SERVER_NODES_OK", "nodes": enriched, "count": len(enriched)}


@router.get("/nodes/{node_id}")
async def dev_server_get_node(node_id: str) -> dict[str, Any]:
    config = _get_config()
    if not config.enabled:
        raise HTTPException(status_code=403, detail={"code": "DEV_SERVER_DISABLED"})
    storage = _get_storage(config)
    node = storage.load_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail={"code": "DEV_SERVER_NODE_NOT_FOUND"})
    return {"code": "DEV_SERVER_NODE_OK", "node": node}


@router.get("/reports")
async def dev_server_list_reports(
    limit: int = Query(default=100, ge=1, le=500),
    node_id: str | None = Query(default=None),
) -> dict[str, Any]:
    config = _get_config()
    if not config.enabled:
        raise HTTPException(status_code=403, detail={"code": "DEV_SERVER_DISABLED"})
    storage = _get_storage(config)
    reports = storage.list_reports(limit=limit, node_id=node_id)
    return {"code": "DEV_SERVER_REPORTS_OK", "reports": reports, "count": len(reports)}


@router.get("/reports/{report_id}")
async def dev_server_get_report(report_id: str) -> dict[str, Any]:
    config = _get_config()
    if not config.enabled:
        raise HTTPException(status_code=403, detail={"code": "DEV_SERVER_DISABLED"})
    storage = _get_storage(config)
    report = storage.load_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail={"code": "DEV_SERVER_REPORT_NOT_FOUND"})
    return {"code": "DEV_SERVER_REPORT_OK", "report": report}


@router.post("/ingest/report")
async def dev_server_ingest_report(
    body: IngestReportRequest,
    x_dev_server_token: str | None = Header(default=None, alias="X-Dev-Server-Token"),
) -> dict[str, Any]:
    config = _get_config()
    storage = _get_storage(config)
    result = ingest_report(
        config=config,
        storage=storage,
        node_data=body.node,
        report_data=body.report,
        auth_token=x_dev_server_token,
    )
    if result["code"] == "DEV_SERVER_REPORT_BLOCKED":
        status = 403
        if result.get("redaction_status") == "review_required":
            status = 202
        raise HTTPException(status_code=status, detail=result)
    return result


@router.get("/actions")
async def dev_server_list_actions(
    limit: int = Query(default=100, ge=1, le=500),
    node_id: str | None = Query(default=None),
) -> dict[str, Any]:
    config = _get_config()
    if not config.enabled:
        raise HTTPException(status_code=403, detail={"code": "DEV_SERVER_DISABLED"})
    storage = _get_storage(config)
    actions = storage.list_actions(limit=limit, node_id=node_id)
    return {"code": "DEV_SERVER_ACTIONS_OK", "actions": actions, "count": len(actions)}


@router.get("/actions/{action_id}")
async def dev_server_get_action(action_id: str) -> dict[str, Any]:
    config = _get_config()
    if not config.enabled:
        raise HTTPException(status_code=403, detail={"code": "DEV_SERVER_DISABLED"})
    storage = _get_storage(config)
    action = storage.load_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail={"code": "DEV_SERVER_ACTION_NOT_FOUND"})
    return {"code": "DEV_SERVER_ACTION_OK", "action": action}


@router.get("/summary")
async def dev_server_summary() -> dict[str, Any]:
    config = _get_config()
    storage = _get_storage(config)
    nodes = storage.list_nodes() if config.enabled else []
    actions = storage.list_actions(limit=200) if config.enabled else []
    reports = storage.list_reports(limit=200) if config.enabled else []

    online = sum(1 for n in nodes if n.get("status") == "online")
    busy = sum(1 for n in nodes if n.get("status") == "busy")
    error = sum(1 for n in nodes if n.get("status") == "error")
    open_actions = [a for a in actions if a.get("status") in ("queued", "running")]
    blocked_actions = [a for a in actions if a.get("status") == "blocked"]

    latest_findings = [
        {
            "report_id": r.get("report_id"),
            "node_id": r.get("node_id"),
            "report_type": r.get("report_type"),
            "created_at": r.get("created_at"),
            "warnings": (r.get("warnings") or [])[:3],
        }
        for r in reports[:10]
    ]

    return {
        "code": "DEV_SERVER_SUMMARY_OK",
        "enabled": config.enabled,
        "node_count": len(nodes),
        "online_count": online,
        "busy_count": busy,
        "error_count": error,
        "reports_last_24h": storage.reports_last_24h_count() if config.enabled else 0,
        "latest_findings": latest_findings,
        "open_actions": len(open_actions),
        "blocked_actions": len(blocked_actions),
        "prompt_candidates_count": 0,
        "generated_at": utc_now_iso(),
    }


@router.post("/nodes/{node_id}/ssh/check")
async def dev_server_ssh_check(node_id: str) -> dict[str, Any]:
    return _ssh_route(node_id, "ssh_check")


@router.post("/nodes/{node_id}/ssh/collect-inventory")
async def dev_server_ssh_collect_inventory(node_id: str) -> dict[str, Any]:
    return _ssh_route(node_id, "collect_inventory")


@router.post("/nodes/{node_id}/ssh/collect-storage")
async def dev_server_ssh_collect_storage(node_id: str) -> dict[str, Any]:
    return _ssh_route(node_id, "collect_storage")


@router.post("/nodes/{node_id}/ssh/collect-boot")
async def dev_server_ssh_collect_boot(node_id: str) -> dict[str, Any]:
    return _ssh_route(node_id, "collect_boot")


def _ssh_route(node_id: str, profile: str) -> dict[str, Any]:
    config = _get_config()
    storage = _get_storage(config)
    return execute_ssh_profile_action(
        config=config,
        storage=storage,
        node_id=node_id,
        profile_name=profile,
    )


@router.post("/prompt-candidates/from-reports")
async def dev_server_prompt_candidates(body: PromptCandidateFromReportsRequest) -> dict[str, Any]:
    config = _get_config()
    if not config.enabled:
        raise HTTPException(status_code=403, detail={"code": "DEV_SERVER_DISABLED"})
    storage = _get_storage(config)
    candidate = build_prompt_candidate_from_reports(body.report_ids, storage=storage)
    if candidate.get("status") == "failed":
        raise HTTPException(status_code=404, detail=candidate)
    return {"code": "DEV_SERVER_PROMPT_CANDIDATE_DRAFT", "candidate": candidate}
