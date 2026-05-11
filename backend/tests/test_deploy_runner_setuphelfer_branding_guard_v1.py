from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_setuphelfer_branding_guard import (
    build_setuphelfer_branding_guard_report,
    check_setuphelfer_branding_guard,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_INV = _HANDOFF / "legacy_identifier_inventory.json"
_ZERO = _HANDOFF / "runtime_identifier_zero_state_verification.json"
_ALIAS = _HANDOFF / "compatibility_aliases.json"
_OUT = _HANDOFF / "setuphelfer_branding_guard_check.json"
_ROUTES = _REPO_ROOT / "backend/deploy/routes.py"
_RUNNER = _REPO_ROOT / "backend/deploy/runner_setuphelfer_branding_guard.py"
_SCRIPT = _REPO_ROOT / "scripts/check-setuphelfer-branding-guard.sh"


class DeployRunnerSetuphelferBrandingGuardV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._inv_bak = _INV.read_bytes() if _INV.exists() else None
        self._zero_bak = _ZERO.read_bytes() if _ZERO.exists() else None
        self._alias_bak = _ALIAS.read_bytes() if _ALIAS.exists() else None
        _OUT.unlink(missing_ok=True)
        (_OUT.parent / (_OUT.name + ".tmp")).unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._inv_bak is None:
            _INV.unlink(missing_ok=True)
        else:
            _INV.write_bytes(self._inv_bak)
        if self._zero_bak is None:
            _ZERO.unlink(missing_ok=True)
        else:
            _ZERO.write_bytes(self._zero_bak)
        if self._alias_bak is None:
            _ALIAS.unlink(missing_ok=True)
        else:
            _ALIAS.write_bytes(self._alias_bak)
        _OUT.unlink(missing_ok=True)

    def _write_zero_ok(self) -> None:
        _ZERO.write_text(
            json.dumps({"zero_state_status": "ok", "zero_state_schema_version": 1}),
            encoding="utf-8",
        )

    def _write_alias_stub(self) -> None:
        _ALIAS.write_text(json.dumps({"legacy": []}), encoding="utf-8")

    def test_runtime_legacy_blocked(self) -> None:
        self._write_zero_ok()
        self._write_alias_stub()
        _INV.write_text(
            json.dumps(
                {
                    "counts": {"active_runtime_identifier": 1},
                    "findings": [
                        {
                            "classification": "active_runtime_identifier",
                            "path": "backend/api/foo.py",
                            "line": 1,
                            "tokens": ["pi-installer"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        res = build_setuphelfer_branding_guard_report(explicit_overwrite=True)
        self.assertEqual(res.get("setuphelfer_branding_guard_check_status"), "blocked")
        parsed = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertEqual(parsed.get("branding_guard_status"), "blocked")
        self.assertGreaterEqual(int(parsed.get("counts", {}).get("blocked_hits") or 0), 1)

    def test_historical_docs_allowed(self) -> None:
        self._write_zero_ok()
        self._write_alias_stub()
        _INV.write_text(
            json.dumps(
                {
                    "counts": {"active_runtime_identifier": 0},
                    "findings": [
                        {
                            "classification": "active_runtime_identifier",
                            "path": "docs/evidence/sample.md",
                            "line": 1,
                            "tokens": ["pi-installer"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        res = build_setuphelfer_branding_guard_report(explicit_overwrite=True)
        self.assertEqual(res.get("setuphelfer_branding_guard_check_status"), "ok")

    def test_compatibility_aliases_allowed(self) -> None:
        self._write_zero_ok()
        self._write_alias_stub()
        _INV.write_text(
            json.dumps(
                {
                    "counts": {"migration_alias": 1},
                    "findings": [
                        {
                            "classification": "migration_alias",
                            "path": "docs/evidence/runtime-results/handoff/compatibility_aliases.json",
                            "line": 2,
                            "tokens": ["PI_INSTALLER_HOME"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        res = build_setuphelfer_branding_guard_report(explicit_overwrite=True)
        self.assertEqual(res.get("setuphelfer_branding_guard_check_status"), "ok")

    def test_pi_installer_env_blocked_in_runtime(self) -> None:
        self._write_zero_ok()
        self._write_alias_stub()
        _INV.write_text(
            json.dumps(
                {
                    "counts": {},
                    "findings": [
                        {
                            "classification": "deprecated_runtime_reference",
                            "path": "config/app.env.example",
                            "line": 3,
                            "tokens": ["PI_INSTALLER_HOME"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        res = build_setuphelfer_branding_guard_report(explicit_overwrite=True)
        self.assertEqual(res.get("setuphelfer_branding_guard_check_status"), "blocked")

    def test_opt_pi_installer_blocked(self) -> None:
        self._write_zero_ok()
        self._write_alias_stub()
        _INV.write_text(
            json.dumps(
                {
                    "counts": {},
                    "findings": [
                        {
                            "classification": "active_runtime_identifier",
                            "path": "frontend/vite.config.ts",
                            "line": 10,
                            "tokens": ["/opt/pi-installer"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        res = build_setuphelfer_branding_guard_report(explicit_overwrite=True)
        self.assertEqual(res.get("setuphelfer_branding_guard_check_status"), "blocked")

    def test_de_pi_installer_app_blocked(self) -> None:
        self._write_zero_ok()
        self._write_alias_stub()
        _INV.write_text(
            json.dumps(
                {
                    "counts": {},
                    "findings": [
                        {
                            "classification": "active_runtime_identifier",
                            "path": "frontend/src-tauri/tauri.conf.json",
                            "line": 1,
                            "tokens": ["de.pi-installer.app"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        res = build_setuphelfer_branding_guard_report(explicit_overwrite=True)
        self.assertEqual(res.get("setuphelfer_branding_guard_check_status"), "blocked")

    def test_setuphelfer_terms_allowed(self) -> None:
        self._write_zero_ok()
        self._write_alias_stub()
        _INV.write_text(
            json.dumps(
                {
                    "counts": {},
                    "findings": [
                        {
                            "classification": "active_runtime_identifier",
                            "path": "backend/main.py",
                            "line": 1,
                            "tokens": ["setuphelfer", "SETUPHELFER_API", "de.setuphelfer.app"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        res = build_setuphelfer_branding_guard_report(explicit_overwrite=True)
        self.assertEqual(res.get("setuphelfer_branding_guard_check_status"), "ok")

    def test_alias_warning_review_required(self) -> None:
        self._write_zero_ok()
        self._write_alias_stub()
        _INV.write_text(
            json.dumps(
                {
                    "counts": {},
                    "findings": [
                        {
                            "classification": "deprecated_runtime_reference",
                            "path": "docs/VERIFY_TARGET_SYSTEM.md",
                            "line": 1,
                            "tokens": ["pi-installer"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        res = build_setuphelfer_branding_guard_report(explicit_overwrite=True)
        self.assertEqual(res.get("setuphelfer_branding_guard_check_status"), "review_required")

    def test_check_does_not_write_handoff(self) -> None:
        self._write_zero_ok()
        self._write_alias_stub()
        _INV.write_text(json.dumps({"counts": {}, "findings": []}), encoding="utf-8")
        _OUT.unlink(missing_ok=True)
        res = check_setuphelfer_branding_guard()
        self.assertEqual(res.get("setuphelfer_branding_guard_check_status"), "ok")
        self.assertFalse(res.get("setuphelfer_branding_guard_handoff_written"))
        self.assertFalse(_OUT.exists())

    def test_existing_handoff_requires_overwrite(self) -> None:
        self._write_zero_ok()
        self._write_alias_stub()
        _INV.write_text(json.dumps({"counts": {}, "findings": []}), encoding="utf-8")
        r1 = build_setuphelfer_branding_guard_report(explicit_overwrite=True)
        self.assertEqual(r1.get("setuphelfer_branding_guard_check_status"), "ok")
        r2 = build_setuphelfer_branding_guard_report(explicit_overwrite=False)
        self.assertEqual(r2.get("setuphelfer_branding_guard_check_status"), "blocked")

    def test_script_exists_check_only(self) -> None:
        self.assertTrue(_SCRIPT.is_file())
        body = _SCRIPT.read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", body)
        self.assertRegex(body, r"rg|ripgrep")
        self.assertNotRegex(body, r"(?i)git\s+(tag|push|commit|release)")
        self.assertNotRegex(body, r"curl|wget|systemctl|docker\s+push")

    def test_runner_no_forbidden_syscalls(self) -> None:
        rb = _RUNNER.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", rb)
        self.assertNotIn("os.system", rb)
        self.assertNotIn("Popen", rb)

    def test_route_block_has_no_apply_or_release(self) -> None:
        routes = _ROUTES.read_text(encoding="utf-8")
        start = routes.find("@router.post(\"/setuphelfer-branding-guard-check\")")
        self.assertGreaterEqual(start, 0)
        block = routes[start : start + 1200]
        lowered = block.lower()
        self.assertNotIn("apply", lowered)
        self.assertNotIn("tag", lowered)
        self.assertNotIn("publish", lowered)
        self.assertNotIn("deploy_execute", lowered)

