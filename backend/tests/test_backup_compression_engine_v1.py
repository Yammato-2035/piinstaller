"""Compression engine selection: pigz auto, gzip fallback, explicit pigz block."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from core import backup_archive_options as bao
from core.backup_profiles import PROFILE_FULL_ROOT_STABLE


class TestBackupCompressionEngineV1(unittest.TestCase):
    def test_pigz_auto_when_available(self) -> None:
        with patch.object(bao, "pigz_available", return_value=True):
            meta = bao.resolve_compression_choice(profile=bao.PROFILE_RECOMMENDED)
        self.assertEqual(meta["compression_engine"], "pigz")
        self.assertEqual(meta["compression_reason"], "pigz_found")
        self.assertIsNotNone(meta["compression_threads"])

    def test_gzip_fallback_when_no_pigz(self) -> None:
        with patch.object(bao, "pigz_available", return_value=False):
            meta = bao.resolve_compression_choice(profile=bao.PROFILE_RECOMMENDED)
        self.assertEqual(meta["compression_engine"], "gzip")
        self.assertEqual(meta["compression_reason"], "pigz_not_found_fallback_gzip")
        self.assertIn("compression_fallback_gzip", meta.get("compression_warning_codes") or [])

    def test_explicit_gzip(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_BACKUP_COMPRESSION_ENGINE": "gzip"}):
            with patch.object(bao, "pigz_available", return_value=True):
                meta = bao.resolve_compression_choice(profile=bao.PROFILE_RECOMMENDED)
        self.assertEqual(meta["compression_engine"], "gzip")
        self.assertTrue(meta["uses_builtin_tar_czf"])

    def test_explicit_pigz_missing_blocks(self) -> None:
        with patch.object(bao, "_compression_engine_env", return_value="pigz"):
            with patch.object(bao, "pigz_available", return_value=False):
                meta = bao.resolve_compression_choice(profile=bao.PROFILE_RECOMMENDED)
        self.assertTrue(meta.get("compression_preflight_blocked"))
        cmd, _ = bao.build_full_root_tar_command("/tmp/x.partial", "/tmp/bd", profile=bao.PROFILE_RECOMMENDED)
        self.assertEqual(cmd, "")

    def test_full_root_stable_excludes_browser_cache(self) -> None:
        cmd, meta = bao.build_full_root_tar_command(
            "/tmp/x.partial",
            "/tmp/backupdir",
            profile=PROFILE_FULL_ROOT_STABLE,
        )
        self.assertEqual(meta["profile_normalized"], PROFILE_FULL_ROOT_STABLE)
        self.assertIn("google-chrome", cmd)


if __name__ == "__main__":
    unittest.main()
