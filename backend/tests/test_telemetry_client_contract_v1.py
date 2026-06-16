"""Telemetry client contract — public-safe, no server URL."""

from __future__ import annotations

import unittest

from core.telemetry_client_contract import (
    EXAMPLE_TELEMETRY_ENDPOINT,
    TelemetryClientEnvelope,
    TelemetryDataCategory,
    TelemetryOptInState,
    validate_client_envelope,
)


class TelemetryClientContractV1Tests(unittest.TestCase):
    def test_example_endpoint_is_placeholder(self) -> None:
        self.assertIn(".example", EXAMPLE_TELEMETRY_ENDPOINT)
        self.assertNotIn("ionos", EXAMPLE_TELEMETRY_ENDPOINT.lower())

    def test_disabled_opt_in_blocked(self) -> None:
        env = TelemetryClientEnvelope(
            schema_version=1,
            opt_in_state=TelemetryOptInState.DISABLED,
            data_categories=(TelemetryDataCategory.VERSION,),
            redaction_applied=True,
            local_preview_ok=True,
        )
        self.assertIn("opt_in_required", validate_client_envelope(env))

    def test_enabled_without_redaction_blocked(self) -> None:
        env = TelemetryClientEnvelope(
            schema_version=1,
            opt_in_state=TelemetryOptInState.ENABLED,
            data_categories=(TelemetryDataCategory.VERSION,),
            redaction_applied=False,
            local_preview_ok=True,
        )
        self.assertIn("redaction_required", validate_client_envelope(env))

    def test_public_dict_no_endpoint(self) -> None:
        env = TelemetryClientEnvelope(
            schema_version=1,
            opt_in_state=TelemetryOptInState.ENABLED,
            data_categories=(TelemetryDataCategory.RUNTIME_HEALTH,),
            redaction_applied=True,
            local_preview_ok=True,
        )
        d = env.to_public_dict()
        self.assertFalse(d["endpoint_configured"])
        self.assertNotIn("url", d)


if __name__ == "__main__":
    unittest.main()
