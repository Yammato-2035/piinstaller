from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_setuphelfer_identifier_consistency_check import check_setuphelfer_identifier_consistency

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_OUT = _HANDOFF / "setuphelfer_identifier_consistency_check.json"


class DeployRunnerSetuphelferIdentifierConsistencyCheckV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        _OUT.unlink(missing_ok=True)
        (_HANDOFF / "setuphelfer_identifier_consistency_check.json.tmp").unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def test_neue_pi_installer_env_blockiert(self) -> None:
        res = check_setuphelfer_identifier_consistency(explicit_overwrite=True)
        blocked = set(res.get("blocked_reasons") or [])
        self.assertIn("SETUPHELFER_IDENTIFIER_CONSISTENCY_NEW_PI_INSTALLER_ENV", blocked)

    def test_neue_pi_installer_services_blockiert(self) -> None:
        res = check_setuphelfer_identifier_consistency(explicit_overwrite=True)
        blocked = set(res.get("blocked_reasons") or [])
        self.assertIn("SETUPHELFER_IDENTIFIER_CONSISTENCY_NEW_PI_INSTALLER_SERVICE", blocked)

    def test_historische_docs_und_evidence_erlaubt(self) -> None:
        res = check_setuphelfer_identifier_consistency(explicit_overwrite=True)
        check = res.get("check") or {}
        findings = check.get("findings") or []
        self.assertTrue(any(bool(x.get("allowed")) for x in findings))

    def test_atomisches_schreiben(self) -> None:
        check_setuphelfer_identifier_consistency(explicit_overwrite=True)
        self.assertTrue(_OUT.is_file())
        self.assertFalse((_HANDOFF / "setuphelfer_identifier_consistency_check.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_setuphelfer_identifier_consistency_check.py"
        t = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", t)
        self.assertNotIn("os.system", t)

    def test_keine_release_publish_tag_execute_delete_routen(self) -> None:
        deploy_dir = Path(__file__).resolve().parents[1] / "deploy"
        evidence_routes = (deploy_dir / "routes_evidence.py").read_text(encoding="utf-8")
        routes_py = (deploy_dir / "routes.py").read_text(encoding="utf-8")
        start = evidence_routes.find("/setuphelfer-identifier-consistency-check")
        self.assertGreater(start, 0)
        block = evidence_routes[start : start + 1000]
        for bad in ("/release", "/publish", "/tag", "/execute", "/delete"):
            self.assertNotIn(bad, block)
        self.assertNotIn('@router.post("/setuphelfer-identifier-consistency-check")', routes_py)

    def test_output_json_parsebar(self) -> None:
        check_setuphelfer_identifier_consistency(explicit_overwrite=True)
        parsed = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertIn("check_status", parsed)

    def test_post_check_erneut_ausfuehrbar(self) -> None:
        r1 = check_setuphelfer_identifier_consistency(explicit_overwrite=True)
        r2 = check_setuphelfer_identifier_consistency(explicit_overwrite=True)
        self.assertIn(str(r1.get("check_status") or ""), ("ok", "blocked", "review_required"))
        self.assertIn(str(r2.get("check_status") or ""), ("ok", "blocked", "review_required"))


if __name__ == "__main__":
    unittest.main()
