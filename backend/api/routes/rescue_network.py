"""
Rescue network API — boot status and live network summary for rescue UI.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from core.rescue_network_connectivity_v2 import build_network_connectivity_v2
from core.rescue_network_live_status_v1 import build_live_boot_status
from core.rescue_network_telemetry_gate import build_compact_network_telemetry_status
from core.rescue_telemetry_connectivity_v1 import build_telemetry_connectivity_v1

router = APIRouter(tags=["rescue-network"])


@router.get("/network/live-status")
async def get_rescue_network_live_status() -> dict[str, Any]:
  return {
    "boot_status": build_live_boot_status(),
    "connectivity": build_network_connectivity_v2(),
    "telemetry": build_telemetry_connectivity_v1(),
    "gate": build_compact_network_telemetry_status(),
  }
