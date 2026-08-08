"""PI-RS-ASUS-HIGHINFO-PHYSICAL-009: HIGHINFO Xorg evidence mirror tests."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from rescue.highinfo_xorg_evidence import (
    build_highinfo_xorg_evidence_record,
    classify_evidence_origin,
    mirror_path_to_roots,
    write_and_mirror_highinfo_xorg_evidence,
)


class HighinfoXorgEvidenceMirrorTests(unittest.TestCase):
    def test_startx_success_with_log(self) -> None:
        rec = build_highinfo_xorg_evidence_record(
            boot_id="b1",
            run_id="r1",
            startx_invoked=True,
            startx_exit_code=0,
            xorg_log_found=True,
            xorg_log_path="/run/setuphelfer/Xorg.forensic.log",
            xorg_probe_status="ok",
        )
        self.assertTrue(rec["startx_invoked"])
        self.assertEqual(rec["startx_exit_code"], 0)
        self.assertTrue(rec["xorg_log_found"])
        self.assertNotIn("reason", rec)

    def test_startx_failed_with_log(self) -> None:
        rec = build_highinfo_xorg_evidence_record(
            boot_id="b1",
            run_id="r1",
            startx_invoked=True,
            startx_exit_code=1,
            xorg_log_found=True,
            xorg_log_path="/tmp/Xorg.forensic.log",
            xorg_probe_status="failed",
            reason="xorg_probe_failed",
        )
        self.assertTrue(rec["startx_invoked"])
        self.assertEqual(rec["startx_exit_code"], 1)
        self.assertTrue(rec["xorg_log_found"])

    def test_startx_failed_without_log(self) -> None:
        rec = build_highinfo_xorg_evidence_record(
            boot_id="b1",
            run_id="r1",
            startx_invoked=True,
            startx_exit_code=1,
            xorg_log_found=False,
            xorg_probe_status="failed",
        )
        self.assertTrue(rec["startx_invoked"])
        self.assertFalse(rec["xorg_log_found"])

    def test_startx_never_invoked(self) -> None:
        rec = build_highinfo_xorg_evidence_record(
            boot_id="b1",
            run_id="r1",
            startx_invoked=False,
        )
        self.assertFalse(rec["startx_invoked"])
        self.assertFalse(rec["xorg_log_found"])
        self.assertEqual(rec["reason"], "startx_not_invoked")

    def test_mirror_when_setup_logs_available(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logs = root / "SETUP_LOGS" / "setuphelfer" / "evidence"
            logs.mkdir(parents=True)
            local = root / "run" / "highinfo" / "xorg_probe_evidence.json"
            rec = build_highinfo_xorg_evidence_record(
                boot_id="boot-current",
                run_id="run-1",
                startx_invoked=True,
                startx_exit_code=0,
                xorg_log_found=True,
                xorg_log_path="/run/Xorg.forensic.log",
            )
            out = write_and_mirror_highinfo_xorg_evidence(
                rec,
                local_path=local,
                setup_logs_roots=[logs],
            )
            self.assertTrue(out["record"]["evidence_mirrored"])
            self.assertIsNotNone(out["record"]["mirrored_at"])
            mirrored = logs / "boot/highinfo/xorg_probe_evidence.json"
            self.assertTrue(mirrored.is_file())
            data = json.loads(mirrored.read_text(encoding="utf-8"))
            self.assertEqual(data["boot_id"], "boot-current")

    def test_mirror_when_setup_logs_unavailable(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            local = root / "run" / "xorg_probe_evidence.json"
            rec = build_highinfo_xorg_evidence_record(
                boot_id="b1",
                run_id="r1",
                startx_invoked=False,
            )
            out = write_and_mirror_highinfo_xorg_evidence(
                rec,
                local_path=local,
                setup_logs_roots=[],
            )
            self.assertFalse(out["record"]["evidence_mirrored"])
            self.assertIn("setup_logs_evidence_root_unavailable", out["record"]["warnings"])
            self.assertTrue(local.is_file())

    def test_stale_previous_boot_not_current(self) -> None:
        self.assertEqual(
            classify_evidence_origin(
                artifact_boot_id="old-boot",
                current_boot_id="new-boot",
            ),
            "stale_previous_boot",
        )

    def test_current_boot_match(self) -> None:
        self.assertEqual(
            classify_evidence_origin(
                artifact_boot_id="same",
                current_boot_id="same",
            ),
            "current_boot",
        )

    def test_mirror_does_not_overwrite_other_boot_tree(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logs = root / "evidence"
            other = logs / "boot" / "other-boot" / "keep.json"
            other.parent.mkdir(parents=True)
            other.write_text('{"boot_id":"other"}\n', encoding="utf-8")
            src = root / "xorg_probe_evidence.json"
            src.write_text('{"boot_id":"current"}\n', encoding="utf-8")
            mirror_path_to_roots(src, "boot/highinfo/xorg_probe_evidence.json", [logs])
            self.assertTrue(other.is_file())
            self.assertEqual(json.loads(other.read_text())["boot_id"], "other")
            self.assertTrue((logs / "boot/highinfo/xorg_probe_evidence.json").is_file())

    def test_no_secret_fields(self) -> None:
        rec = build_highinfo_xorg_evidence_record(
            boot_id="b1",
            run_id="r1",
            startx_invoked=True,
            startx_exit_code=0,
            xorg_log_found=True,
            xorg_log_path="/run/Xorg.forensic.log",
        )
        blob = json.dumps(rec)
        for forbidden in ("password", "token", "api_key", "Authorization", "psk"):
            self.assertNotIn(forbidden, blob.lower())

    def test_gui_success_not_required(self) -> None:
        rec = build_highinfo_xorg_evidence_record(
            boot_id="b1",
            run_id="r1",
            startx_invoked=True,
            startx_exit_code=1,
            xorg_log_found=True,
            xorg_probe_status="failed",
            reason="xorg_probe_failed",
        )
        self.assertTrue(rec["startx_invoked"])
        self.assertNotEqual(rec.get("xorg_probe_status"), "gui_required")


if __name__ == "__main__":
    unittest.main()
