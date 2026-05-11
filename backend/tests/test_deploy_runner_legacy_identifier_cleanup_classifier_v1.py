from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_legacy_identifier_cleanup_classifier import classify_active_legacy_identifiers

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_INV = _HANDOFF / "legacy_identifier_inventory.json"
_OUT = _HANDOFF / "legacy_identifier_cleanup_classification.json"


class DeployRunnerLegacyIdentifierCleanupClassifierV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._inv_bak = _INV.read_text(encoding="utf-8") if _INV.exists() else None
        self._out_bak = _OUT.read_text(encoding="utf-8") if _OUT.exists() else None
        _OUT.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("legacy_identifier_cleanup_classification.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._inv_bak is None:
            _INV.unlink(missing_ok=True)
        else:
            _INV.write_text(self._inv_bak, encoding="utf-8")
        if self._out_bak is None:
            _OUT.unlink(missing_ok=True)
        else:
            _OUT.write_text(self._out_bak, encoding="utf-8")

    def test_aktive_identifier_klassifiziert_rename_now(self) -> None:
        fx = _REPO_ROOT / "backend/tests/_legacy_classifier_fixture.txt"
        fx.parent.mkdir(parents=True, exist_ok=True)
        fx.write_text("PI_INSTALLER_DIR=/opt/pi-installer\n", encoding="utf-8")
        try:
            _INV.write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "path": "backend/tests/_legacy_classifier_fixture.txt",
                                "line": 1,
                                "tokens": ["PI_INSTALLER_", "/opt/pi-installer"],
                                "classification": "active_runtime_identifier",
                            }
                        ],
                        "counts": {},
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            res = classify_active_legacy_identifiers(explicit_overwrite=True)
            self.assertIn(res.get("classification_status"), ("ok", "review_required", "blocked"))
            items = (res.get("classification") or {}).get("items") or []
            self.assertTrue(any(x.get("cleanup_classification") == "rename_now" for x in items))
        finally:
            fx.unlink(missing_ok=True)

    def test_historische_docs_bleiben_historical_keep(self) -> None:
        _INV.write_text(
            json.dumps(
                {
                    "findings": [
                        {
                            "path": "docs/evidence/runtime-results/handoff/foo.json",
                            "line": 1,
                            "tokens": ["pi-installer"],
                            "classification": "active_runtime_identifier",
                        }
                    ],
                    "counts": {},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        res = classify_active_legacy_identifiers(explicit_overwrite=True)
        items = (res.get("classification") or {}).get("items") or []
        self.assertTrue(any(x.get("cleanup_classification") == "historical_keep" for x in items))

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_legacy_identifier_cleanup_classifier.py"
        t = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", t)
        self.assertNotIn("os.system", t)

    def test_keine_verbotenen_unterrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        c = routes.read_text(encoding="utf-8")
        start = c.find("/legacy-identifier-cleanup-classification")
        self.assertGreater(start, 0)
        block = c[start : start + 900]
        for bad in ("/release", "/publish", "/tag", "/delete", "/execute"):
            self.assertNotIn(bad, block)


if __name__ == "__main__":
    unittest.main()
