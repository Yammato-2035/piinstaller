"""PI-RS-TEL-003 contract tests."""

from __future__ import annotations

from pathlib import Path

from core.rescue_lab_telemetry_cross_repo_preview import (
    CSE_TARGET_COMPATIBILITY,
    DIAGNOSTICS_CONTRACT_REFERENCE,
    build_rescue_cross_repo_telemetry_payload,
    validate_cross_repo_preview_contract,
)


def test_contract_document_exists():
    contract = Path(__file__).resolve().parents[2] / "docs/contracts/PI_RS_TEL_003_CROSS_REPO_PREVIEW_CONTRACT.md"
    text = contract.read_text(encoding="utf-8")
    assert CSE_TARGET_COMPATIBILITY in text
    assert DIAGNOSTICS_CONTRACT_REFERENCE in text
    assert "production_ready=false" in text


def test_contract_payload_fields():
    payload = build_rescue_cross_repo_telemetry_payload()
    ok, errors = validate_cross_repo_preview_contract(payload)
    assert ok, errors
    assert payload["source_kind"] == "rescue_stick"
    assert payload["event_kind"] == "rescue_stick_cross_repo_preview"
    assert payload["cross_repo"]["cse_target_compatibility"] == CSE_TARGET_COMPATIBILITY
    assert payload["cross_repo"]["diagnostics_contract_reference"] == DIAGNOSTICS_CONTRACT_REFERENCE
