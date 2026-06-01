"""Pydantic-Schemas für Fleet-Session-API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FleetSessionWriteBody(BaseModel):
    run_id: str
    session_id: str | None = None
    session_type: str = "local_qemu_smoke"
    status: str | None = None
    severity: str | None = None
    label: str | None = None
    host: dict[str, Any] | None = None
    qemu: dict[str, Any] | None = None
    guest: dict[str, Any] | None = None
    serial: dict[str, Any] | None = None
    heartbeat: dict[str, Any] | None = None
    evidence_paths: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class FleetSessionPatchBody(BaseModel):
    status: str | None = None
    severity: str | None = None
    host: dict[str, Any] | None = None
    qemu: dict[str, Any] | None = None
    guest: dict[str, Any] | None = None
    serial: dict[str, Any] | None = None
    heartbeat: dict[str, Any] | None = None
    evidence_paths: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    qemu_exit_code: int | None = None


class FleetSessionFinishBody(BaseModel):
    status: str
    severity: str | None = None
    qemu: dict[str, Any] | None = None
    guest: dict[str, Any] | None = None
    serial: dict[str, Any] | None = None
    evidence_paths: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    qemu_exit_code: int | None = None
