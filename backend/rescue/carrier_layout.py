"""
64-GB carrier strategy evaluation — Variant A/B/C comparison, no partitioning.

PI-RS-HW-COMPAT-PROVISION-001 Phase 12 (strategy evaluation half).

Variant A: universal x86_64 + Raspberry Pi bootable single stick.
Variant B: shared build catalog, separate x86 and ARM carriers.
Variant C: universal rescue/orchestrator stick with downloadable/cached target images.

Spec rule: no variant may be marked "decided" without technical evidence. As of
this phase, no evidence of a validated universal (single boot sector/ESP serving
both x86_64 BIOS/UEFI and Raspberry Pi's SD/EEPROM boot process) boot path exists
in this repository (see docs/evidence/rescue/hardware-compat-001/
HARDWARE_DISCOVERY_IST_AUDIT.md) — so Variant C is the spec-mandated default
unless/until such evidence is produced.
"""

from __future__ import annotations

from typing import Any

CARRIER_LAYOUT_VERSION = 1

_VARIANTS: dict[str, dict[str, Any]] = {
    "universal": {
        "variant_label": "A",
        "description": "Single stick bootable natively on both x86_64 and Raspberry Pi",
        "requires_evidence": "validated_single_boot_path_for_x86_and_pi",
    },
    "split_carriers": {
        "variant_label": "B",
        "description": "Shared build catalog, separate physical x86 and ARM/Pi carriers",
        "requires_evidence": "none_required_but_requires_two_physical_sticks",
    },
    "orchestrator_cache": {
        "variant_label": "C",
        "description": "Universal rescue/orchestrator stick with downloadable/cached target OS images",
        "requires_evidence": "none_required_default_per_spec",
    },
}


def evaluate_carrier_strategy(
    *,
    universal_boot_path_evidence: bool = False,
    split_carrier_operationally_acceptable: bool | None = None,
) -> dict[str, Any]:
    """Return the strategy decision. Only ever returns ``decision_status="decided"``
    for Variant A when ``universal_boot_path_evidence=True`` is explicitly passed by
    a caller that actually has that evidence — this function never assumes it."""
    if universal_boot_path_evidence:
        return {
            "schema_version": "carrier-strategy-decision.v1",
            "recommended_strategy": "universal",
            "decision_status": "decided",
            "rationale": "validated_single_boot_path_evidence_provided_by_caller",
            "variants_considered": _VARIANTS,
        }

    if split_carrier_operationally_acceptable is True:
        return {
            "schema_version": "carrier-strategy-decision.v1",
            "recommended_strategy": "split_carriers",
            "decision_status": "review_required",
            "rationale": "no_universal_boot_evidence_but_operator_accepted_two_physical_sticks",
            "variants_considered": _VARIANTS,
        }

    return {
        "schema_version": "carrier-strategy-decision.v1",
        "recommended_strategy": "orchestrator_cache",
        "decision_status": "decided_by_spec_default",
        "rationale": "no_validated_universal_boot_path_evidence_exists_yet_spec_mandates_variant_c_default",
        "variants_considered": _VARIANTS,
    }


def build_carrier_layout_diagnostics() -> dict[str, Any]:
    return {
        "layout_version": CARRIER_LAYOUT_VERSION,
        "module": "rescue.carrier_layout",
        "partitioning_performed": False,
        "variants": sorted(_VARIANTS.keys()),
    }


__all__ = [
    "CARRIER_LAYOUT_VERSION",
    "evaluate_carrier_strategy",
    "build_carrier_layout_diagnostics",
]
