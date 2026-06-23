from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_version_source_of_truth_check import check_version_source_of_truth_consistency

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_VERSION_STATE = _HANDOFF / "version_state.json"
_OUT = _HANDOFF / "version_source_of_truth_check.json"
_ROOT_PKG = _REPO_ROOT / "package.json"
_FRONT_PKG = _REPO_ROOT / "frontend" / "package.json"
_CFG = _REPO_ROOT / "config" / "version.json"


class DeployRunnerVersionSourceOfTruthCheckV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        _OUT.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("version_source_of_truth_check.json.tmp"):
            tmp.unlink(missing_ok=True)
        self.root_pkg_orig = _ROOT_PKG.read_text(encoding="utf-8")
        self.front_pkg_orig = _FRONT_PKG.read_text(encoding="utf-8")
        cfg = json.loads(_CFG.read_text(encoding="utf-8"))
        current = str(cfg.get("project_version") or "1.7.0")
        cparts = [int(x) for x in current.split(".")]
        previous = f"{cparts[0]}.{cparts[1]-1}.0" if cparts[1] > 0 else f"{max(cparts[0]-1,0)}.0.0"
        self.vs_orig = _VERSION_STATE.read_text(encoding="utf-8") if _VERSION_STATE.exists() else None
        _VERSION_STATE.write_text(
            json.dumps(
                {
                    "version_schema_version": 1,
                    "current_version": current,
                    "previous_version": previous,
                    "strict_mode_phase": "laptop_failure_finalization_chain",
                    "phase_status": "completed",
                    "release_readiness": "internal_testing",
                    "generated_at": "2026-05-09T00:00:00Z",
                    "completed_modules": [],
                    "evidence_artifacts": [],
                    "test_status": "green",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        _ROOT_PKG.write_text(self.root_pkg_orig, encoding="utf-8")
        _FRONT_PKG.write_text(self.front_pkg_orig, encoding="utf-8")
        if self.vs_orig is None:
            _VERSION_STATE.unlink(missing_ok=True)
        else:
            _VERSION_STATE.write_text(self.vs_orig, encoding="utf-8")
        _OUT.unlink(missing_ok=True)

    def _set_pkg_version(self, path: Path, version: str) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["version"] = version
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def test_drift_frontend_backend_blockiert(self) -> None:
        self._set_pkg_version(_FRONT_PKG, "9.9.9")
        res = check_version_source_of_truth_consistency(explicit_overwrite=True)
        self.assertEqual(res.get("check_status"), "blocked")

    def test_fehlende_version_json_blockiert(self) -> None:
        cfg = _REPO_ROOT / "config" / "version.json"
        bak = cfg.read_text(encoding="utf-8")
        cfg.unlink(missing_ok=True)
        try:
            res = check_version_source_of_truth_consistency(explicit_overwrite=True)
            self.assertEqual(res.get("check_status"), "blocked")
        finally:
            cfg.write_text(bak, encoding="utf-8")

    def test_ungueltige_release_stage_blockiert(self) -> None:
        cfg = _REPO_ROOT / "config" / "version.json"
        data = json.loads(cfg.read_text(encoding="utf-8"))
        old = dict(data)
        data["release_stage"] = "broken"
        cfg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        try:
            res = check_version_source_of_truth_consistency(explicit_overwrite=True)
            self.assertEqual(res.get("check_status"), "blocked")
        finally:
            cfg.write_text(json.dumps(old, indent=2) + "\n", encoding="utf-8")

    def test_rueckwaerts_laufende_version_blockiert(self) -> None:
        _VERSION_STATE.write_text(
            json.dumps(
                {
                    "version_schema_version": 1,
                    "current_version": "1.6.0",
                    "previous_version": "1.7.0",
                    "strict_mode_phase": "laptop_failure_finalization_chain",
                    "phase_status": "completed",
                    "release_readiness": "internal_testing",
                    "generated_at": "2026-05-09T00:00:00Z",
                    "completed_modules": [],
                    "evidence_artifacts": [],
                    "test_status": "green",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        res = check_version_source_of_truth_consistency(explicit_overwrite=True)
        self.assertEqual(res.get("check_status"), "blocked")

    def test_atomisches_schreiben(self) -> None:
        res = check_version_source_of_truth_consistency(explicit_overwrite=True)
        self.assertIn(res.get("check_status"), ("ok", "blocked"))
        self.assertTrue(_OUT.is_file())
        self.assertFalse((_HANDOFF / "version_source_of_truth_check.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_version_source_of_truth_check.py"
        t = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", t)
        self.assertNotIn("os.system", t)

    def test_keine_release_publish_tag_routen(self) -> None:
        deploy_dir = Path(__file__).resolve().parents[1] / "deploy"
        governance_routes = (deploy_dir / "routes_governance.py").read_text(encoding="utf-8")
        routes_py = (deploy_dir / "routes.py").read_text(encoding="utf-8")
        start = governance_routes.find("/version-source-of-truth-check")
        self.assertGreater(start, 0)
        block = governance_routes[start : start + 900]
        for bad in ("/release", "/publish", "/tag"):
            self.assertNotIn(bad, block)
        self.assertNotIn('@router.post("/version-source-of-truth-check")', routes_py)


if __name__ == "__main__":
    unittest.main()
