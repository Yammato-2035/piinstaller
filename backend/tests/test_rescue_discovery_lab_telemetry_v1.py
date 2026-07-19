"""Tests for anonymized discovery lab telemetry + USB wait fix."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.rescue_discovery_lab_telemetry import (
    build_anonymized_discovery_summary,
    send_discovery_lab_telemetry,
)
from core.rescue_stick_cloud_lab_models import RescueStickLabSendStatus
from core.rescue_stick_cloud_lab_payload import assert_no_pii_in_payload, build_rescue_stick_lab_payload


class AnonymizedDiscoverySummaryTests(unittest.TestCase):
    def test_summary_has_hashes_not_raw_ids(self) -> None:
        summary = build_anonymized_discovery_summary(
            state={
                "session_id": "rescue-session-20260717T195854Z-209f4ec9",
                "boot_id": "dd71bd7a-87be-4e3b-8ce4-3ac67b3515b7",
                "payload_version": "1.10.0.37",
                "run_mode": "auto_discovery_only",
            },
            gate={"status": "review_required", "privacy_gate_passed": False, "secret_gate_passed": True},
            machine={
                "vendor_class": "msi",
                "model_family": "GE63 Raider",
                "architecture": "x86_64",
                "product_name": "GE63 Raider RGB 8RF",
            },
            modules_completed=["machine", "storage"],
        )
        self.assertEqual(summary["vendor_class"], "msi")
        self.assertEqual(summary["status"], "review_required")
        self.assertTrue(str(summary["session_id_hash"]).startswith("sha256:"))
        self.assertNotIn("209f4ec9", json.dumps(summary))
        self.assertNotIn("product_name", summary)
        payload = build_rescue_stick_lab_payload(
            stick_version="1.10.0.37",
            boot_mode="lab_auto_discovery",
            discovery_summary=summary,
        )
        assert_no_pii_in_payload(payload)
        self.assertEqual(payload["event_type"], "rescue_stick.discovery_evidence")
        self.assertIn("discovery_summary", payload)


class DiscoveryLabSendTests(unittest.TestCase):
    def test_send_uses_discovery_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            token = Path(tmp) / "token"
            token.write_text("lab-token-value\n", encoding="utf-8")
            captured: dict = {}

            def fake_transport(url, body, headers, timeout_seconds):
                captured["url"] = url
                captured["body"] = json.loads(body.decode("utf-8"))
                captured["auth"] = headers.get("Authorization", "")
                return 200, json.dumps({"accepted": True, "request_id": "req-test"}), {"X-Request-Id": "req-test"}

            with patch.dict(
                "os.environ",
                {
                    "SETUPHELFER_RS_TELEMETRY_LAB_SEND_ENABLED": "1",
                    "SETUPHELFER_RS_TELEMETRY_OPERATOR_APPROVAL": "explicit",
                    "SETUPHELFER_RS_TELEMETRY_CONSENT_STATUS": "granted_lab",
                    "SETUPHELFER_RS_TELEMETRY_LAB_TOKEN_FILE": str(token),
                    "SETUPHELFER_RS_TELEMETRY_ENDPOINT": "https://telemetrie.setuphelfer.de/v1/telemetry/ingest",
                },
                clear=False,
            ), patch(
                "core.rescue_stick_cloud_lab_send._default_health_check",
                return_value="health_ok",
            ), patch(
                "core.rescue_stick_cloud_lab_send._default_http_transport",
                side_effect=fake_transport,
            ):
                result = send_discovery_lab_telemetry(
                    state={
                        "session_id": "rescue-session-x",
                        "boot_id": "boot-y",
                        "payload_version": "1.10.0.37",
                        "run_mode": "auto_discovery_only",
                    },
                    gate={"status": "review_required", "privacy_gate_passed": False, "secret_gate_passed": True},
                    machine={"vendor_class": "msi", "model_family": "GE63 Raider", "architecture": "x86_64"},
                    modules_completed=["machine"],
                )
            self.assertTrue(result["accepted"])
            self.assertEqual(result["send_status"], RescueStickLabSendStatus.LAB_SEND_ACCEPTED.value)
            self.assertEqual(captured["body"]["event_type"], "rescue_stick.discovery_evidence")
            self.assertIn("discovery_summary", captured["body"])
            self.assertTrue(captured["auth"].startswith("Bearer "))


class UsbWaitKeyTests(unittest.TestCase):
    def test_wait_exits_when_disks_present_without_targets(self) -> None:
        from core import rescue_auto_discovery_orchestrator as orch

        calls = {"n": 0}

        def fake_discover():
            calls["n"] += 1
            return {
                "classified": [{"type": "disk", "path": "/dev/nvme0n1"}],
                "target_candidates": [],
            }

        with patch.object(orch, "discover_rescue_storage", side_effect=fake_discover), patch.object(
            orch, "set_phase"
        ), patch.object(orch, "heartbeat"), patch.object(orch.subprocess, "run"):
            orch._wait_usb_devices(max_wait_sec=30)
        self.assertEqual(calls["n"], 1)


if __name__ == "__main__":
    unittest.main()
