from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_legacy_identifier_hotspot_analysis import (
    _cleanup_priority_rank,
    _cluster,
    _criticality,
    build_legacy_identifier_hotspot_analysis,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_INV = _HANDOFF / "legacy_identifier_inventory.json"
_POST = _HANDOFF / "setuphelfer_identifier_cleanup_cycle_1_postcheck.json"
_CONS = _HANDOFF / "setuphelfer_identifier_consistency_check.json"
_HOT = _HANDOFF / "legacy_identifier_hotspot_analysis.json"


class DeployRunnerLegacyIdentifierHotspotAnalysisV1Tests(unittest.TestCase):
    def test_cluster_api_vor_backend_runtime(self) -> None:
        self.assertEqual(_cluster("backend/deploy/routes.py", [], ""), "api")

    def test_cluster_env_config(self) -> None:
        self.assertEqual(_cluster("config/setuphelfer.env", [], ""), "env_config")

    def test_cluster_tauri(self) -> None:
        self.assertEqual(_cluster("frontend/src-tauri/tauri.conf.json", [], ""), "tauri")

    def test_cluster_unknown(self) -> None:
        self.assertEqual(_cluster("orphan/custom/file.md", [], ""), "unknown")

    def test_cluster_migration_alias_pfad(self) -> None:
        self.assertEqual(
            _cluster("docs/evidence/runtime-results/handoff/compatibility_aliases.json", [], ""),
            "migration_alias",
        )

    def test_criticality_env_tokens(self) -> None:
        self.assertEqual(
            _criticality("config/x.env", ["PI_INSTALLER_HOME"], "PI_INSTALLER_HOME=/x", "env_config"),
            "critical",
        )

    def test_criticality_comment_low(self) -> None:
        self.assertEqual(
            _criticality("docs/x.md", ["pi-installer"], "# pi-installer legacy note", "unknown"),
            "low",
        )

    def test_cleanup_priority_env_vor_tests(self) -> None:
        a = {"path": "config/a.env", "cluster": "env_config", "criticality": "critical", "line_preview": ""}
        b = {"path": "backend/tests/t.py", "cluster": "tests", "criticality": "critical", "line_preview": ""}
        ordered = sorted([b, a], key=_cleanup_priority_rank)
        self.assertEqual(ordered[0]["path"], "config/a.env")
        self.assertEqual(ordered[1]["path"], "backend/tests/t.py")

    def test_cleanup_priority_kommentar_zuletzt(self) -> None:
        code = {"path": "scripts/start.sh", "cluster": "scripts", "criticality": "high", "line_preview": "x=1"}
        comment = {"path": "docs/x.md", "cluster": "unknown", "criticality": "low", "line_preview": "# old pi-installer"}
        ordered = sorted([comment, code], key=_cleanup_priority_rank)
        self.assertEqual(ordered[-1]["path"], "docs/x.md")

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_legacy_identifier_hotspot_analysis.py"
        t = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", t)
        self.assertNotIn("os.system", t)
        self.assertNotIn("systemctl", t)

    def test_keine_release_publish_tag_execute_delete_routen(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        c = routes.read_text(encoding="utf-8")
        start = c.find("/legacy-identifier-hotspot-analysis")
        self.assertGreater(start, 0)
        block = c[start : start + 1200]
        for bad in ("/release", "/publish", "/tag", "/execute", "/delete"):
            self.assertNotIn(bad, block)


class DeployRunnerLegacyIdentifierHotspotAnalysisHandoffV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._inv_bak = _INV.read_bytes() if _INV.exists() else None
        self._post_bak = _POST.read_bytes() if _POST.exists() else None
        self._cons_bak = _CONS.read_bytes() if _CONS.exists() else None
        self._hot_bak = _HOT.read_bytes() if _HOT.exists() else None
        _HOT.unlink(missing_ok=True)
        (_HANDOFF / "legacy_identifier_hotspot_analysis.json.tmp").unlink(missing_ok=True)
        _POST.unlink(missing_ok=True)
        _CONS.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._inv_bak is None:
            _INV.unlink(missing_ok=True)
        else:
            _INV.write_bytes(self._inv_bak)
        if self._post_bak is None:
            _POST.unlink(missing_ok=True)
        else:
            _POST.write_bytes(self._post_bak)
        if self._cons_bak is None:
            _CONS.unlink(missing_ok=True)
        else:
            _CONS.write_bytes(self._cons_bak)
        if self._hot_bak is None:
            _HOT.unlink(missing_ok=True)
        else:
            _HOT.write_bytes(self._hot_bak)
        (_HANDOFF / "legacy_identifier_hotspot_analysis.json.tmp").unlink(missing_ok=True)

    def test_unknown_cluster_review_required(self) -> None:
        body = {
            "findings": [
                {
                    "classification": "active_runtime_identifier",
                    "path": "orphan/legacy_only/readme.md",
                    "line": 1,
                    "tokens": ["pi-installer"],
                }
            ]
        }
        _INV.write_text(json.dumps(body), encoding="utf-8")
        res = build_legacy_identifier_hotspot_analysis(explicit_overwrite=True)
        self.assertEqual(res.get("analysis_status"), "review_required")
        parsed = json.loads(_HOT.read_text(encoding="utf-8"))
        self.assertEqual(parsed.get("analysis_status"), "review_required")
        clusters = parsed.get("clusters") or {}
        self.assertTrue((clusters.get("unknown") or []))

    def test_zero_remaining_ok(self) -> None:
        _INV.write_text(json.dumps({"findings": []}), encoding="utf-8")
        res = build_legacy_identifier_hotspot_analysis(explicit_overwrite=True)
        self.assertEqual(res.get("analysis_status"), "ok")
        parsed = json.loads(_HOT.read_text(encoding="utf-8"))
        self.assertEqual(parsed.get("remaining_identifier_count"), 0)

    def test_empfehlungen_sortierung_env_vor_tests(self) -> None:
        body = {
            "findings": [
                {
                    "classification": "active_runtime_identifier",
                    "path": "config/z.env",
                    "line": 1,
                    "tokens": ["PI_INSTALLER_X"],
                },
                {
                    "classification": "active_runtime_identifier",
                    "path": "backend/tests/_hotspot_order.py",
                    "line": 1,
                    "tokens": ["pi-installer"],
                },
            ]
        }
        _INV.write_text(json.dumps(body), encoding="utf-8")
        build_legacy_identifier_hotspot_analysis(explicit_overwrite=True)
        parsed = json.loads(_HOT.read_text(encoding="utf-8"))
        rec = parsed.get("recommended_next_cleanup_targets") or []
        paths = [r.get("path") for r in rec]
        self.assertLess(paths.index("config/z.env"), paths.index("backend/tests/_hotspot_order.py"))

    def test_exists_no_overwrite_blocked(self) -> None:
        _INV.write_text(json.dumps({"findings": []}), encoding="utf-8")
        build_legacy_identifier_hotspot_analysis(explicit_overwrite=True)
        res = build_legacy_identifier_hotspot_analysis(explicit_overwrite=False)
        self.assertEqual(res.get("analysis_status"), "blocked")


if __name__ == "__main__":
    unittest.main()
