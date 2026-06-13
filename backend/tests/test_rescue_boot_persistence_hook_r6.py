"""Phase R.6: boot evidence init hook and matrix entries."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


class TestRescueBootPersistenceHookR6(unittest.TestCase):
    def test_persistence_version_is_4(self) -> None:
        import core.rescue_persistence as rp

        diag = rp.build_rescue_persistence_diagnostics()
        self.assertEqual(diag["persistence_version"], 4)
        self.assertIn("initialize_boot_evidence_marker", diag["public_functions"])
        self.assertIn("/lib/live/mount/medium", diag["live_medium_candidates"])

    def test_initialize_boot_evidence_marker_writes_markers(self) -> None:
        import core.rescue_persistence as rp

        with tempfile.TemporaryDirectory() as tmp:
            evidence_root = Path(tmp)
            boot_dir = evidence_root / "boot"
            boot_dir.mkdir(parents=True)
            tree = {
                "tree_ready": True,
                "evidence_root": str(evidence_root),
                "fallback": False,
                "persistence_mode": "stick_rw",
                "warning": None,
            }
            with (
                mock.patch.object(rp, "detect_rescue_stick_mount", return_value={"fallback": False}),
                mock.patch.object(rp, "ensure_rescue_evidence_tree", return_value=tree),
                mock.patch.object(rp, "collect_boot_context_safe", return_value={"kernel": "6.1.0"}),
                mock.patch.object(
                    rp,
                    "write_rescue_json_evidence",
                    side_effect=lambda area, name, payload, **_: {
                        "path": str(evidence_root / area / name),
                        "status": "ok",
                    },
                ),
                mock.patch.object(
                    rp,
                    "write_rescue_text_evidence",
                    side_effect=lambda area, name, _text, **_: {
                        "path": str(evidence_root / area / name),
                        "status": "ok",
                    },
                ),
            ):
                result = rp.initialize_boot_evidence_marker()

        self.assertTrue(result["boot_marker_written"])
        self.assertEqual(result["status"], "stick")
        self.assertTrue(result["evidence_target_is_stick"])
        self.assertFalse(result["evidence_target_is_ram_fallback"])

    def test_initialize_boot_evidence_marker_ram_fallback(self) -> None:
        import core.rescue_persistence as rp

        tree = {
            "tree_ready": True,
            "evidence_root": "/tmp/setuphelfer-evidence",
            "fallback": True,
            "persistence_mode": "ram_fallback",
            "warning": "Stick read-only",
        }
        with (
            mock.patch.object(rp, "detect_rescue_stick_mount", return_value={"fallback": True, "mount_point": "/run/live/medium"}),
            mock.patch.object(rp, "_attempt_remount_rw", return_value={"attempted": True, "ok": False}),
            mock.patch.object(rp, "ensure_rescue_evidence_tree", return_value=tree),
            mock.patch.object(rp, "collect_boot_context_safe", return_value={}),
            mock.patch.object(rp, "write_rescue_json_evidence", return_value={"path": "/tmp/x.json"}),
            mock.patch.object(rp, "write_rescue_text_evidence", return_value={"path": "/tmp/x.md"}),
        ):
            result = rp.initialize_boot_evidence_marker()

        self.assertEqual(result["status"], "ram_fallback")
        self.assertTrue(result["evidence_target_is_ram_fallback"])

    def test_r6_matrix_entries_include_boot_marker(self) -> None:
        import core.rescue_test_matrix as rtm

        with tempfile.TemporaryDirectory() as tmp:
            evidence_root = Path(tmp)
            boot_dir = evidence_root / "boot"
            boot_dir.mkdir(parents=True)
            (boot_dir / "boot_marker.json").write_text("{}", encoding="utf-8")
            (boot_dir / "boot_marker.md").write_text("# marker", encoding="utf-8")
            tree = {
                "tree_ready": True,
                "evidence_root": str(evidence_root),
                "fallback": False,
                "persistence_mode": "stick_rw",
                "created_dirs": ["boot"],
            }
            with mock.patch.object(rtm, "ensure_rescue_evidence_tree", return_value=tree):
                entries = rtm.build_r6_boot_persistence_matrix_entries()

        ids = {e["id"] for e in entries}
        self.assertIn("R6-BOOT-MARKER-001", ids)
        self.assertIn("R6-EVIDENCE-ROOT-001", ids)
        self.assertIn("R6-TARGET-STICK-001", ids)
        self.assertIn("R6-TARGET-RAM-001", ids)
        self.assertIn("R6-START-ASSIST-001", ids)
        marker = next(e for e in entries if e["id"] == "R6-BOOT-MARKER-001")
        self.assertEqual(marker["status"], "green")
        self.assertEqual(marker["title"], "boot_marker_written")

    def test_evidence_py_boot_init_subcommand(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        ev_script = repo_root / "scripts/rescue-live/image/setuphelfer-rescue-evidence.py"
        text = ev_script.read_text(encoding="utf-8")
        self.assertIn('sub.add_parser("boot-init"', text)
        self.assertIn("initialize_boot_evidence_marker", text)


if __name__ == "__main__":
    unittest.main()
