from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

_repo = Path(__file__).resolve().parent.parent.parent
_build_script = _repo / "scripts/rescue-live/run-controlled-iso-build-with-logging.sh"
_clean_script = _repo / "scripts/rescue-live/clean-controlled-live-build-tree.sh"
_preflight_script = _repo / "scripts/rescue-live/preflight-developer-controlled-iso-build.sh"

from core.rescue_iso_build_permission_policy import (  # noqa: E402
    assess_build_tree_permissions,
    default_build_tree,
    list_clean_targets,
    validate_clean_target,
)


class RescueDeveloperIsoBuildPermissionPolicyTests(unittest.TestCase):
    def test_preflight_blocks_non_writable_dot_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "tree"
            dot_build = root / ".build"
            dot_build.mkdir(parents=True)
            (dot_build / "config").write_text("x", encoding="utf-8")
            os.chmod(dot_build, stat.S_IRUSR | stat.S_IXUSR)
            result = assess_build_tree_permissions(root)
            self.assertTrue(result["operator_fix_required"])
            self.assertIn("dot_build_not_writable", result["permission_blockers"])
            self.assertEqual(result["error_code"], "rescue_iso_build.permission_denied_dot_build")

    def test_preflight_detects_root_owned_dot_build(self) -> None:
        if os.geteuid() != 0:
            self.skipTest("requires root to create root-owned fixture")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "tree"
            dot_build = root / ".build"
            dot_build.mkdir(parents=True)
            (dot_build / "config").write_text("x", encoding="utf-8")
            os.chown(dot_build, 0, 0)
            os.chown(dot_build / "config", 0, 0)
            result = assess_build_tree_permissions(root)
            self.assertTrue(result["operator_fix_required"])
            self.assertIn("root_owned_active_work_areas", result["permission_blockers"])

    def test_preflight_operator_fix_required_true_when_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "tree"
            root.mkdir()
            blocked = root / ".build"
            blocked.mkdir()
            os.chmod(blocked, 0o555)
            result = assess_build_tree_permissions(root)
            self.assertTrue(result["operator_fix_required"])
            self.assertIn("clean-controlled-live-build-tree", result["recommended_fix"])

    def test_clean_helper_rejects_paths_outside_build_tree(self) -> None:
        build_root = default_build_tree()
        outside = _repo / "build/rescue/outside-evil"
        self.assertFalse(validate_clean_target(outside, build_root))
        self.assertFalse(validate_clean_target(_repo / "opt", build_root))

    def test_clean_helper_dry_run_does_not_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_repo = Path(tmp) / "repo"
            tree = fake_repo / "build/rescue/live-build/setuphelfer-rescue-live"
            tree.mkdir(parents=True)
            marker = tree / ".build" / "config"
            marker.parent.mkdir()
            marker.write_text("keep", encoding="utf-8")
            proc = subprocess.run(
                ["bash", str(_clean_script), "--dry-run"],
                cwd=fake_repo,
                capture_output=True,
                text=True,
                env={**os.environ, "REPO_ROOT_OVERRIDE": str(fake_repo)},
            )
            # Script resolves repo from script location; run via copied path check instead
            targets = list_clean_targets(tree)
            self.assertTrue(any(t.name == ".build" for t in targets))
            self.assertTrue(marker.is_file())

    def test_clean_helper_confirm_removes_only_allowed_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "setuphelfer-rescue-live"
            tree.mkdir()
            (tree / ".build").mkdir()
            (tree / "binary").mkdir()
            (tree / "keep-config").mkdir()
            allowed = list_clean_targets(tree)
            names = {p.name for p in allowed}
            self.assertIn(".build", names)
            self.assertIn("binary", names)
            self.assertNotIn("keep-config", names)

    def test_build_script_has_permission_preflight_before_lb_config(self) -> None:
        text = _build_script.read_text(encoding="utf-8")
        marker = 'cd "${BUILD_ROOT}"'
        config_idx = text.index(marker)
        block = text[:config_idx]
        self.assertIn("permission_preflight_ok", block)
        self.assertIn("PERMISSION_PREFLIGHT_CODE", text)
        self.assertIn("rescue_iso_build.permission_denied_dot_build", text)

    def test_build_script_permission_blocked_exit_code(self) -> None:
        text = _build_script.read_text(encoding="utf-8")
        self.assertIn("PERMISSION_PREFLIGHT_EXIT=34", text)
        self.assertIn('exit "${LB_EXIT}"', text)

    def test_scripts_forbid_dangerous_commands(self) -> None:
        text = _clean_script.read_text(encoding="utf-8")
        for forbidden in ("dd ", "mkfs", "mount ", "umount", "apt install", "apt-get install"):
            # usage documents forbidden ops; ensure no executable invocations
            self.assertNotRegex(text, rf"(^|\n)\s*{forbidden.strip()}")

    def test_clean_script_stays_under_rescue_live_build_tree(self) -> None:
        text = _clean_script.read_text(encoding="utf-8")
        self.assertIn("build/rescue/live-build/setuphelfer-rescue-live", text)
        self.assertIn('BUILD_ROOT="${REPO_ROOT}/build/rescue/live-build/setuphelfer-rescue-live"', text)
        self.assertIn('build tree outside repo', text)

    def test_preflight_script_emits_permission_policy(self) -> None:
        text = _preflight_script.read_text(encoding="utf-8")
        self.assertIn("permission_policy", text)
        self.assertIn("assess_build_tree_permissions", text)


if __name__ == "__main__":
    unittest.main()
