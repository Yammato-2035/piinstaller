from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_legacy_runtime_compatibility_validation import (
    analyze_legacy_runtime_coexistence,
    build_legacy_runtime_compatibility_inventory,
    build_legacy_upgrade_path_matrix,
    build_safe_legacy_runtime_migration_recommendations,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_INV = _HANDOFF / "legacy_identifier_inventory.json"
_ZERO = _HANDOFF / "runtime_identifier_zero_state_verification.json"
_BRAND = _HANDOFF / "setuphelfer_branding_guard_check.json"
_ALIAS = _HANDOFF / "compatibility_aliases.json"
_OUT_INV = _HANDOFF / "legacy_runtime_compatibility_inventory.json"
_OUT_COEX = _HANDOFF / "legacy_runtime_coexistence_analysis.json"
_OUT_REC = _HANDOFF / "legacy_runtime_safe_migration_recommendations.json"
_OUT_MATRIX = _HANDOFF / "legacy_upgrade_path_matrix.json"
_RUNNER = _REPO_ROOT / "backend/deploy/runner_legacy_runtime_compatibility_validation.py"
_ROUTES = _REPO_ROOT / "backend/deploy/routes.py"


class DeployRunnerLegacyRuntimeCompatibilityValidationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._inv_bak = _INV.read_bytes() if _INV.exists() else None
        self._zero_bak = _ZERO.read_bytes() if _ZERO.exists() else None
        self._brand_bak = _BRAND.read_bytes() if _BRAND.exists() else None
        self._alias_bak = _ALIAS.read_bytes() if _ALIAS.exists() else None
        for p in (_OUT_INV, _OUT_COEX, _OUT_REC, _OUT_MATRIX):
            p.unlink(missing_ok=True)
            p.with_name(p.name + ".tmp").unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in (
            (_INV, self._inv_bak),
            (_ZERO, self._zero_bak),
            (_BRAND, self._brand_bak),
            (_ALIAS, self._alias_bak),
        ):
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)
        for p in (_OUT_INV, _OUT_COEX, _OUT_REC, _OUT_MATRIX):
            p.unlink(missing_ok=True)

    def _write_gates_ok(self) -> None:
        _ZERO.write_text(json.dumps({"zero_state_status": "ok"}), encoding="utf-8")
        _BRAND.write_text(json.dumps({"branding_guard_status": "ok"}), encoding="utf-8")
        _ALIAS.write_text(json.dumps({"aliases": []}), encoding="utf-8")

    def test_appdata_detected(self) -> None:
        self._write_gates_ok()
        _INV.write_text(
            json.dumps(
                {
                    "counts": {},
                    "findings": [
                        {
                            "classification": "deprecated_runtime_reference",
                            "path": "home/user/.local/share/de.pi-installer.app/config.json",
                            "line": 1,
                            "tokens": ["de.pi-installer.app"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        res = build_legacy_runtime_compatibility_inventory(explicit_overwrite=True)
        self.assertEqual(res.get("legacy_runtime_compatibility_inventory_status"), "review_required")
        body = json.loads(_OUT_INV.read_text(encoding="utf-8"))
        self.assertGreater(len(body.get("categories", {}).get("legacy_appdata") or []), 0)

    def test_desktop_files_detected(self) -> None:
        self._write_gates_ok()
        _INV.write_text(
            json.dumps(
                {
                    "counts": {},
                    "findings": [
                        {
                            "classification": "active_runtime_identifier",
                            "path": "usr/share/applications/pi-installer.desktop",
                            "line": 2,
                            "tokens": ["pi-installer"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        res = build_legacy_runtime_compatibility_inventory(explicit_overwrite=True)
        self.assertEqual(res.get("legacy_runtime_compatibility_inventory_status"), "review_required")
        body = json.loads(_OUT_INV.read_text(encoding="utf-8"))
        self.assertGreater(len(body.get("categories", {}).get("desktop_files") or []), 0)

    def test_duplicate_runtime_blocked(self) -> None:
        self._write_gates_ok()
        _INV.write_text(
            json.dumps(
                {
                    "counts": {},
                    "findings": [
                        {
                            "classification": "active_runtime_identifier",
                            "path": "etc/systemd/system/pi-installer.service",
                            "line": 1,
                            "tokens": ["pi-installer.service"],
                        },
                        {
                            "classification": "active_runtime_identifier",
                            "path": "etc/systemd/system/setuphelfer.service",
                            "line": 1,
                            "tokens": ["setuphelfer.service"],
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        build_legacy_runtime_compatibility_inventory(explicit_overwrite=True)
        res = analyze_legacy_runtime_coexistence(explicit_overwrite=True)
        self.assertEqual(res.get("legacy_runtime_coexistence_analysis_status"), "blocked")
        co = json.loads(_OUT_COEX.read_text(encoding="utf-8"))
        types = [c.get("type") for c in co.get("conflicts") or []]
        self.assertIn("duplicate_runtime", types)

    def test_old_env_review_required_not_blocked(self) -> None:
        self._write_gates_ok()
        _INV.write_text(
            json.dumps(
                {
                    "counts": {},
                    "findings": [
                        {
                            "classification": "deprecated_runtime_reference",
                            "path": "config/production.env",
                            "line": 4,
                            "tokens": ["PI_INSTALLER_HOME"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        build_legacy_runtime_compatibility_inventory(explicit_overwrite=True)
        res = analyze_legacy_runtime_coexistence(explicit_overwrite=True)
        self.assertEqual(res.get("legacy_runtime_coexistence_analysis_status"), "review_required")
        self.assertNotEqual(res.get("legacy_runtime_coexistence_analysis_status"), "blocked")

    def test_migration_recommendations_and_matrix_chain(self) -> None:
        self._write_gates_ok()
        _INV.write_text(
            json.dumps(
                {
                    "counts": {},
                    "findings": [
                        {
                            "path": "config/app.env",
                            "line": 1,
                            "tokens": ["PI_INSTALLER_HOME"],
                            "classification": "deprecated_runtime_reference",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            build_legacy_runtime_compatibility_inventory(explicit_overwrite=True).get(
                "legacy_runtime_compatibility_inventory_status"
            ),
            "review_required",
        )
        analyze_legacy_runtime_coexistence(explicit_overwrite=True)
        rec_res = build_safe_legacy_runtime_migration_recommendations(explicit_overwrite=True)
        self.assertEqual(rec_res.get("legacy_runtime_safe_migration_recommendations_status"), "review_required")
        rec = json.loads(_OUT_REC.read_text(encoding="utf-8"))
        ids = [r.get("id") for r in rec.get("recommendations") or []]
        self.assertIn("env_readonly_archive", ids)
        self.assertIn("disclaimer", rec)
        mat_res = build_legacy_upgrade_path_matrix(explicit_overwrite=True)
        self.assertIn(mat_res.get("legacy_upgrade_path_matrix_status"), ("ok", "review_required"))
        matrix = json.loads(_OUT_MATRIX.read_text(encoding="utf-8"))
        self.assertEqual(len(matrix.get("upgrade_paths") or []), 6)
        keys = {p.get("key") for p in matrix.get("upgrade_paths") or []}
        self.assertIn("pi_installer_to_setuphelfer_clean", keys)
        self.assertIn("rollback_legacy", keys)

    def test_inventory_blocked_without_legacy_inventory(self) -> None:
        self._write_gates_ok()
        _INV.unlink(missing_ok=True)
        res = build_legacy_runtime_compatibility_inventory(explicit_overwrite=True)
        self.assertEqual(res.get("legacy_runtime_compatibility_inventory_status"), "blocked")

    def test_runner_no_subprocess(self) -> None:
        src = _RUNNER.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)
        self.assertNotIn("os.system", src)
        self.assertNotIn("Popen", src)

    def test_routes_no_forbidden_verbs(self) -> None:
        routes = _ROUTES.read_text(encoding="utf-8")
        markers = (
            "@router.post(\"/legacy-runtime-compatibility-inventory\")",
            "@router.post(\"/legacy-runtime-coexistence-analysis\")",
            "@router.post(\"/legacy-runtime-safe-migration-recommendations\")",
            "@router.post(\"/legacy-upgrade-path-matrix\")",
        )
        banned_subpaths = ("/migrate", "/delete", "/restart", "/release", "/publish")
        for m in markers:
            start = routes.find(m)
            self.assertGreaterEqual(start, 0, msg=m)
            block = routes[start : start + 900].lower()
            for b in banned_subpaths:
                self.assertNotIn(b, block, msg=f"{m} contains {b}")

