"""Rescue UI screenshot API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.rescue_ui_screenshot import build_screenshot_capabilities, capture_rescue_screenshot

router = APIRouter(prefix="/api/rescue/ui", tags=["rescue-ui"])


class RescueScreenshotRequest(BaseModel):
    label: str = Field(default="ui", max_length=49)


@router.get("/screenshot/capabilities")
async def get_rescue_ui_screenshot_capabilities() -> dict[str, Any]:
    return build_screenshot_capabilities()


@router.post("/screenshot")
async def post_rescue_ui_screenshot(body: RescueScreenshotRequest) -> dict[str, Any]:
    return capture_rescue_screenshot(body.label)
