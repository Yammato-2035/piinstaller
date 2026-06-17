"""Rescue restore preview plan-only API handlers (RS-F2S)."""

from __future__ import annotations

from typing import Any

from core.rescue_restore_preview_contract import restore_preview_preflight


async def post_restore_preview_preflight(body: dict[str, Any]) -> dict[str, Any]:
    return restore_preview_preflight(body)
