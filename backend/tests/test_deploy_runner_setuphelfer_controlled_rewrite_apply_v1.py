from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_setuphelfer_controlled_rewrite_apply import apply_setuphelfer_controlled_rewrite

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_PLAN = _HANDOFF / "setuphelfer_safe_rewrite_plan.json"
_RESULT = _HANDOFF / "setuphelfer_controlled_rewrite_result.json"
_BACKUP_DIR = _HANDOFF / "legacy-backups"
_FIXTURE = _REPO_ROOT / "backend/tests/_legacy_apply_fixture.txt"


class DeployRunnerSetuphelferControlledRewriteApplyV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._plan_bak = _PLAN.read_text(encoding="utf-8") if _PLAN.exists() else None
        self._result_bak = _RESULT.read_text(encoding="utf-8") if _RESULT.exists() else None
        _RESULT.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("setuphelfer_controlled_rewrite_result.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._plan_bak is None:
            _PLAN.unlink(missing_ok=True)
        else:
            _PLAN.write_text(self._plan_bak, encoding="utf-8")
        if self._result_bak is None:
            _RESULT.unlink(missing_ok=True)
        else:
            _RESULT.write_text(self._result_bak, encoding="utf-8")
        for p in _BACKUP_DIR.glob("*.legacy-backup"):
            p.unlink(missing_ok=True)

    def test_controlled_apply_backup_und_rewrite(self) -> None:
        _FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        _FIXTURE.write_text("export PI_INSTALLER_DIR=1\n", encoding="utf-8")
        try:
            _PLAN.write_text(
                json.dumps(
                    {
                        "plan_status": "ok",
                        "entries": [
                            {
                                "source_file": "backend/tests/_legacy_apply_fixture.txt",
                                "legacy_token": "PI_INSTALLER_",
                                "replacement": "SETUPHELFER_",
                                "classification": "rename_now",
                                "write_allowed": True,
                                "reason": "test",
                            }
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            res = apply_setuphelfer_controlled_rewrite(
                explicit_overwrite=True,
                run_post_consistency_check=False,
            )
            self.assertIn(res.get("apply_status"), ("ok", "review_required"))
            self.assertIn("SETUPHELFER_", _FIXTURE.read_text(encoding="utf-8"))
            backups = list(_BACKUP_DIR.glob("*.legacy-backup"))
            self.assertTrue(backups)
            meta = json.loads(backups[0].read_text(encoding="utf-8"))
            self.assertIn("original_text", meta)
        finally:
            _FIXTURE.write_text("export PI_INSTALLER_DIR=1\n", encoding="utf-8")

    def test_evidence_wird_nicht_ueberschrieben(self) -> None:
        ev = _REPO_ROOT / "docs/evidence/_legacy_apply_should_skip.txt"
        ev.parent.mkdir(parents=True, exist_ok=True)
        ev.write_text("PI_INSTALLER_X=1\n", encoding="utf-8")
        try:
            _PLAN.write_text(
                json.dumps(
                    {
                        "plan_status": "ok",
                        "entries": [
                            {
                                "source_file": "docs/evidence/_legacy_apply_should_skip.txt",
                                "legacy_token": "PI_INSTALLER_",
                                "replacement": "SETUPHELFER_",
                                "classification": "rename_now",
                                "write_allowed": True,
                                "reason": "test",
                            }
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            apply_setuphelfer_controlled_rewrite(explicit_overwrite=True, run_post_consistency_check=False)
            self.assertIn("PI_INSTALLER_", ev.read_text(encoding="utf-8"))
        finally:
            ev.unlink(missing_ok=True)

    def test_keine_binaries(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_setuphelfer_controlled_rewrite_apply.py"
        t = src.read_text(encoding="utf-8")
        self.assertIn("_is_probably_text_file", t)

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_setuphelfer_controlled_rewrite_apply.py"
        t = src.read_text(encoding="utf-8")
        for bad in ("subprocess", "os.system", "chmod", "chown", "systemctl"):
            self.assertNotIn(bad, t)

    def test_keine_verbotenen_unterrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        c = routes.read_text(encoding="utf-8")
        start = c.find("/setuphelfer-controlled-rewrite-apply")
        self.assertGreater(start, 0)
        block = c[start : start + 1000]
        for bad in ("/release", "/publish", "/tag", "/delete", "/execute"):
            self.assertNotIn(bad, block)


if __name__ == "__main__":
    unittest.main()
