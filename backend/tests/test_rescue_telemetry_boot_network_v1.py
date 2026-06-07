"""Rescue boot network telemetry ingest schema tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_telemetry_ingest import (  # noqa: E402
    compute_payload_hash,
    process_telemetry_ingest,
    validate_boot_network_envelope,
)


def _boot_network_payload(**overrides: object) -> dict:
    payload = {
        "schema_version": 1,
        "source": "rescue_stick",
        "payload_kind": "rescue_boot_network_telemetry",
        "boot_id": "boot-test-001",
        "machine_hint": "msi",
        "timestamp": "2026-06-07T12:00:00Z",
        "iso_sha256": "9ef1b330c6ec774dfa1966c2f87c3c3ef31b3adf421f64fa2375c90408f21f3a",
        "network": {"wifi_connected": True},
        "hardware": {"cpu_vendor": "Intel"},
        "kernel_warnings": {"pcie": "corrected"},
        "media_check": {"live_media_runtime_stable": True},
        "operator_notes": [],
    }
    payload.update(overrides)
    payload["payload_hash_sha256"] = compute_payload_hash(payload)
    return payload


class RescueBootNetworkIngestTests(unittest.TestCase):
    def test_validate_boot_network_envelope_ok(self) -> None:
        ok, code = validate_boot_network_envelope(_boot_network_payload())
        self.assertTrue(ok)
        self.assertIsNone(code)

    def test_wrong_payload_kind_rejected(self) -> None:
        ok, _ = validate_boot_network_envelope(_boot_network_payload(payload_kind="windows_rescue_inspect"))
        self.assertFalse(ok)

    def test_ingest_ack_boot_network(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = type(
                "Cfg",
                (),
                {
                    "enabled": True,
                    "ingest_token_configured": False,
                    "hmac_required": False,
                    "storage_root": root,
                    "queue_dir": root / "queue",
                    "ingest_dir": root / "received",
                    "ack_dir": root / "acks",
                },
            )()
            envelope = _boot_network_payload()
            raw = json.dumps(envelope, sort_keys=True).encode("utf-8")
            result = process_telemetry_ingest(
                envelope,
                headers={"X-Setuphelfer-Payload-Hash": envelope["payload_hash_sha256"]},
                body_bytes=raw,
                config=cfg,
            )
            self.assertEqual(result["http_status"], 200)
            self.assertEqual(result["body"]["status"], "acknowledged")
            self.assertTrue(result["body"]["hash_match"])


if __name__ == "__main__":
    unittest.main()
