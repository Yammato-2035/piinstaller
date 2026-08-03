"""
64-GB carrier capacity planner — byte-accurate, no partitioning.

PI-RS-HW-COMPAT-PROVISION-001 Phase 12 (capacity planner half).

Real media byte counts MUST come from ``core.storage_facade`` (the existing,
tested storage facade) — this module never runs its own ``lsblk``/``blockdev``
(see audit doc "hoch, falls neu implementiert" risk note). No ``dd``, ``mkfs``,
``parted``, ``sfdisk``, ``sgdisk`` or ``wipefs`` calls exist in this module.
"""

from __future__ import annotations

from typing import Any

from rescue.carrier_content_catalog import CARRIER_CONTENT_COMPONENTS, get_required_components

CARRIER_CAPACITY_PLANNER_VERSION = 1

MIN_SAFETY_RESERVE_RATIO = 0.10  # spec: "mindestens 10% Sicherheitsreserve"


def get_real_carrier_size_bytes(device_path: str, *, runner: Any = None) -> int | None:
    """Thin, explicit delegation to the existing storage facade (single source of
    truth for block-device byte sizes)."""
    from core.storage_facade import get_block_device_size_bytes

    return get_block_device_size_bytes(device_path, runner=runner)


def compute_capacity_plan(
    *,
    carrier_size_bytes: int,
    include_optional_components: list[str] | None = None,
    safety_reserve_ratio: float = MIN_SAFETY_RESERVE_RATIO,
) -> dict[str, Any]:
    """Pure byte arithmetic — never touches a real device. ``carrier_size_bytes``
    must be the *actual* measured size (see ``get_real_carrier_size_bytes``), not an
    assumption like "64 GB == 64 * 1024**3" (spec: "nicht blind von 64 GB ausgehen")."""
    if carrier_size_bytes <= 0:
        return {
            "carrier_size_bytes": carrier_size_bytes,
            "layout_status": "blocked",
            "warnings": ["carrier_size_bytes_must_be_positive"],
        }

    reserved_bytes = int(carrier_size_bytes * max(safety_reserve_ratio, MIN_SAFETY_RESERVE_RATIO))
    usable_bytes = carrier_size_bytes - reserved_bytes

    required = get_required_components()
    optional_ids = set(include_optional_components or [])
    optional = [c for c in CARRIER_CONTENT_COMPONENTS if not c["required"] and c["component_id"] in optional_ids]

    required_bytes = sum(c["estimated_bytes"] for c in required)
    optional_bytes = sum(c["estimated_bytes"] for c in optional)

    runtime_bytes = next((c["estimated_bytes"] for c in required if c["component_id"] == "rescue_runtime"), 0)
    driver_cache_bytes = next(
        (c["estimated_bytes"] for c in optional if c["component_id"] == "driver_firmware_offline_packages"), 0
    )
    image_cache_component = next(
        (c["estimated_bytes"] for c in optional if c["component_id"] == "os_image_cache"), 0
    )
    evidence_bytes = next((c["estimated_bytes"] for c in required if c["component_id"] == "evidence_and_logs"), 0)

    total_needed = required_bytes + optional_bytes
    warnings: list[str] = []
    if total_needed > usable_bytes:
        layout_status = "blocked"
        warnings.append("required_plus_optional_components_exceed_usable_capacity")
    elif total_needed > usable_bytes * 0.8:
        layout_status = "review_required"
        warnings.append("less_than_20_percent_headroom_after_selected_components")
    else:
        layout_status = "ok"

    # Very rough per-image estimate for max_cached_images (image_cache_component
    # divided by a conservative single-image size assumption; refined once Phase 13
    # catalog entries with real sha256/size exist).
    assumed_single_image_bytes = 2 * 1024**3
    max_cached_images = int(image_cache_component // assumed_single_image_bytes) if image_cache_component else 0

    recommended_strategy = "orchestrator_cache"  # see carrier_layout.evaluate_carrier_strategy for the full rationale

    return {
        "schema_version": "carrier-capacity-plan.v1",
        "carrier_size_bytes": carrier_size_bytes,
        "safety_reserve_ratio": max(safety_reserve_ratio, MIN_SAFETY_RESERVE_RATIO),
        "reserved_bytes": reserved_bytes,
        "usable_bytes": usable_bytes,
        "required_bytes": required_bytes,
        "optional_selected_bytes": optional_bytes,
        "runtime_bytes": runtime_bytes,
        "driver_cache_bytes": driver_cache_bytes,
        "image_cache_bytes": image_cache_component,
        "evidence_bytes": evidence_bytes,
        "max_cached_images": max_cached_images,
        "layout_status": layout_status,
        "recommended_strategy": recommended_strategy,
        "warnings": warnings,
        "partitioning_performed": False,
    }


def build_carrier_capacity_planner_diagnostics() -> dict[str, Any]:
    return {
        "planner_version": CARRIER_CAPACITY_PLANNER_VERSION,
        "module": "rescue.carrier_capacity_planner",
        "min_safety_reserve_ratio": MIN_SAFETY_RESERVE_RATIO,
        "uses_storage_facade_for_real_size": True,
        "partitioning_performed": False,
        "dd_used": False,
        "mkfs_used": False,
    }


__all__ = [
    "CARRIER_CAPACITY_PLANNER_VERSION",
    "MIN_SAFETY_RESERVE_RATIO",
    "get_real_carrier_size_bytes",
    "compute_capacity_plan",
    "build_carrier_capacity_planner_diagnostics",
]
