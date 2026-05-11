from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_runtime_identifier_zero_state_verification import verify_runtime_identifier_zero_state

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_OUT = _HANDOFF / "runtime_identifier_zero_state_verification.json"
_ELIM = _HANDOFF / "runtime_identifier_elimination_postcheck.json"
_ALIAS = _HANDOFF / "runtime_compatibility_alias_validation.json"
_CONS = _HANDOFF / "setuphelfer_identifier_consistency_check.json"
_INV = _HANDOFF / "legacy_identifier_inventory.json"
_HOT = _HANDOFF / "legacy_identifier_hotspot_analysis.json"


class DeployRunnerRuntimeIdentifierZeroStateVerificationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._elim_bak = _ELIM.read_bytes() if _ELIM.exists() else None
        self._alias_bak = _ALIAS.read_bytes() if _ALIAS.exists() else None
        self._cons_bak = _CONS.read_bytes() if _CONS.exists() else None
        self._inv_bak = _INV.read_bytes() if _INV.exists() else None
        self._hot_bak = _HOT.read_bytes() if _HOT.exists() else None
        _OUT.unlink(missing_ok=True)
        (_OUT.parent / (_OUT.name + ".tmp")).unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._elim_bak is None:
            _ELIM.unlink(missing_ok=True)
        else:
            _ELIM.write_bytes(self._elim_bak)
        if self._alias_bak is None:
            _ALIAS.unlink(missing_ok=True)
        else:
            _ALIAS.write_bytes(self._alias_bak)
        if self._cons_bak is None:
            _CONS.unlink(missing_ok=True)
        else:
            _CONS.write_bytes(self._cons_bak)
        if self._inv_bak is None:
            _INV.unlink(missing_ok=True)
        else:
            _INV.write_bytes(self._inv_bak)
        if self._hot_bak is None:
            _HOT.unlink(missing_ok=True)
        else:
            _HOT.write_bytes(self._hot_bak)
        _OUT.unlink(missing_ok=True)

    def _write_ok_inputs(self) -> None:
        _ELIM.write_text(
            json.dumps(
                {
                    "after_runtime_identifier_count": 0,
                    "critical_remaining": 0,
                    "high_remaining": 0,
                    "consistency_status": "ok",
                    "hotspot_status": "ok",
                }
            ),
            encoding="utf-8",
        )
        _ALIAS.write_text(
            json.dumps(
                {
                    "legacy_identifiers_only_in_compat_contract": True,
                    "issues": [],
                }
            ),
            encoding="utf-8",
        )
        _CONS.write_text(json.dumps({"check_status": "ok", "findings": []}), encoding="utf-8")
        _INV.write_text(
            json.dumps(
                {
                    "counts": {"active_runtime_identifier": 0},
                    "findings": [],
                }
            ),
            encoding="utf-8",
        )
        _HOT.write_text(
            json.dumps(
                {
                    "remaining_identifier_count": 0,
                    "clusters": {},
                }
            ),
            encoding="utf-8",
        )

    def test_zero_state_ok(self) -> None:
        self._write_ok_inputs()
        res = verify_runtime_identifier_zero_state(explicit_overwrite=True)
        self.assertEqual(res.get("runtime_identifier_zero_state_verification_status"), "ok")
        parsed = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertEqual(parsed.get("zero_state_status"), "ok")

    def test_runtime_rest_blockiert(self) -> None:
        self._write_ok_inputs()
        e = json.loads(_ELIM.read_text(encoding="utf-8"))
        e["after_runtime_identifier_count"] = 3
        _ELIM.write_text(json.dumps(e), encoding="utf-8")
        res = verify_runtime_identifier_zero_state(explicit_overwrite=True)
        self.assertEqual(res.get("runtime_identifier_zero_state_verification_status"), "blocked")

    def test_alias_warnung_review_required(self) -> None:
        self._write_ok_inputs()
        _ALIAS.write_text(
            json.dumps(
                {
                    "legacy_identifiers_only_in_compat_contract": True,
                    "issues": ["soft_warning"],
                }
            ),
            encoding="utf-8",
        )
        res = verify_runtime_identifier_zero_state(explicit_overwrite=True)
        self.assertEqual(res.get("runtime_identifier_zero_state_verification_status"), "review_required")

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_runtime_identifier_zero_state_verification.py"
        t = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", t)
        self.assertNotIn("systemctl", t)

    def test_routes_keine_release_execute(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        c = routes.read_text(encoding="utf-8")
        start = c.find("/runtime-identifier-zero-state-verification")
        self.assertGreater(start, 0)
        block = c[start : start + 4200]
        for bad in ("/release", "/publish", "/tag", "/execute", "/delete", "/deploy", "systemctl"):
            self.assertNotIn(bad, block)


if __name__ == "__main__":
    unittest.main()
