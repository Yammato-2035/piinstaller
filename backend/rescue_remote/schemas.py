"""Pydantic schemas for rescue remote control API (phase 1)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

RunbookMode = Literal["read_only", "diagnostic"]
AgentMode = Literal["local_lab", "rescue_user", "school", "production"]


class AgentCapabilities(BaseModel):
    read_logs: bool = True
    run_readonly_runbooks: bool = True
    run_write_runbooks: bool = False
    network_info: bool = True


class AgentNetwork(BaseModel):
    interface: str = "unknown"
    ip: str = ""
    gateway: str = ""
    dev_server_url: str = ""


class AgentSecurity(BaseModel):
    paired: bool = False
    server_fingerprint: str = ""
    agent_fingerprint: str = ""
    token_expires_at: str = ""
    remote_shell: bool = False
    controlled_write: bool = False


class AgentRegisterRequest(BaseModel):
    agent_id: str = Field(..., min_length=8, max_length=128)
    boot_id: str = Field(..., min_length=4, max_length=128)
    session_id: str = ""
    mode: AgentMode = "local_lab"
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    network: AgentNetwork = Field(default_factory=AgentNetwork)
    security: AgentSecurity = Field(default_factory=AgentSecurity)
    pairing_token: str = Field(default="", max_length=256)

    @field_validator("mode")
    @classmethod
    def phase1_mode(cls, v: str) -> str:
        if v != "local_lab":
            raise ValueError("phase1_only_local_lab")
        return v

    @field_validator("capabilities")
    @classmethod
    def no_write_capabilities(cls, v: AgentCapabilities) -> AgentCapabilities:
        if v.run_write_runbooks:
            raise ValueError("write_runbooks_disabled_phase1")
        return v


class AgentHeartbeatRequest(BaseModel):
    agent_id: str
    boot_id: str = ""
    status: str = "online"
    network: AgentNetwork | None = None


class JobCreateRequest(BaseModel):
    agent_id: str
    runbook_id: str
    mode: RunbookMode = "read_only"
    requires_operator_consent: bool = False
    timeout_seconds: int = Field(default=30, ge=5, le=600)
    command_plan: list[Any] = Field(default_factory=list)
    redaction: bool = True

    @field_validator("command_plan")
    @classmethod
    def no_command_plan(cls, v: list[Any]) -> list[Any]:
        if v:
            raise ValueError("command_plan_not_allowed_phase1")
        return v


class JobResultRequest(BaseModel):
    agent_id: str
    status: Literal["success", "failed", "timeout", "blocked"] = "success"
    result: dict[str, Any] = Field(default_factory=dict)


class AgentDisconnectRequest(BaseModel):
    agent_id: str
    reason: str = "operator_disconnect"
