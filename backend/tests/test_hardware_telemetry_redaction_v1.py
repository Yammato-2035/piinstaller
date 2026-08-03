"""PI-RS-HW-COMPAT-PROVISION-001 Phase 16: hardware_telemetry_contract.py +
hardware_dcc_status.py tests.

Fixture group per spec PHASE 17: "Telemetrie mit Seriennummer muss blockiert oder
redigiert werden".
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_dcc_status import build_hardware_dcc_status_fields
from core.hardware_telemetry_contract import (
    HARDWARE_TELEMETRY_SCHEMA_ID,
    build_hardware_inventory_summary_v1,
    build_hardware_telemetry_contract_diagnostics,
    validate_hardware_telemetry_payload,
)

_BASE_SUMMARY = {
    "platform_class": "laptop",
    "architecture": "x86_64",
    "is_raspberry_pi": False,
    "device_count_by_class": {"pci": 12, "usb": 5},
    "device_count_by_operational_status": {"ready": 10, "unknown": 7},
}


class TestAllowlistPayload(unittest.TestCase):
    def test_schema_id_and_contract_version_present(self) -> None:
        payload = build_hardware_inventory_summary_v1(inventory_summary=_BASE_SUMMARY)
        self.assertEqual(payload["schema_id"], HARDWARE_TELEMETRY_SCHEMA_ID)
        self.assertIn("contract_version", payload)

    def test_only_allowlisted_top_level_keys_exist(self) -> None:
        payload = build_hardware_inventory_summary_v1(inventory_summary=_BASE_SUMMARY)
        allowed = {
            "schema_id",
            "contract_version",
            "platform_class",
            "architecture",
            "is_raspberry_pi",
            "raspberry_pi_model_family",
            "cpu_vendor",
            "cpu_model_family",
            "gpu_vendor",
            "gpu_model_class",
            "device_count_by_class",
            "device_count_by_operational_status",
            "rescue_payload_version",
            "kernel_version",
            "known_issue_codes",
            "correlation_id",
            "evidence_hashes",
        }
        self.assertEqual(set(payload.keys()), allowed)

    def test_device_counts_are_aggregates_not_raw_rows(self) -> None:
        payload = build_hardware_inventory_summary_v1(inventory_summary=_BASE_SUMMARY)
        self.assertEqual(payload["device_count_by_class"], {"pci": 12, "usb": 5})
        self.assertNotIn("devices", payload)

    def test_version_scheme_dotted_quad_not_mangled_as_ip(self) -> None:
        """Setuphelfer's own X.Y.Z.W version scheme looks IP-shaped but must survive
        the redaction pass unchanged."""
        payload = build_hardware_inventory_summary_v1(
            inventory_summary=_BASE_SUMMARY, rescue_payload_version="1.10.6.0", kernel_version="6.8.0-generic"
        )
        self.assertEqual(payload["rescue_payload_version"], "1.10.6.0")
        self.assertEqual(payload["kernel_version"], "6.8.0-generic")

    def test_descriptive_field_with_embedded_ip_gets_redacted(self) -> None:
        payload = build_hardware_inventory_summary_v1(
            inventory_summary=_BASE_SUMMARY, cpu_model_family="Ryzen 9 (seen at 192.168.1.5)"
        )
        self.assertIn("[REDACTED:ip]", payload["cpu_model_family"])
        self.assertNotIn("192.168.1.5", payload["cpu_model_family"])


class TestHardBlockValidation(unittest.TestCase):
    def test_clean_payload_has_no_violations(self) -> None:
        payload = build_hardware_inventory_summary_v1(
            inventory_summary=_BASE_SUMMARY,
            rescue_payload_version="1.10.6.0",
            correlation_id="corr-abc-123",
            evidence_hashes=["sha256:deadbeef"],
        )
        self.assertEqual(validate_hardware_telemetry_payload(payload), [])

    def test_serial_number_value_is_blocked(self) -> None:
        payload = build_hardware_inventory_summary_v1(inventory_summary=_BASE_SUMMARY)
        payload["leaked_field"] = "SN1234567890AB"
        violations = validate_hardware_telemetry_payload(payload)
        self.assertTrue(any("serial_like_value" in v for v in violations))

    def test_mac_address_key_is_blocked(self) -> None:
        payload = build_hardware_inventory_summary_v1(inventory_summary=_BASE_SUMMARY)
        payload["mac_address"] = "AA:BB:CC:DD:EE:FF"
        violations = validate_hardware_telemetry_payload(payload)
        self.assertTrue(any("forbidden_key:mac_address" in v for v in violations))

    def test_ip_address_key_is_blocked(self) -> None:
        payload = build_hardware_inventory_summary_v1(inventory_summary=_BASE_SUMMARY)
        payload["device_ip_address"] = "10.0.0.5"
        violations = validate_hardware_telemetry_payload(payload)
        self.assertTrue(any("forbidden_key:device_ip_address" in v for v in violations))

    def test_hostname_key_is_blocked(self) -> None:
        payload = build_hardware_inventory_summary_v1(inventory_summary=_BASE_SUMMARY)
        payload["hostname"] = "operator-laptop"
        violations = validate_hardware_telemetry_payload(payload)
        self.assertTrue(any("forbidden_key:hostname" in v for v in violations))

    def test_already_redacted_placeholder_is_not_flagged_again(self) -> None:
        payload = build_hardware_inventory_summary_v1(inventory_summary=_BASE_SUMMARY)
        payload["some_field"] = "[REDACTED:ip]"
        self.assertEqual(validate_hardware_telemetry_payload(payload), [])


class TestDiagnostics(unittest.TestCase):
    def test_no_network_upload_performed(self) -> None:
        diag = build_hardware_telemetry_contract_diagnostics()
        self.assertFalse(diag["network_upload_performed"])
        self.assertTrue(diag["allowlist_only"])


class TestDccHardwareStatusFields(unittest.TestCase):
    def test_expected_status_fields_present(self) -> None:
        fields = build_hardware_dcc_status_fields()
        for key in (
            "hardware_detection_status",
            "driver_resolution_status",
            "firmware_coverage_status",
            "printer_scanner_detection_status",
            "raspberry_pi_coverage_status",
            "carrier_feasibility_status",
            "provisioning_catalog_status",
            "physical_matrix_status",
        ):
            self.assertIn(key, fields)

    def test_no_status_field_claims_a_forbidden_absolute(self) -> None:
        fields = build_hardware_dcc_status_fields()
        forbidden = {
            "all_hardware_supported",
            "raspberry_pi_3_to_5_verified",
            "printer_support_complete",
            "gpu_support_complete",
            "universal_64gb_stick_verified",
            "operating_system_installation_verified",
            "production_ready",
        }
        values = {v for k, v in fields.items() if k.endswith("_status")}
        self.assertEqual(values & forbidden, set())

    def test_missing_repo_root_does_not_crash(self) -> None:
        fields = build_hardware_dcc_status_fields(repo_root=Path("/nonexistent/repo/root"))
        self.assertEqual(fields["hardware_detection_status"], "not_started")


if __name__ == "__main__":
    unittest.main()
