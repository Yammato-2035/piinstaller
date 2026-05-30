"""Agent-Datenmodelle und Report-/Node-Builder."""

from __future__ import annotations

import os
import socket
import uuid
from datetime import datetime, timezone
from typing import Any

UTC = timezone.utc


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def new_report_id() -> str:
    return f"report-{uuid.uuid4().hex[:16]}"


def default_node_id() -> str:
    return f"rescue-dev-{uuid.uuid4().hex[:12]}"


def build_dev_node(
    *,
    node_id: str,
    display_name: str,
    mode: str,
    node_kind: str = "rescue_stick",
) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "display_name": display_name or node_id,
        "node_kind": node_kind,
        "lab_mode": mode,
        "status": "online",
        "tags": ["dev_agent"],
        "notes": "Setuphelfer development agent",
    }


def build_dev_report(
    *,
    report_id: str,
    node_id: str,
    report_type: str,
    mode: str,
    payload: dict[str, Any],
    setuphelfer_version: str = "",
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "node_id": node_id,
        "created_at": utc_now_iso(),
        "report_type": report_type,
        "lab_mode": mode,
        "setuphelfer_version": setuphelfer_version,
        "rescue_build_id": os.environ.get("SETUPHELFER_RESCUE_BUILD_ID", ""),
        "payload": payload,
        "redaction_status": "raw_lab" if mode == "local_lab" else "not_required",
        "warnings": warnings or [],
        "errors": errors or [],
    }


def resolve_node_identity(config_node_id: str, config_display_name: str) -> tuple[str, str]:
    node_id = config_node_id.strip() or default_node_id()
    display_name = config_display_name.strip() or node_id
    return node_id, display_name
