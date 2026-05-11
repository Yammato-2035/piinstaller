from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_setuphelfer_safe_rewrite_plan import build_setuphelfer_safe_rewrite_plan

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_CLS = _HANDOFF / "legacy_identifier_cleanup_classification.json"
_PLAN = _HANDOFF / "setuphelfer_safe_rewrite_plan.json"


class DeployRunnerSetuphelferSafeRewritePlanV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._cls_bak = _CLS.read_text(encoding="utf-8") if _CLS.exists() else None
        self._plan_bak = _PLAN.read_text(encoding="utf-8") if _PLAN.exists() else None
        _PLAN.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("setuphelfer_safe_rewrite_plan.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._cls_bak is None:
            _CLS.unlink(missing_ok=True)
        else:
            _CLS.write_text(self._cls_bak, encoding="utf-8")
        if self._plan_bak is None:
            _PLAN.unlink(missing_ok=True)
        else:
            _PLAN.write_text(self._plan_bak, encoding="utf-8")

    def test_write_allowed_nur_fuer_sichere_aktive_dateien(self) -> None:
        _CLS.write_text(
            json.dumps(
                {
                    "classification_status": "ok",
                    "items": [
                        {
                            "path": "backend/tests/_legacy_plan_fixture.txt",
                            "line": 1,
                            "tokens": ["PI_INSTALLER_"],
                            "cleanup_classification": "rename_now",
                            "reason": "test",
                        },
                        {
                            "path": "docs/Foo.md",
                            "line": 1,
                            "tokens": ["pi-installer"],
                            "cleanup_classification": "needs_manual_review",
                            "reason": "test",
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        res = build_setuphelfer_safe_rewrite_plan(explicit_overwrite=True)
        entries = (res.get("plan") or {}).get("entries") or []
        by_file = {e["source_file"]: e for e in entries if e.get("legacy_token") == "PI_INSTALLER_"}
        row = by_file.get("backend/tests/_legacy_plan_fixture.txt")
        self.assertIsNotNone(row)
        self.assertTrue(row.get("write_allowed"))
        doc_rows = [e for e in entries if e.get("source_file") == "docs/Foo.md"]
        self.assertTrue(all(not e.get("write_allowed") for e in doc_rows))

    def test_historical_keep_write_false(self) -> None:
        _CLS.write_text(
            json.dumps(
                {
                    "classification_status": "ok",
                    "items": [
                        {
                            "path": "docs/evidence/x.md",
                            "line": 1,
                            "tokens": ["pi-installer"],
                            "cleanup_classification": "historical_keep",
                            "reason": "test",
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        res = build_setuphelfer_safe_rewrite_plan(explicit_overwrite=True)
        entries = (res.get("plan") or {}).get("entries") or []
        self.assertTrue(all(not e.get("write_allowed") for e in entries))

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_setuphelfer_safe_rewrite_plan.py"
        t = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", t)

    def test_keine_verbotenen_unterrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        c = routes.read_text(encoding="utf-8")
        start = c.find("/setuphelfer-safe-rewrite-plan")
        self.assertGreater(start, 0)
        block = c[start : start + 900]
        for bad in ("/release", "/publish", "/tag", "/delete", "/execute"):
            self.assertNotIn(bad, block)


if __name__ == "__main__":
    unittest.main()
