"""Pydantic-Schemas für den Development Server."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

NodeKind = Literal["vm", "physical", "rescue_stick", "raspberry_pi", "unknown"]
LabMode = Literal["local_lab", "beta_opt_in", "public_rescue"]
NodeStatus = Literal["unknown", "online", "offline", "busy", "error"]
SshCheckStatus = Literal["not_configured", "ok", "failed", "disabled"]
ReportType = Literal[
    "inventory", "boot", "storage", "backup_preflight", "rescue", "ssh_probe", "manual"
]
RedactionStatus = Literal["raw_lab", "redacted", "not_required", "failed"]
ActionType = Literal[
    "ssh_check", "collect_inventory", "collect_storage", "collect_boot", "collect_basic_logs"
]
ActionStatus = Literal["queued", "running", "success", "failed", "blocked"]


class DevNodeSsh(BaseModel):
    enabled: bool = False
    host: str = ""
    port: int = 22
    username: str = ""
    auth_ref: str = ""
    last_check_status: SshCheckStatus = "not_configured"
    last_check_error: str = ""


class DevNodeSchema(BaseModel):
    node_id: str = Field(..., min_length=1, max_length=128)
    display_name: str = ""
    node_kind: NodeKind = "unknown"
    lab_mode: LabMode = "local_lab"
    last_seen_at: str = ""
    status: NodeStatus = "unknown"
    current_action: str | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str = ""
    ssh: DevNodeSsh = Field(default_factory=DevNodeSsh)


class DevReportSchema(BaseModel):
    report_id: str = Field(..., min_length=1, max_length=128)
    node_id: str = Field(..., min_length=1, max_length=128)
    created_at: str = ""
    report_type: ReportType = "manual"
    lab_mode: LabMode = "local_lab"
    setuphelfer_version: str = ""
    rescue_build_id: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    redaction_status: RedactionStatus = "raw_lab"
    evidence_paths: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class DevActionSchema(BaseModel):
    action_id: str = Field(..., min_length=1, max_length=128)
    node_id: str = Field(..., min_length=1, max_length=128)
    requested_at: str = ""
    started_at: str | None = None
    finished_at: str | None = None
    requested_by: str = "developer_dashboard"
    action_type: ActionType = "ssh_check"
    mode: Literal["read_only"] = "read_only"
    status: ActionStatus = "queued"
    command_profile: str = ""
    commands: list[str] = Field(default_factory=list)
    stdout_excerpt: str = ""
    stderr_excerpt: str = ""
    exit_code: int | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class IngestReportRequest(BaseModel):
    node: dict[str, Any] = Field(default_factory=dict)
    report: dict[str, Any] = Field(default_factory=dict)


class PromptCandidateFromReportsRequest(BaseModel):
    report_ids: list[str] = Field(default_factory=list)
