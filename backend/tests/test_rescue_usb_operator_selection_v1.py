"""Tests for rescue USB operator selection (Developer Toolbox)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_usb_operator_selection as rus  # noqa: E402

try:
    from fastapi.testclient import TestClient

    from app import app as fastapi_app

    _HAS_TC = True
except Exception:
    TestClient = None  # type: ignore[misc, assignment]
    fastapi_app = None  # type: ignore[misc, assignment]
    _HAS_TC = False


def _mock_lsblk(stdout: str):
    def runner(argv, **kwargs):
        if argv[:2] == ["lsblk", "-J"]:
            return SimpleNamespace(returncode=0, stdout=stdout, stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    return runner


_LSBLK_USB_SDB = json.dumps(
    {
        "blockdevices": [
            {
                "path": "/dev/sda",
                "name": "sda",
                "type": "disk",
                "size": "931G",
                "tran": "usb",
                "rm": True,
                "model": "HGST BACKUP",
                "serial": "BACKUP001",
                "children": [
                    {
                        "path": "/dev/sda1",
                        "name": "sda1",
                        "type": "part",
                        "size": "931G",
                        "fstype": "ext4",
                        "mountpoints": ["/media/gabriel/BACKUP_DISK"],
                    }
                ],
            },
            {
                "path": "/dev/sdb",
                "name": "sdb",
                "type": "disk",
                "size": "58G",
                "tran": "usb",
                "rm": True,
                "model": "INTENSO",
                "serial": "STICK123",
                "children": [
                    {
                        "path": "/dev/sdb1",
                        "name": "sdb1",
                        "type": "part",
                        "size": "58G",
                        "fstype": "iso9660",
                        "label": "SETUPHELFER_RESCUE",
                        "mountpoints": ["/media/gabriel/SETUPHELFER_RESCUE"],
                    }
                ],
            },
            {
                "path": "/dev/nvme0n1",
                "name": "nvme0n1",
                "type": "disk",
                "size": "512G",
                "tran": "nvme",
                "rm": False,
                "model": "SYSTEM NVME",
                "serial": "NVME001",
            },
        ]
    }
)


def _all_confirmations() -> dict[str, bool]:
    return {k: True for k in rus.REQUIRED_CONFIRMATIONS}


class RescueUsbOperatorSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = _mock_lsblk(_LSBLK_USB_SDB)
        self.tmp = Path(self._testMethodName + "_ws")
        self.tmp.mkdir(exist_ok=True)
        gate_dir = self.tmp / "docs/evidence/runtime-results/rescue"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "rescue_iso_usb_gate_status_latest.json").write_text(
            json.dumps(
                {
                    "iso_path": "build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso",
                    "iso_sha256": "09b9482a4ef18e2abf091edace794fc6baa27398f44b26e131db87ca855e0879",
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        import shutil

        if self.tmp.exists():
            shutil.rmtree(self.tmp, ignore_errors=True)

    def test_blocks_without_checkboxes(self) -> None:
        out = rus.evaluate_operator_submission(
            selected_device="/dev/sdb",
            operator_confirmations={},
            confirmation_phrase=rus.CONFIRMATION_PHRASE,
            runner=self.runner,
            workspace=self.tmp,
        )
        self.assertFalse(out["write_allowed"])
        self.assertIn(rus.BLOCKER_DESTRUCTIVE_NOT_CONFIRMED, out["blockers"])

    def test_blocks_nvme_device(self) -> None:
        out = rus.evaluate_operator_submission(
            selected_device="/dev/nvme0n1",
            operator_confirmations=_all_confirmations(),
            confirmation_phrase=rus.CONFIRMATION_PHRASE,
            runner=self.runner,
            workspace=self.tmp,
        )
        self.assertFalse(out["write_allowed"])
        self.assertIn(rus.BLOCKER_SELECTION_REQUIRED, out["blockers"])

    def test_blocks_sda_backup_device(self) -> None:
        out = rus.evaluate_operator_submission(
            selected_device="/dev/sda",
            operator_confirmations=_all_confirmations(),
            confirmation_phrase=rus.CONFIRMATION_PHRASE,
            runner=self.runner,
            workspace=self.tmp,
        )
        self.assertFalse(out["write_allowed"])
        self.assertIn(rus.BLOCKER_SELECTION_REQUIRED, out["blockers"])

    def test_old_setuphelfer_warning_without_replace_confirmation(self) -> None:
        conf = _all_confirmations()
        conf["confirm_old_stick_replace"] = False
        out = rus.evaluate_operator_submission(
            selected_device="/dev/sdb",
            operator_confirmations=conf,
            confirmation_phrase=rus.CONFIRMATION_PHRASE,
            runner=self.runner,
            workspace=self.tmp,
        )
        self.assertFalse(out["write_allowed"])
        self.assertTrue(out["setuphelfer_rescue_detected"])
        self.assertIn(rus.BLOCKER_OLD_REPLACE_NOT_CONFIRMED, out["blockers"])

    def test_allows_usb_with_full_confirmation(self) -> None:
        out = rus.evaluate_operator_submission(
            selected_device="/dev/sdb",
            operator_confirmations=_all_confirmations(),
            confirmation_phrase=rus.CONFIRMATION_PHRASE,
            runner=self.runner,
            workspace=self.tmp,
        )
        self.assertTrue(out["write_allowed"])
        self.assertEqual(out["blockers"], [])

    def test_generated_dd_command_contains_selected_device(self) -> None:
        out = rus.evaluate_operator_submission(
            selected_device="/dev/sdb",
            operator_confirmations=_all_confirmations(),
            confirmation_phrase=rus.CONFIRMATION_PHRASE,
            runner=self.runner,
            workspace=self.tmp,
        )
        cmd = out.get("generated_dd_command") or ""
        self.assertIn('of="/dev/sdb"', cmd)
        self.assertIn("binary.hybrid.iso", cmd)

    def test_evidence_has_no_secrets(self) -> None:
        out = rus.evaluate_operator_submission(
            selected_device="/dev/sdb",
            operator_confirmations=_all_confirmations(),
            confirmation_phrase=rus.CONFIRMATION_PHRASE,
            runner=self.runner,
            workspace=self.tmp,
        )
        path = rus.save_operator_selection_evidence(out, workspace=self.tmp)
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("TOKEN", text.upper())
        self.assertFalse(out.get("secrets_exposed"))
        loaded = json.loads(text)
        self.assertEqual(loaded["selected_device"], "/dev/sdb")
        self.assertTrue(loaded["confirmation_phrase_matched"])

    def test_candidates_mark_old_rescue_warning_not_auto_write(self) -> None:
        payload = rus.build_usb_candidates_payload(runner=self.runner, workspace=self.tmp)
        sdb = next(d for d in payload["devices"] if d["device"] == "/dev/sdb")
        self.assertTrue(sdb["setuphelfer_rescue_detected"])
        self.assertIsNotNone(sdb["setuphelfer_rescue_warning"])
        self.assertFalse(payload["dd_execution_allowed"])

    def test_compact_summary_reflects_missing_selection(self) -> None:
        summary = rus.build_compact_usb_operator_summary(runner=self.runner, workspace=self.tmp)
        self.assertTrue(summary["usb_detected"])
        self.assertTrue(summary["old_rescue_stick_detected"])
        self.assertFalse(summary["operator_selection_present"])
        self.assertFalse(summary["destructive_write_allowed"])
        self.assertIn(rus.BLOCKER_SELECTION_REQUIRED, summary["blockers"])


@unittest.skipUnless(_HAS_TC, "FastAPI TestClient nicht verfügbar")
class RescueUsbOperatorHttpTests(unittest.TestCase):
    def test_candidates_requires_developer_capability_on_status_routes(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "SETUPHELFER_INSTALL_PROFILE": "release",
                "DCC_DEVELOPER_ENABLED": "1",
                "DCC_DEVELOPER_TOKEN": "valid-token",
            },
            clear=False,
        ):
            client = TestClient(fastapi_app, base_url="http://localhost")
            r = client.get(
                "/api/dev-dashboard/rescue-usb/candidates",
                headers={"X-Setuphelfer-Developer-Token": "valid-token"},
            )
            self.assertEqual(r.status_code, 200)
            self.assertFalse(r.json().get("dd_execution_allowed"))
            self.assertNotIn("valid-token", r.text)


if __name__ == "__main__":
    unittest.main()
