"""Tests for rescue live-medium check (ISO hybrid + FAT32 ESP)."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IMAGE = REPO / "scripts" / "rescue-live" / "image"


def _load_medium_check():
    path = IMAGE / "setuphelfer-rescue-live-medium-check.py"
    spec = importlib.util.spec_from_file_location("live_medium_check", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["live_medium_check"] = mod
    spec.loader.exec_module(mod)
    return mod


class RescueLiveMediumCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_medium_check()

    def _fat32_layout(
        self,
        tmp: Path,
        *,
        squashfs_sha: str = "abc123",
        wrong_label: bool = False,
        omit_squashfs: bool = False,
    ) -> Path:
        root = tmp / "SETUPHELFER"
        for rel in self.mod.REQUIRED_MEDIUM_PATHS:
            if omit_squashfs and rel == "live/filesystem.squashfs":
                continue
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"x" * 64)
        evidence = {
            "writer_mode": "fat32_esp",
            "files": [
                {
                    "staging_path": "live/filesystem.squashfs",
                    "sha256": squashfs_sha,
                }
            ],
        }
        (root / "setuphelfer/rescue/evidence.json").write_text(
            json.dumps(evidence), encoding="utf-8"
        )
        if not wrong_label:
            return root
        return tmp / "INTENSO"

    def test_iso_hybrid_still_stable_with_classic_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "medium"
            sq = root / "live/filesystem.squashfs"
            sq.parent.mkdir(parents=True)
            sq.write_bytes(b"squashfs")
            result = self.mod.evaluate_live_medium_check(
                proc_cmdline="boot=live setuphelfer_rescue=1",
                medium_roots=[root],
                path_exists=lambda p: p.is_file(),
                squashfs_reader=lambda _p: True,
                spot_reader=lambda _sq, _inner: True,
            )
            self.assertTrue(result["live_media_runtime_stable"])
            self.assertIn(result["medium_mode"], ("iso_hybrid", "unknown"))

    def test_fat32_esp_stable_with_full_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fat32_layout(Path(tmp), squashfs_sha="deadbeef")
            result = self.mod.evaluate_live_medium_check(
                proc_cmdline="boot=live setuphelfer_rescue=1",
                medium_roots=[root],
                path_exists=lambda p: p.is_file(),
                squashfs_reader=lambda _p: True,
                spot_reader=lambda _sq, _inner: True,
                sha256_fn=lambda _p: "deadbeef",
            )
            self.assertEqual(result["medium_mode"], "fat32_esp")
            self.assertTrue(result["live_media_runtime_stable"])
            self.assertTrue(result["squashfs_hash_ok"])

    def test_fat32_esp_hash_ok_overrides_spot_check_false_positive(self) -> None:
        # Regression: `unsquashfs -cat` spot checks fail on some unsquashfs builds
        # and on symlinked targets (nmcli/curl), but a matching full-image sha256
        # proves the medium is intact. The spot-check must then be advisory only
        # and NOT mark the medium unstable.
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fat32_layout(Path(tmp), squashfs_sha="deadbeef")
            result = self.mod.evaluate_live_medium_check(
                proc_cmdline="boot=live setuphelfer_rescue=1",
                medium_roots=[root],
                path_exists=lambda p: p.is_file(),
                squashfs_reader=lambda _p: True,
                spot_reader=lambda _sq, _inner: False,
                sha256_fn=lambda _p: "deadbeef",
            )
            self.assertTrue(result["squashfs_hash_ok"])
            self.assertFalse(result["spot_checks_ok"])
            self.assertTrue(result["spot_check_failures"])
            self.assertTrue(result["live_media_runtime_stable"])
            self.assertIsNone(result["error_code"])

    def test_fat32_esp_without_squashfs_unstable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fat32_layout(Path(tmp), omit_squashfs=True)
            result = self.mod.evaluate_live_medium_check(
                proc_cmdline="boot=live setuphelfer_rescue=1",
                medium_roots=[root],
                path_exists=lambda p: p.is_file(),
            )
            self.assertFalse(result["live_media_runtime_stable"])
            self.assertIn("live/filesystem.squashfs", result["required_files_missing"])

    def test_fat32_esp_wrong_hash_unstable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fat32_layout(Path(tmp), squashfs_sha="expected")
            result = self.mod.evaluate_live_medium_check(
                proc_cmdline="boot=live setuphelfer_rescue=1",
                medium_roots=[root],
                path_exists=lambda p: p.is_file(),
                squashfs_reader=lambda _p: True,
                spot_reader=lambda _sq, _inner: True,
                sha256_fn=lambda _p: "different",
            )
            self.assertFalse(result["live_media_runtime_stable"])
            self.assertEqual(result["error_code"], "FAT32_ESP_SQUASHFS_HASH_MISMATCH")

    def test_fat32_esp_missing_required_files_review_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "SETUPHELFER"
            (root / "live").mkdir(parents=True)
            (root / "live/filesystem.squashfs").write_bytes(b"x")
            (root / "setuphelfer/rescue").mkdir(parents=True)
            (root / "setuphelfer/rescue/evidence.json").write_text(
                json.dumps({"writer_mode": "fat32_esp", "files": []}),
                encoding="utf-8",
            )
            result = self.mod.evaluate_live_medium_check(
                proc_cmdline="boot=live setuphelfer_rescue=1",
                medium_roots=[root],
                path_exists=lambda p: p.is_file(),
                squashfs_reader=lambda _p: True,
                spot_reader=lambda _sq, _inner: True,
            )
            self.assertFalse(result["live_media_runtime_stable"])
            self.assertEqual(result["evidence_status"], "review_required")

    def test_resolve_squashfs_from_media_setuphelfer_mount(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "media" / "user" / "SETUPHELFER"
            sq = root / "live/filesystem.squashfs"
            sq.parent.mkdir(parents=True)
            sq.write_bytes(b"x")
            found, medium = self.mod.resolve_squashfs_and_medium_root(medium_roots=[root])
            self.assertEqual(found, sq)
            self.assertEqual(medium, root)

    def test_unstable_blocks_repair_via_plan_builder(self) -> None:
        plan_mod_path = IMAGE / "setuphelfer-rescue-plan-builder.py"
        spec = importlib.util.spec_from_file_location("plan_builder", plan_mod_path)
        assert spec and spec.loader
        plan = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plan)
        out = plan.build_plans(
            {"devices": []},
            {"media_check": {"live_media_runtime_stable": False}, "selected_action": "repair"},
        )
        self.assertFalse(out["execution_allowed"])
        self.assertEqual(out["blocked_reason"], "live_media_unstable")

    def test_boot_warning_sets_yellow_not_green_rs001(self) -> None:
        """HW boot with unstable medium must not imply RS-001 green."""
        result = self.mod.evaluate_live_medium_check(
            proc_cmdline="boot=live setuphelfer_rescue=1 setuphelfer_start_assistant=1",
            medium_roots=[],
            path_exists=lambda _p: False,
        )
        self.assertFalse(result["live_media_runtime_stable"])
        self.assertIn("no_repair_or_install", result["operator_hints"])


if __name__ == "__main__":
    unittest.main()
