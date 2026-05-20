"""Status telemetry mirrors progress and compression to top-level fields."""

from __future__ import annotations

import unittest

from core.backup_progress import merge_progress_optional
from core.backup_telemetry import format_bytes_human, sync_status_telemetry


class TestBackupStatusTelemetryV1(unittest.TestCase):
    def test_format_bytes_human(self) -> None:
        self.assertIn("GiB", format_bytes_human(227318956032))

    def test_sync_status_from_progress(self) -> None:
        po = merge_progress_optional(
            None,
            phase="archiving",
            bytes_current=1_000_000_000,
            bytes_total_estimate=None,
            start_monotonic=0.0,
            compression_method="gzip",
            current_operation="tar_create_stream",
            target_mount="/media/setuphelfer/br001",
            target_free_bytes=900_000_000_000,
            warning_codes=[],
            health_flags={"compression_detail": {"compression_engine": "gzip"}},
            throughput_state={"last_bytes": 0, "last_t": 0.0},
        )
        st: dict = {"progress_optional": po, "compression_detail": {"compression_engine": "gzip", "compression_reason": "pigz_not_found_fallback_gzip"}}
        sync_status_telemetry(st)
        self.assertEqual(st.get("phase"), "archiving")
        self.assertEqual(st.get("written_bytes"), 1_000_000_000)
        self.assertIn("written_human", st)
        self.assertEqual(st.get("compression_engine"), "gzip")


if __name__ == "__main__":
    unittest.main()
