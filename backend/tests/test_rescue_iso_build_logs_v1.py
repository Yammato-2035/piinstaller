"""Rescue ISO build log filtering for Development Dashboard."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_iso_build_logs import (  # noqa: E402
    extract_log_events,
    filter_log_lines,
    read_rescue_iso_build_log_download,
    read_rescue_iso_build_logs,
)


class RescueIsoBuildLogsTests(unittest.TestCase):
    def _write_sample_log(self, repo: Path) -> None:
        log_dir = repo / "build/rescue/logs/controlled-iso-build"
        log_dir.mkdir(parents=True)
        lines = [
            "START 2026-05-30T07:41:10+02:00",
            "POLICY_GUARD_STATUS=ready",
            "CHROOT_STALE: config/hooks/includes neuer als binary/live/filesystem.squashfs",
            "Reading package lists...",
            "Building dependency tree...",
            "Reading state information...",
            "P: Begin building root filesystem image...",
            "W: skipping binary_rootfs, already done",
            "P: Begin executing hooks...",
            "=== Post-build squashfs validation ===",
            "LIVE_LOGIN_USER_GAP: etc/passwd missing user account",
            "LB_EXIT=18",
            "OK: summary written to docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json",
        ]
        (log_dir / "latest.log").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_important_filter_reduces_noise(self) -> None:
        repo = Path(tempfile.mkdtemp())
        self._write_sample_log(repo)
        payload = read_rescue_iso_build_logs(repo_root=repo, log_filter="important", tail=500)
        self.assertEqual(payload["status"], "success")
        self.assertLess(payload["returned_lines"], payload["total_lines"])
        joined = "\n".join(payload["lines"])
        self.assertIn("LB_EXIT=18", joined)
        self.assertIn("CHROOT_STALE", joined)
        self.assertNotIn("Reading package lists", joined)

    def test_errors_filter_finds_gap_and_exit(self) -> None:
        repo = Path(tempfile.mkdtemp())
        self._write_sample_log(repo)
        payload = read_rescue_iso_build_logs(repo_root=repo, log_filter="errors", tail=500)
        joined = "\n".join(payload["lines"])
        self.assertIn("LIVE_LOGIN_USER_GAP", joined)
        self.assertIn("LB_EXIT=18", joined)

    def test_summary_events_include_skipped_stage(self) -> None:
        repo = Path(tempfile.mkdtemp())
        self._write_sample_log(repo)
        payload = read_rescue_iso_build_logs(repo_root=repo, log_filter="summary", tail=500)
        types = [event["type"] for event in payload["events"]]
        self.assertIn("stage_skipped", types)
        self.assertIn("lb_exit", types)
        self.assertEqual(payload["last_lb_exit"], "18")

    def test_download_returns_full_content(self) -> None:
        repo = Path(tempfile.mkdtemp())
        self._write_sample_log(repo)
        payload = read_rescue_iso_build_log_download(repo_root=repo)
        self.assertIn("LB_EXIT=18", payload["content"])
        self.assertEqual(payload["total_lines"], 13)

    def test_filter_log_lines_unit(self) -> None:
        lines = [
            "noise line",
            "LB_EXIT=0",
            "LIVE_LOGIN_USER_GAP: missing user",
        ]
        important = filter_log_lines(lines, "important")
        self.assertIn("LB_EXIT=0", important)
        self.assertNotIn("noise line", important)


if __name__ == "__main__":
    unittest.main()
