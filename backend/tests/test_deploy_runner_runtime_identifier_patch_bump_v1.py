from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_runtime_identifier_patch_bump_apply import (
    apply_runtime_identifier_patch_bump,
    build_runtime_identifier_patch_bump_postcheck,
)
from deploy.runner_runtime_identifier_patch_bump_preparation import prepare_runtime_identifier_patch_bump
from deploy.runner_runtime_identifier_zero_state_verification import verify_runtime_identifier_zero_state

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_ZERO = _HANDOFF / "runtime_identifier_zero_state_verification.json"
_PREP = _HANDOFF / "runtime_identifier_patch_bump_preparation.json"
_RES = _HANDOFF / "runtime_identifier_patch_bump_apply_result.json"
_POST = _HANDOFF / "runtime_identifier_patch_bump_postcheck.json"
_CFG = _REPO_ROOT / "config" / "version.json"
_PKG = _REPO_ROOT / "package.json"
_PKGF = _REPO_ROOT / "frontend" / "package.json"
_TAURI = _REPO_ROOT / "frontend" / "src-tauri" / "tauri.conf.json"
_VS = _HANDOFF / "version_state.json"
_TR = _HANDOFF / "phase_release_tracking.json"

_ELIM = _HANDOFF / "runtime_identifier_elimination_postcheck.json"
_ALIAS = _HANDOFF / "runtime_compatibility_alias_validation.json"
_CONS = _HANDOFF / "setuphelfer_identifier_consistency_check.json"
_INV = _HANDOFF / "legacy_identifier_inventory.json"
_HOT = _HANDOFF / "legacy_identifier_hotspot_analysis.json"


