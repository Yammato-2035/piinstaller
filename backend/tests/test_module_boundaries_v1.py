"""Architecture boundary docs and check-module-boundaries script (no runtime backup)."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


class ModuleBoundariesV1Tests(unittest.TestCase):
    def test_required_architecture_docs_exist(self) -> None:
        required = [
            "docs/architecture/MONOLITH_BOUNDARY_AUDIT_2026-05-20.md",
            "docs/architecture/MODULE_BOUNDARIES_TARGET_2026-05-20.md",
            "docs/architecture/MONOLITH_DECOMPOSITION_PLAN_2026-05-20.md",
            "docs/architecture/NO_DUPLICATE_MODULE_RULES.md",
            "docs/rescue-stick/RESCUE_STICK_CORE_DEPENDENCIES_2026-05-20.md",
        ]
        for rel in required:
            self.assertTrue((_REPO / rel).is_file(), msg=rel)

    def test_monolith_audit_evidence_json_valid(self) -> None:
        path = _REPO / "docs/evidence/runtime-results/monolith_boundary_audit_before_rescue_2026-05-20.json"
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data.get("task"), "monolith_boundary_audit_before_rescue")
        self.assertTrue(data.get("monolith_audit_done"))
        self.assertTrue(data.get("br001_offline_next_allowed_after_audit"))

    def test_check_module_boundaries_script_runs(self) -> None:
        script = _REPO / "scripts/check-module-boundaries.sh"
        self.assertTrue(script.is_file())
        proc = subprocess.run(
            ["bash", str(script)],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=(proc.stdout or "") + (proc.stderr or ""),
        )

    def test_single_canonical_backup_runner(self) -> None:
        runners = [
            p
            for p in _REPO.glob("backend/**/backup_runner.py")
            if "venv" not in p.parts and ".venv" not in p.parts
        ]
        self.assertEqual(len(runners), 1)
        self.assertEqual(runners[0].resolve(), (_REPO / "backend/tools/backup_runner.py").resolve())


if __name__ == "__main__":
    unittest.main()
