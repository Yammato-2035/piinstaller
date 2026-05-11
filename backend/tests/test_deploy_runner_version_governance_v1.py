from __future__ import annotations

import unittest
from pathlib import Path

from deploy.runner_version_governance import build_version_governance_state

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_OUT = _HANDOFF / "version_state.json"
_CONFIG_VERSION = _REPO_ROOT / "config" / "version.json"
_TRACKING = _HANDOFF / "phase_release_tracking.json"


class DeployRunnerVersionGovernanceV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self._config_orig = _CONFIG_VERSION.read_text(encoding="utf-8") if _CONFIG_VERSION.exists() else None
        self._tracking_orig = _TRACKING.read_text(encoding="utf-8") if _TRACKING.exists() else None
        self._version_state_orig = _OUT.read_text(encoding="utf-8") if _OUT.exists() else None
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        _OUT.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("version_state.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        _OUT.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("version_state.json.tmp"):
            tmp.unlink(missing_ok=True)
        if self._version_state_orig is None:
            _OUT.unlink(missing_ok=True)
        else:
            _OUT.write_text(self._version_state_orig, encoding="utf-8")
        if self._config_orig is None:
            _CONFIG_VERSION.unlink(missing_ok=True)
        else:
            _CONFIG_VERSION.write_text(self._config_orig, encoding="utf-8")
        if self._tracking_orig is None:
            _TRACKING.unlink(missing_ok=True)
        else:
            _TRACKING.write_text(self._tracking_orig, encoding="utf-8")

    def test_patch_bump(self) -> None:
        res = build_version_governance_state(
            previous_version="1.5.0",
            changes=["docs"],
            explicit_overwrite=True,
        )
        self.assertEqual(res.get("state_status"), "ok")
        self.assertEqual((res.get("state") or {}).get("current_version"), "1.5.1")

    def test_minor_bump(self) -> None:
        res = build_version_governance_state(
            previous_version="1.5.0",
            changes=["strict_mode_module", "api_route"],
            explicit_overwrite=True,
        )
        self.assertEqual((res.get("state") or {}).get("current_version"), "1.6.0")

    def test_major_bump(self) -> None:
        res = build_version_governance_state(
            previous_version="1.5.0",
            changes=["architecture"],
            explicit_overwrite=True,
        )
        self.assertEqual((res.get("state") or {}).get("current_version"), "2.0.0")

    def test_atomisches_schreiben(self) -> None:
        build_version_governance_state(previous_version="1.5.0", changes=["docs"], explicit_overwrite=True)
        self.assertTrue(_OUT.is_file())
        self.assertFalse((_HANDOFF / "version_state.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_version_governance.py"
        t = src.read_text(encoding="utf-8")
        for bad in ("subprocess", "os.system", "mkfs", "dd ", "wipefs", "mount", "umount", "restore"):
            self.assertNotIn(bad, t)

    def test_keine_release_deploy_tag_publish_subrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        c = routes.read_text(encoding="utf-8")
        start = c.find("/version-governance/state")
        self.assertGreater(start, 0)
        block = c[start : start + 900]
        for bad in ("/release", "/tag", "/publish", "/execute"):
            self.assertNotIn(bad, block)


if __name__ == "__main__":
    unittest.main()
