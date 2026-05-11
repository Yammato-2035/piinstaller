from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_setuphelfer_runtime_identifier_migration import build_runtime_identifier_migration_plan

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_PLAN = _HANDOFF / "setuphelfer_runtime_identifier_migration_plan.json"
_ALIASES = _HANDOFF / "compatibility_aliases.json"
_WORKSPACE = _HANDOFF / "setuphelfer_workspace_migration_plan.json"


class DeployRunnerSetuphelferRuntimeIdentifierMigrationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for path in (_PLAN, _ALIASES, _WORKSPACE):
            path.unlink(missing_ok=True)
            tmp = path.with_name(path.name + ".tmp")
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def test_alias_definition_korrekt(self) -> None:
        res = build_runtime_identifier_migration_plan(explicit_overwrite=True)
        self.assertEqual(res.get("migration_status"), "ok")
        aliases = json.loads(_ALIASES.read_text(encoding="utf-8"))
        rows = aliases.get("aliases") or []
        self.assertTrue(any(str(x.get("mode")) == "read_only_compatibility" for x in rows))
        self.assertTrue(all(bool(x.get("allow_new_writes")) is False for x in rows))

    def test_atomisches_schreiben(self) -> None:
        build_runtime_identifier_migration_plan(explicit_overwrite=True)
        self.assertTrue(_PLAN.is_file())
        self.assertTrue(_ALIASES.is_file())
        self.assertTrue(_WORKSPACE.is_file())
        self.assertFalse((_HANDOFF / "setuphelfer_runtime_identifier_migration_plan.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_setuphelfer_runtime_identifier_migration.py"
        t = src.read_text(encoding="utf-8")
        for bad in ("subprocess", "os.system", "mount", "umount", "mkfs", "dd "):
            self.assertNotIn(bad, t)

    def test_keine_runtime_manipulation(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_setuphelfer_runtime_identifier_migration.py"
        t = src.read_text(encoding="utf-8")
        for bad in ("chmod(", "chown(", "systemctl", "unlink(", "rmtree("):
            self.assertNotIn(bad, t)


if __name__ == "__main__":
    unittest.main()
