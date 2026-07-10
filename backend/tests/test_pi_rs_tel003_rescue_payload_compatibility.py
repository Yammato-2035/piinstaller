"""PI-RS-TEL-003 rescue payload compatibility tests."""

from __future__ import annotations

import json

from core.rescue_lab_telemetry_cross_repo_preview import (
    build_diagnostics_cloudserver_payload_from_rescue,
    build_rescue_cross_repo_telemetry_payload,
    validate_cross_repo_preview_contract,
)


def test_rescue_payload_has_diagnostics_aggregates():
    payload = build_rescue_cross_repo_telemetry_payload()
    assert isinstance(payload.get("diagnostics_aggregates"), dict)
    assert payload["diagnostics_aggregates"]["plesk"]["version_status"] == "unknown"


def test_cloudserver_payload_compatible_shape():
    rescue = build_rescue_cross_repo_telemetry_payload()
    cloudserver = build_diagnostics_cloudserver_payload_from_rescue(rescue)
    assert cloudserver["payload_kind"] == "cloudserver_collector_preview"
    assert cloudserver["production_ready"] is False
    assert cloudserver["contains_pii"] is False
    assert cloudserver["collector"]["plesk_write_access"] is False
    assert "aggregates" in cloudserver


def test_no_secrets_in_payload():
    payload = build_rescue_cross_repo_telemetry_payload()
    blob = json.dumps(payload)
    assert "Bearer" not in blob
    assert "password" not in blob.lower()
    assert "@" not in blob


def test_missing_optional_aggregates_defaults():
    rescue = build_rescue_cross_repo_telemetry_payload()
    rescue.pop("diagnostics_aggregates", None)
    cloudserver = build_diagnostics_cloudserver_payload_from_rescue(rescue)
    assert cloudserver["aggregates"]["dns"]["records_status"] == "unknown"
