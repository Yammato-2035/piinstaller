from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_version_consistency_check import check_version_consistency

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_VS = _HANDOFF / "version_state.json"
_TR = _HANDOFF / "phase_release_tracking.json"
_OUT = _HANDOFF / "version_consistency_check.json"


class DeployRunnerVersionConsistencyCheckV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in (_VS, _TR, _OUT):
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("version_consistency_check.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write(self, cur: str, prev: str, *, phase: str = "laptop_failure_finalization_chain", tracked_version: str | None = None) -> None:
        _VS.write_text(
            json.dumps(
                {
                    "current_version": cur,
                    "previous_version": prev,
                    "strict_mode_phase": phase,
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
                            "phase_name": phase,
                            "phase_status": "completed",
                            "version": tracked_version or cur,
                            "test_status": "green",
                            "evidence_complete": True,
                            "release_level": "internal_testing",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    def test_rueckwaerts_laufende_version_blockiert(self) -> None:
        self._write("1.5.0", "1.6.0")
        res = check_version_consistency(explicit_overwrite=True)
        self.assertEqual(res.get("check_status"), "blocked")

    def test_missing_version_bump_blockiert(self) -> None:
        self._write("1.5.0", "1.5.0")
        res = check_version_consistency(explicit_overwrite=True)
        self.assertEqual(res.get("check_status"), "blocked")

    def test_inkonsistente_trackingdaten_blockieren(self) -> None:
        self._write("1.6.0", "1.5.0", tracked_version="1.5.9")
        res = check_version_consistency(explicit_overwrite=True)
        self.assertEqual(res.get("check_status"), "blocked")

    def test_ok_consistency(self) -> None:
        self._write("1.6.0", "1.5.0")
        res = check_version_consistency(explicit_overwrite=True)
        self.assertEqual(res.get("check_status"), "ok")

    def test_atomisches_schreiben(self) -> None:
        self._write("1.6.0", "1.5.0")
        check_version_consistency(explicit_overwrite=True)
        self.assertTrue(_OUT.is_file())
        self.assertFalse((_HANDOFF / "version_consistency_check.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_version_consistency_check.py"
        t = src.read_text(encoding="utf-8")
        for bad in ("subprocess", "os.system", "mkfs", "dd ", "wipefs", "mount", "umount", "restore"):
            self.assertNotIn(bad, t)

    def test_keine_release_deploy_tag_publish_unterrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        c = routes.read_text(encoding="utf-8")
        start = c.find("/version-governance/state")
        self.assertGreater(start, 0)
        block = c[start : start + 1000]
        for bad in ("/release", "/tag", "/publish", "/execute"):
            self.assertNotIn(bad, block)


if __name__ == "__main__":
    unittest.main()
