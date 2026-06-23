from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_setuphelfer_runtime_identifier_elimination import (
    apply_runtime_identifier_elimination,
    build_runtime_identifier_elimination_plan,
    build_runtime_identifier_elimination_targets,
    validate_runtime_compatibility_aliases,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_HOT = _HANDOFF / "legacy_identifier_hotspot_analysis.json"
_TGT = _HANDOFF / "runtime_identifier_elimination_targets.json"
_PLAN = _HANDOFF / "runtime_identifier_elimination_plan.json"
_RES = _HANDOFF / "runtime_identifier_elimination_result.json"
_VAL = _HANDOFF / "runtime_compatibility_alias_validation.json"
_SAFE = _HANDOFF / "setuphelfer_safe_rewrite_plan.json"
_COMPAT = _HANDOFF / "compatibility_aliases.json"
_INV = _HANDOFF / "legacy_identifier_inventory.json"
_CONS = _HANDOFF / "setuphelfer_identifier_consistency_check.json"
_POST2 = _HANDOFF / "setuphelfer_identifier_cleanup_cycle_2_postcheck.json"


class DeployRunnerSetuphelferRuntimeIdentifierEliminationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._hot_bak = _HOT.read_bytes() if _HOT.exists() else None
        self._safe_bak = _SAFE.read_bytes() if _SAFE.exists() else None
        self._compat_bak = _COMPAT.read_bytes() if _COMPAT.exists() else None
        self._inv_bak = _INV.read_bytes() if _INV.exists() else None
        self._cons_bak = _CONS.read_bytes() if _CONS.exists() else None
        self._post2_bak = _POST2.read_bytes() if _POST2.exists() else None
        for p in (_TGT, _PLAN, _RES, _VAL):
            p.unlink(missing_ok=True)
            p.with_suffix(p.suffix + ".tmp").unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._hot_bak is None:
            _HOT.unlink(missing_ok=True)
        else:
            _HOT.write_bytes(self._hot_bak)
        if self._safe_bak is None:
            _SAFE.unlink(missing_ok=True)
        else:
            _SAFE.write_bytes(self._safe_bak)
        if self._compat_bak is None:
            _COMPAT.unlink(missing_ok=True)
        else:
            _COMPAT.write_bytes(self._compat_bak)
        if self._inv_bak is None:
            _INV.unlink(missing_ok=True)
        else:
            _INV.write_bytes(self._inv_bak)
        if self._cons_bak is None:
            _CONS.unlink(missing_ok=True)
        else:
            _CONS.write_bytes(self._cons_bak)
        if self._post2_bak is None:
            _POST2.unlink(missing_ok=True)
        else:
            _POST2.write_bytes(self._post2_bak)
        for p in (_TGT, _PLAN, _RES, _VAL):
            p.unlink(missing_ok=True)
            p.with_suffix(p.suffix + ".tmp").unlink(missing_ok=True)

    def test_targets_keine_tests_und_keine_docs(self) -> None:
        hot = {
            "clusters": {
                "backend_runtime": [
                    {
                        "path": "backend/tests/_elim_x.py",
                        "line": 1,
                        "tokens": ["PI_INSTALLER_"],
                        "criticality": "critical",
                    }
                ],
                "api": [
                    {
                        "path": "backend/deploy/routes.py",
                        "line": 1,
                        "tokens": ["pi-installer"],
                        "criticality": "critical",
                    }
                ],
            }
        }
        _HOT.write_text(json.dumps(hot), encoding="utf-8")
        _POST2.write_text(json.dumps({"remaining_runtime_identifiers": []}), encoding="utf-8")
        _CONS.write_text(json.dumps({"findings": []}), encoding="utf-8")
        build_runtime_identifier_elimination_targets(explicit_overwrite=True)
        data = json.loads(_TGT.read_text(encoding="utf-8"))
        paths = {t["path"] for t in (data.get("targets") or [])}
        self.assertNotIn("backend/tests/_elim_x.py", paths)
        self.assertIn("backend/deploy/routes.py", paths)

    def test_plan_write_allowed_nur_rename_now(self) -> None:
        hot = {
            "clusters": {
                "api": [
                    {
                        "path": "backend/tests/_elim_apply.txt",
                        "line": 1,
                        "tokens": ["PI_INSTALLER_"],
                        "criticality": "critical",
                    }
                ],
            }
        }
        _HOT.write_text(json.dumps(hot), encoding="utf-8")
        _POST2.write_text(json.dumps({"remaining_runtime_identifiers": []}), encoding="utf-8")
        _CONS.write_text(json.dumps({"findings": []}), encoding="utf-8")
        build_runtime_identifier_elimination_targets(explicit_overwrite=True)
        tgt = json.loads(_TGT.read_text(encoding="utf-8"))
        self.assertEqual(len(tgt.get("targets") or []), 0)

        rel = "backend/deploy/_elim_runtime_tmp.py"
        hot2 = {
            "clusters": {
                "api": [
                    {
                        "path": rel,
                        "line": 1,
                        "tokens": ["PI_INSTALLER_"],
                        "criticality": "critical",
                    }
                ],
            }
        }
        _HOT.write_text(json.dumps(hot2), encoding="utf-8")
        fx = _REPO_ROOT / rel
        existed_before = fx.exists()
        prev = fx.read_text(encoding="utf-8") if existed_before else ""
        fx.parent.mkdir(parents=True, exist_ok=True)
        fx.write_text("x=PI_INSTALLER_HOME\n", encoding="utf-8")
        try:
            build_runtime_identifier_elimination_targets(explicit_overwrite=True)
            _SAFE.write_text(
                json.dumps(
                    {
                        "entries": [
                            {
                                "source_file": rel,
                                "legacy_token": "PI_INSTALLER_",
                                "replacement": "SETUPHELFER_",
                                "classification": "rename_now",
                                "write_allowed": True,
                                "reason": "ok",
                            }
                        ],
                        "plan_status": "ok",
                    }
                ),
                encoding="utf-8",
            )
            build_runtime_identifier_elimination_plan(explicit_overwrite=True)
            plan = json.loads(_PLAN.read_text(encoding="utf-8"))
            rows = plan.get("entries") or []
            self.assertTrue(any(r.get("write_allowed") for r in rows))
            apply_runtime_identifier_elimination(explicit_overwrite=True)
            self.assertIn("SETUPHELFER_", fx.read_text(encoding="utf-8"))
            backups = list((_HANDOFF / "legacy-backups").glob("*.legacy-backup"))
            self.assertTrue(any("runtime_identifier_elimination_apply" in b.read_text(encoding="utf-8") for b in backups))
        finally:
            if existed_before:
                fx.write_text(prev, encoding="utf-8")
            else:
                fx.unlink(missing_ok=True)

    def test_alias_validation_struktur(self) -> None:
        _COMPAT.write_text(
            json.dumps(
                {
                    "aliases": [
                        {
                            "legacy_identifier": "PI_INSTALLER_*",
                            "mode": "read_only_compatibility",
                            "allow_new_writes": False,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        _INV.write_text(
            json.dumps(
                {
                    "counts": {"active_runtime_identifier": 0},
                    "findings": [],
                }
            ),
            encoding="utf-8",
        )
        validate_runtime_compatibility_aliases(explicit_overwrite=True)
        v = json.loads(_VAL.read_text(encoding="utf-8"))
        self.assertTrue(v.get("aliases_all_read_only_mode"))

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_setuphelfer_runtime_identifier_elimination.py"
        t = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", t)
        self.assertNotIn("os.system", t)
        self.assertNotIn("systemctl", t)

    def test_routes_keine_execute_delete_release(self) -> None:
        deploy_dir = Path(__file__).resolve().parents[1] / "deploy"
        versioning_routes = (deploy_dir / "routes_versioning.py").read_text(encoding="utf-8")
        routes_py = (deploy_dir / "routes.py").read_text(encoding="utf-8")
        start = versioning_routes.find("/runtime-identifier-elimination-targets")
        self.assertGreater(start, 0)
        block = versioning_routes[start : start + 4500]
        for bad in ("/delete", "/execute", "/release", "/publish", "/systemctl", "service restart"):
            self.assertNotIn(bad, block)
        self.assertNotIn('@router.post("/runtime-identifier-elimination-targets")', routes_py)


if __name__ == "__main__":
    unittest.main()
