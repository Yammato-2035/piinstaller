"""
Security API router (Phase E.14) — scan, firewall, configure.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from core import security_handlers as handlers

router = APIRouter(tags=["security"])


@router.post("/api/security/scan")
async def security_scan_route():
    return await handlers.security_scan()


@router.get("/api/security/status")
async def security_status_route():
    return await handlers.security_status()


@router.post("/api/security/firewall/enable")
async def enable_firewall_route(request: Request):
    return await handlers.enable_firewall(request)


@router.post("/api/security/firewall/install")
async def install_firewall_route(request: Request):
    return await handlers.install_firewall(request)


@router.get("/api/security/firewall/rules")
async def get_firewall_rules_route():
    return await handlers.get_firewall_rules()


@router.post("/api/security/firewall/rules/add")
async def add_firewall_rule_route(request: Request):
    return await handlers.add_firewall_rule(request)


@router.delete("/api/security/firewall/rules/{rule_number}")
async def delete_firewall_rule_route(rule_number: int, request: Request):
    return await handlers.delete_firewall_rule(rule_number, request)


@router.post("/api/security/configure")
async def configure_security_route(request: Request):
    return await handlers.configure_security(request)
