"""Deploy runner registry Phase C.1 — static classification only."""

from __future__ import annotations

import ast
import sys
import tempfile
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_registry import (
    RunnerCategory,
    RunnerExecutionPolicy,
    RunnerRiskLevel,
    build_runner_registry_from_files,
    build_runner_registry_summary,
    classify_runner_file,
    find_runner_by_id,
    list_runners_by_category,
    list_runners_by_risk,
    registry_policy_warnings,
    runner_id_from_path,
)


class DeployRunnerRegistryV1Tests(unittest.TestCase):
    def test_import_without_runner_execution(self) -> None:
        src = (_BACKEND / "deploy" / "runner_registry.py").read_text(encoding="utf-8")
        self.assertNotIn("importlib.import_module", src)
        tree = ast.parse(src)
        imports_runner_modules = any(
            isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("deploy.runner_")
            for n in ast.walk(tree)
        )
        self.assertFalse(imports_runner_modules)

    def test_runner_id_stable_from_filename(self) -> None:
        self.assertEqual(
            runner_id_from_path("backend/deploy/runner_rescue_iso_build_execution.py"),
            "runner_rescue_iso_build_execution",
        )

    def test_usb_stick_classified_rescue_usb(self) -> None:
        p = _BACKEND / "deploy" / "runner_rescue_stick_readonly_build_emulation.py"
        if not p.is_file():
            self.skipTest("runner file missing")
        entry = classify_runner_file(p, repo_root=_BACKEND.parent)
        self.assertEqual(entry.category, RunnerCategory.RESCUE_USB)

    def test_iso_build_runner_category(self) -> None:
        p = _BACKEND / "deploy" / "runner_rescue_iso_build_execution.py"
        entry = classify_runner_file(p, repo_root=_BACKEND.parent)
        self.assertEqual(entry.category, RunnerCategory.RESCUE_BUILD)

    def test_evidence_runner_not_device_write(self) -> None:
        p = _BACKEND / "deploy" / "runner_manual_runtime_evidence_timeline.py"
        entry = classify_runner_file(p, repo_root=_BACKEND.parent)
        self.assertEqual(entry.category, RunnerCategory.EVIDENCE)
        self.assertFalse(entry.uses_device_write)

    def test_sudo_detected(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write("def run():\n    sudo = True\n    return {'sudo': sudo}\n")
            path = Path(tf.name)
        try:
            entry = classify_runner_file(path)
            self.assertTrue(entry.uses_sudo)
        finally:
            path.unlink(missing_ok=True)

    def test_mkfs_dd_detected(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write('subprocess.run(["dd", "if=/dev/zero", "of=/dev/sdb"])\n')
            path = Path(tf.name)
        try:
            entry = classify_runner_file(path)
            self.assertTrue(entry.uses_device_write)
            self.assertEqual(entry.risk_level, RunnerRiskLevel.DESTRUCTIVE)
        finally:
            path.unlink(missing_ok=True)

    def test_unknown_category_conservative_risk(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write("def mystery_runner():\n    return 1\n")
            path = Path(tf.name)
        try:
            entry = classify_runner_file(path)
            self.assertEqual(entry.category, RunnerCategory.UNKNOWN)
            self.assertIn(entry.risk_level, (RunnerRiskLevel.LOCAL_RUNTIME_CHANGE, RunnerRiskLevel.READ_ONLY))
        finally:
            path.unlink(missing_ok=True)

    def test_build_registry_from_deploy_dir(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        self.assertGreaterEqual(len(entries), 100)
        summary = build_runner_registry_summary(entries)
        self.assertEqual(summary.total, len(entries))
        self.assertGreater(summary.by_category.get("rescue", 0), 0)

    def test_find_and_list_helpers(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        first = entries[0]
        hit = find_runner_by_id(first.runner_id, entries)
        self.assertIsNotNone(hit)
        by_cat = list_runners_by_category(first.category, entries)
        self.assertTrue(any(e.runner_id == first.runner_id for e in by_cat))
        by_risk = list_runners_by_risk(first.risk_level, entries)
        self.assertTrue(any(e.runner_id == first.runner_id for e in by_risk))

    def test_destructive_policy_never_auto(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        destructive = [e for e in entries if e.risk_level == RunnerRiskLevel.DESTRUCTIVE]
        for e in destructive:
            self.assertEqual(e.execution_policy, RunnerExecutionPolicy.NEVER_AUTO)

    def test_registry_policy_warnings_no_false_destructive(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        bad = [w for w in registry_policy_warnings(entries) if w.startswith("runner_destructive_without_never_auto")]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
