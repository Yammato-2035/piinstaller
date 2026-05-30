"""Tests für devserver.redaction."""

from __future__ import annotations

import unittest

from devserver.redaction import (
    apply_lab_mode_redaction,
    detect_forbidden_sensitive_fields,
    hash_sensitive_value,
    redact_hardware_inventory,
    redact_report_for_beta,
    redact_storage_topology,
)


class DevServerRedactionTests(unittest.TestCase):
    def test_hostname_hashed(self) -> None:
        out = redact_hardware_inventory({"hostname": "my-laptop.local", "cpu": {"model": "x"}})
        self.assertNotEqual(out["hostname"], "my-laptop.local")
        self.assertTrue(str(out["hostname"]).startswith("sha256:"))

    def test_username_hashed(self) -> None:
        out = redact_hardware_inventory({"username": "volker"})
        self.assertTrue(str(out["username"]).startswith("sha256:"))

    def test_mac_hashed(self) -> None:
        out = redact_hardware_inventory({"note": "NIC aa:bb:cc:dd:ee:ff seen"})
        self.assertNotIn("aa:bb:cc:dd:ee:ff", out["note"])

    def test_disk_serial_hashed(self) -> None:
        out = redact_storage_topology({"block_devices": [{"serial": "S123456789"}]})
        dev = out["block_devices"][0]
        self.assertNotIn("S123456789", str(dev))

    def test_beta_forbidden_fields_redacted(self) -> None:
        report = {
            "report_id": "r1",
            "node_id": "n1",
            "report_type": "inventory",
            "payload": {"hostname": "secret-host", "cpu": {}},
        }
        out, warnings, errors = apply_lab_mode_redaction(report, "beta_opt_in")
        self.assertEqual(out["redaction_status"], "redacted")
        self.assertIn("forbidden_fields_redacted", warnings)
        self.assertFalse(errors)

    def test_local_lab_raw_allowed(self) -> None:
        report = {
            "report_id": "r1",
            "node_id": "n1",
            "payload": {"hostname": "lab-host"},
        }
        out, _, errors = apply_lab_mode_redaction(report, "local_lab")
        self.assertEqual(out["redaction_status"], "raw_lab")
        self.assertEqual(out["payload"]["hostname"], "lab-host")
        self.assertFalse(errors)

    def test_detect_forbidden_fields(self) -> None:
        found = detect_forbidden_sensitive_fields({"email": "a@b.c", "cpu": {}})
        self.assertTrue(any("email" in f for f in found))

    def test_hash_stable(self) -> None:
        a = hash_sensitive_value("x", "scope")
        b = hash_sensitive_value("x", "scope")
        self.assertEqual(a, b)

    def test_redact_report_for_beta(self) -> None:
        report = redact_report_for_beta({
            "report_type": "inventory",
            "payload": {"hostname": "h1"},
        })
        self.assertEqual(report["redaction_status"], "redacted")


if __name__ == "__main__":
    unittest.main()
