import json
import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.diagnostics.models import EvidenceRecord, StorageDevice, SystemProfile


class TestDiagnosticsEvidenceModelV1(unittest.TestCase):
    def test_storage_device_invalid_size(self):
        with self.assertRaises(ValidationError):
            StorageDevice(
                name="/dev/sda1",
                type="usb",
                size_gb=-1,
            )

    def test_system_profile_valid_from_seed(self):
        root = Path(__file__).resolve().parents[2]
        data = json.loads(
            (root / "data/diagnostics/profiles/profile-rpi5-usb-nvme.json").read_text(
                encoding="utf-8"
            )
        )
        profile = SystemProfile(**data)
        self.assertEqual(profile.platform_class, "raspberry_pi")
        self.assertGreaterEqual(len(profile.storage_devices), 1)

    def test_evidence_record_minimal(self):
        rec = EvidenceRecord(
            id="EVID-T-1",
            timestamp="2026-01-01T00:00:00Z",
            source_type="unit_test",
            domain="backup_restore",
            platform="vm",
            scenario="s",
            test_goal="g",
            outcome="failed",
            severity="high",
            confidence="medium",
        )
        self.assertEqual(rec.outcome, "failed")


if __name__ == "__main__":
    unittest.main()
