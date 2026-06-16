"""
MSI Windows read-only API router (Phase F.1).

Plan-only / parse-readonly — no backup, restore, wipe, or credential endpoints.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from core import msi_windows_handlers as handlers

router = APIRouter(tags=["msi-windows"])


@router.get("/api/msi/windows/precheck/schema")
async def msi_windows_precheck_schema_route():
    return await handlers.get_precheck_schema()


@router.get("/api/msi/windows/capabilities")
async def msi_windows_capabilities_route():
    return await handlers.get_capabilities()


@router.post("/api/msi/windows/precheck/parse-readonly")
async def msi_windows_parse_readonly_route(body: dict[str, Any] = Body(...)):
    return await handlers.parse_readonly_precheck(body)
