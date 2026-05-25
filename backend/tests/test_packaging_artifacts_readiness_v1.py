from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import packaging_readiness_state as prs  # noqa: E402


class PackagingArtifactsReadinessTests(unittest.TestCase):
    def test_missing_artifacts_is_yellow_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime_root = Path(td)
            payload = prs.build_packaging_readiness_state(runtime_root=runtime_root)
        self.assertEqual(payload["status"], "yellow")
        self.assertFalse(payload["deb_ready"])
        self.assertFalse(payload["install_test_passed"])

    def test_deb_artifact_sets_green_readiness_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime_root = Path(td)
            deb_dir = runtime_root / "frontend/src-tauri/target/release/bundle/deb"
            deb_dir.mkdir(parents=True, exist_ok=True)
            (deb_dir / "SetupHelfer_1.7.1_amd64.deb").write_bytes(b"deb")
            payload = prs.build_packaging_readiness_state(runtime_root=runtime_root)
        self.assertEqual(payload["status"], "green")
        self.assertTrue(payload["deb_ready"])
        self.assertFalse(payload["install_test_passed"])
        self.assertTrue(payload["install_test_pending"])

    def test_optional_rpm_and_appimage_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime_root = Path(td)
            rpm_dir = runtime_root / "frontend/src-tauri/target/release/bundle/rpm"
            appimage_dir = runtime_root / "frontend/src-tauri/target/release/bundle/appimage"
            rpm_dir.mkdir(parents=True, exist_ok=True)
            appimage_dir.mkdir(parents=True, exist_ok=True)
            (rpm_dir / "SetupHelfer-1.7.1.rpm").write_bytes(b"rpm")
            (appimage_dir / "SetupHelfer.AppImage").write_bytes(b"appimage")
            payload = prs.build_packaging_readiness_state(runtime_root=runtime_root)
        self.assertTrue(payload["rpm_ready"])
        self.assertTrue(payload["appimage_ready"])
        self.assertFalse(payload["deb_ready"])
        self.assertEqual(payload["status"], "yellow")

    def test_forbidden_actions_stay_false(self) -> None:
        payload = prs.build_packaging_readiness_state(runtime_root=Path("/tmp/packaging-readiness-missing"))
        forbidden = payload["forbidden_actions"]
        self.assertFalse(forbidden["dpkg_install_allowed"])
        self.assertFalse(forbidden["rpm_install_allowed"])
        self.assertFalse(forbidden["appimage_start_allowed"])
        self.assertFalse(forbidden["root_actions_allowed"])

    def test_source_contains_no_install_commands(self) -> None:
        src = (_backend / "core/packaging_readiness_state.py").read_text(encoding="utf-8")
        self.assertNotIn("dpkg -i", src)
        self.assertNotIn("rpm -i", src)
        self.assertNotIn("subprocess.run", src)
        self.assertNotIn("os.system", src)
        self.assertNotIn("apt install", src)
        self.assertNotIn("apt upgrade", src)

    def test_evidence_path_is_documented(self) -> None:
        payload = prs.build_packaging_readiness_state(runtime_root=Path("/tmp/packaging-readiness-missing"))
        self.assertTrue(str(payload["evidence_path"]).endswith("PROJECT_OVERVIEW_DASHBOARD_INTEGRATION_RESULT.md"))


if __name__ == "__main__":
    unittest.main()