class DeployRunnerRuntimeIdentifierPatchBumpV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._cfg_bak = _CFG.read_text(encoding="utf-8")
        self._pkg_bak = _PKG.read_text(encoding="utf-8")
        self._pkgf_bak = _PKGF.read_text(encoding="utf-8")
        self._tauri_bak = _TAURI.read_text(encoding="utf-8")
        self._vs_bak = _VS.read_bytes() if _VS.exists() else None
        self._tr_bak = _TR.read_bytes() if _TR.exists() else None
        self._elim_bak = _ELIM.read_bytes() if _ELIM.exists() else None
        self._alias_bak = _ALIAS.read_bytes() if _ALIAS.exists() else None
        self._cons_bak = _CONS.read_bytes() if _CONS.exists() else None
        self._inv_bak = _INV.read_bytes() if _INV.exists() else None
        self._hot_bak = _HOT.read_bytes() if _HOT.exists() else None
        for p in (_ZERO, _PREP, _RES, _POST):
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        _CFG.write_text(self._cfg_bak, encoding="utf-8")
        _PKG.write_text(self._pkg_bak, encoding="utf-8")
        _PKGF.write_text(self._pkgf_bak, encoding="utf-8")
        _TAURI.write_text(self._tauri_bak, encoding="utf-8")
        if self._vs_bak is None:
            _VS.unlink(missing_ok=True)
        else:
            _VS.write_bytes(self._vs_bak)
        if self._tr_bak is None:
            _TR.unlink(missing_ok=True)
        else:
            _TR.write_bytes(self._tr_bak)
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
        for p in (_ZERO, _PREP, _RES, _POST):
            p.unlink(missing_ok=True)

    def _write_zero_inputs(self) -> None:
        _ELIM.write_text(
            json.dumps(
                {
                    "after_runtime_identifier_count": 0,
                    "critical_remaining": 0,
                    "high_remaining": 0,
                    "consistency_status": "ok",
                }
            ),
            encoding="utf-8",
        )
        _ALIAS.write_text(
            json.dumps({"legacy_identifiers_only_in_compat_contract": True, "issues": []}),
            encoding="utf-8",
        )
        _CONS.write_text(json.dumps({"check_status": "ok", "findings": []}), encoding="utf-8")
        _INV.write_text(json.dumps({"counts": {"active_runtime_identifier": 0}, "findings": []}), encoding="utf-8")
        _HOT.write_text(json.dumps({"remaining_identifier_count": 0, "clusters": {}}), encoding="utf-8")

    def test_prepare_nur_bei_zero_state_ok(self) -> None:
        self._write_zero_inputs()
        verify_runtime_identifier_zero_state(explicit_overwrite=True)
        pr = prepare_runtime_identifier_patch_bump(explicit_overwrite=True)
        self.assertEqual(pr.get("runtime_identifier_patch_bump_preparation_status"), "ok")
        body = pr.get("runtime_identifier_patch_bump_preparation") or {}
        self.assertTrue(body.get("no_auto_apply"))
        self.assertEqual(body.get("release_stage"), "internal_testing")

    def test_apply_ohne_flag_blockiert(self) -> None:
        self._write_zero_inputs()
        verify_runtime_identifier_zero_state(explicit_overwrite=True)
        prepare_runtime_identifier_patch_bump(explicit_overwrite=True)
        res = apply_runtime_identifier_patch_bump(explicit_overwrite=True, explicit_apply_patch_bump=False)
        self.assertEqual(res.get("runtime_identifier_patch_bump_apply_status"), "blocked")

    def test_apply_nur_erlaubte_versionsdateien(self) -> None:
        self._write_zero_inputs()
        verify_runtime_identifier_zero_state(explicit_overwrite=True)
        prepare_runtime_identifier_patch_bump(explicit_overwrite=True)
        cur = json.loads(_CFG.read_text(encoding="utf-8")).get("project_version")
        _VS.write_text(
            json.dumps(
                {
                    "current_version": cur,
                    "previous_version": "1.6.0",
                    "strict_mode_phase": "laptop_failure_finalization_chain",
                    "phase_status": "completed",
                    "release_readiness": "internal_testing",
                    "test_status": "green",
                }
            ),
            encoding="utf-8",
        )
        _TR.write_text(
            json.dumps(
                {
                    "tracked_phases": [
                        {
                            "phase_name": "laptop_failure_finalization_chain",
                            "version": cur,
                            "test_status": "green",
                            "evidence_complete": True,
                            "release_level": "internal_testing",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        prep_expected = json.loads(_PREP.read_text(encoding="utf-8")).get("suggested_next_version")
        res = apply_runtime_identifier_patch_bump(explicit_overwrite=True, explicit_apply_patch_bump=True)
        self.assertEqual(res.get("runtime_identifier_patch_bump_apply_status"), "ok")
        new_v = json.loads(_CFG.read_text(encoding="utf-8")).get("project_version")
        self.assertEqual(new_v, prep_expected)
        updated = (res.get("runtime_identifier_patch_bump_apply") or {}).get("updated_files") or []
        for rel in (
            "config/version.json",
            "package.json",
            "frontend/package.json",
            "frontend/src-tauri/tauri.conf.json",
            "docs/evidence/runtime-results/handoff/version_state.json",
            "docs/evidence/runtime-results/handoff/phase_release_tracking.json",
        ):
            self.assertIn(rel, updated)

    def test_postcheck_schreibt(self) -> None:
        pc = build_runtime_identifier_patch_bump_postcheck(explicit_overwrite=True)
        self.assertIn(str(pc.get("runtime_identifier_patch_bump_postcheck_status") or ""), ("ok", "review_required", "blocked"))
        self.assertTrue(_POST.is_file())

    def test_keine_git_release_in_runner(self) -> None:
        for name in (
            "runner_runtime_identifier_patch_bump_apply.py",
            "runner_runtime_identifier_patch_bump_preparation.py",
        ):
            t = (Path(__file__).resolve().parents[1] / "deploy" / name).read_text(encoding="utf-8")
            for bad in ("git tag", "gh release", "npm publish", "systemctl"):
                self.assertNotIn(bad, t)


if __name__ == "__main__":
    unittest.main()
