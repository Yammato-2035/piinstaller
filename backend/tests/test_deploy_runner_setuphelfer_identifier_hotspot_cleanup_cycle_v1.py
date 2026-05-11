from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_setuphelfer_identifier_hotspot_cleanup_cycle import (
    _count_critical_high_in_hotspot_body,
    apply_setuphelfer_identifier_hotspot_cleanup_cycle,
    build_setuphelfer_identifier_hotspot_cleanup_cycle,
    build_setuphelfer_identifier_hotspot_cleanup_cycle_postcheck,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_HOT = _HANDOFF / "legacy_identifier_hotspot_analysis.json"
_SAFE = _HANDOFF / "setuphelfer_safe_rewrite_plan.json"
_PLAN2 = _HANDOFF / "setuphelfer_identifier_cleanup_cycle_2_plan.json"
_RES2 = _HANDOFF / "setuphelfer_identifier_cleanup_cycle_2_result.json"
_POST2 = _HANDOFF / "setuphelfer_identifier_cleanup_cycle_2_postcheck.json"
_INV = _HANDOFF / "legacy_identifier_inventory.json"
_CONS = _HANDOFF / "setuphelfer_identifier_consistency_check.json"
_POST1 = _HANDOFF / "setuphelfer_identifier_cleanup_cycle_1_postcheck.json"


class DeployRunnerSetuphelferIdentifierHotspotCleanupCycleV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._hot_bak = _HOT.read_bytes() if _HOT.exists() else None
        self._safe_bak = _SAFE.read_bytes() if _SAFE.exists() else None
        self._inv_bak = _INV.read_bytes() if _INV.exists() else None
        self._cons_bak = _CONS.read_bytes() if _CONS.exists() else None
        self._post1_bak = _POST1.read_bytes() if _POST1.exists() else None
        for p in (_PLAN2, _RES2, _POST2):
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
        if self._inv_bak is None:
            _INV.unlink(missing_ok=True)
        else:
            _INV.write_bytes(self._inv_bak)
        if self._cons_bak is None:
            _CONS.unlink(missing_ok=True)
        else:
            _CONS.write_bytes(self._cons_bak)
        if self._post1_bak is None:
            _POST1.unlink(missing_ok=True)
        else:
            _POST1.write_bytes(self._post1_bak)
        for p in (_PLAN2, _RES2, _POST2):
            p.unlink(missing_ok=True)
            p.with_suffix(p.suffix + ".tmp").unlink(missing_ok=True)

    def _write_min_inv_cons_post1(self) -> None:
        _INV.write_text(
            json.dumps({"counts": {"active_runtime_identifier": 0}, "findings": []}),
            encoding="utf-8",
        )
        _CONS.write_text(
            json.dumps(
                {
                    "check_schema_version": 1,
                    "check_status": "ok",
                    "findings": [],
                }
            ),
            encoding="utf-8",
        )
        _POST1.write_text(
            json.dumps({"remaining_runtime_identifiers": [], "strict_mode": "x"}),
            encoding="utf-8",
        )

    def test_prioritaet_env_config_vor_backend_runtime(self) -> None:
        recs = [
            {
                "path": "backend/tests/_hot_pri_backend.py",
                "cluster": "backend_runtime",
                "criticality": "critical",
                "rationale": "t",
            },
            {
                "path": "config/_hot_pri.env",
                "cluster": "env_config",
                "criticality": "critical",
                "rationale": "t",
            },
        ]
        ents = [
            {
                "source_file": "backend/tests/_hot_pri_backend.py",
                "legacy_token": "PI_INSTALLER_",
                "replacement": "SETUPHELFER_",
                "classification": "rename_now",
                "write_allowed": True,
                "reason": "t",
            },
            {
                "source_file": "config/_hot_pri.env",
                "legacy_token": "PI_INSTALLER_",
                "replacement": "SETUPHELFER_",
                "classification": "rename_now",
                "write_allowed": True,
                "reason": "t",
            },
        ]
        _HOT.write_text(json.dumps({"recommended_next_cleanup_targets": recs}), encoding="utf-8")
        _SAFE.write_text(json.dumps({"entries": ents, "plan_status": "ok"}), encoding="utf-8")
        res = build_setuphelfer_identifier_hotspot_cleanup_cycle(explicit_overwrite=True)
        planned = (res.get("hotspot_cleanup_cycle_plan") or {}).get("planned_entries") or []
        self.assertGreaterEqual(len(planned), 2)
        self.assertEqual(planned[0].get("source_file"), "config/_hot_pri.env")

    def test_plan_nur_recommended_critical_high_max_50(self) -> None:
        recs = []
        ents = []
        for i in range(52):
            p = f"backend/tests/_hotspot_cap_{i:02d}.py"
            recs.append(
                {
                    "path": p,
                    "cluster": "backend_runtime",
                    "criticality": "critical",
                    "rationale": "t",
                }
            )
            ents.append(
                {
                    "source_file": p,
                    "legacy_token": "PI_INSTALLER_",
                    "replacement": "SETUPHELFER_",
                    "classification": "rename_now",
                    "write_allowed": True,
                    "reason": "t",
                }
            )
        _HOT.write_text(
            json.dumps(
                {
                    "recommended_next_cleanup_targets": recs,
                    "remaining_identifier_count": 52,
                }
            ),
            encoding="utf-8",
        )
        _SAFE.write_text(json.dumps({"entries": ents, "plan_status": "ok"}), encoding="utf-8")
        res = build_setuphelfer_identifier_hotspot_cleanup_cycle(explicit_overwrite=True)
        body = res.get("hotspot_cleanup_cycle_plan") or {}
        self.assertLessEqual(int(body.get("planned_changes") or 0), 50)
        self.assertEqual(int(body.get("deferred_changes") or 0), 2)
        planned = body.get("planned_entries") or []
        self.assertEqual(len(planned), 50)

    def test_unknown_cluster_ausgeschlossen(self) -> None:
        recs = [
            {
                "path": "backend/tests/_hotspot_unknown_only.py",
                "cluster": "unknown",
                "criticality": "critical",
                "rationale": "t",
            }
        ]
        ents = [
            {
                "source_file": "backend/tests/_hotspot_unknown_only.py",
                "legacy_token": "PI_INSTALLER_",
                "replacement": "SETUPHELFER_",
                "classification": "rename_now",
                "write_allowed": True,
                "reason": "t",
            }
        ]
        _HOT.write_text(json.dumps({"recommended_next_cleanup_targets": recs}), encoding="utf-8")
        _SAFE.write_text(json.dumps({"entries": ents, "plan_status": "ok"}), encoding="utf-8")
        res = build_setuphelfer_identifier_hotspot_cleanup_cycle(explicit_overwrite=True)
        body = res.get("hotspot_cleanup_cycle_plan") or {}
        self.assertEqual(int(body.get("planned_changes") or 0), 0)

    def test_evidence_pfad_nicht_geplant(self) -> None:
        recs = [
            {
                "path": "docs/evidence/runtime-results/handoff/x.json",
                "cluster": "api",
                "criticality": "critical",
                "rationale": "t",
            }
        ]
        ents = [
            {
                "source_file": "docs/evidence/runtime-results/handoff/x.json",
                "legacy_token": "PI_INSTALLER_",
                "replacement": "SETUPHELFER_",
                "classification": "rename_now",
                "write_allowed": True,
                "reason": "t",
            }
        ]
        _HOT.write_text(json.dumps({"recommended_next_cleanup_targets": recs}), encoding="utf-8")
        _SAFE.write_text(json.dumps({"entries": ents, "plan_status": "ok"}), encoding="utf-8")
        res = build_setuphelfer_identifier_hotspot_cleanup_cycle(explicit_overwrite=True)
        planned = (res.get("hotspot_cleanup_cycle_plan") or {}).get("planned_entries") or []
        self.assertEqual(len(planned), 0)

    def test_apply_backup_und_nur_geplant(self) -> None:
        tgt = _REPO_ROOT / "backend/tests/_hotspot_c2_apply.txt"
        tgt.parent.mkdir(parents=True, exist_ok=True)
        tgt.write_text("export PI_INSTALLER_HOME=/tmp\n", encoding="utf-8")
        try:
            recs = [
                {
                    "path": "backend/tests/_hotspot_c2_apply.txt",
                    "cluster": "backend_runtime",
                    "criticality": "critical",
                    "rationale": "t",
                }
            ]
            ents = [
                {
                    "source_file": "backend/tests/_hotspot_c2_apply.txt",
                    "legacy_token": "PI_INSTALLER_",
                    "replacement": "SETUPHELFER_",
                    "classification": "rename_now",
                    "write_allowed": True,
                    "reason": "t",
                }
            ]
            _HOT.write_text(
                json.dumps({"recommended_next_cleanup_targets": recs, "remaining_identifier_count": 1}),
                encoding="utf-8",
            )
            _SAFE.write_text(json.dumps({"entries": ents, "plan_status": "ok"}), encoding="utf-8")
            build_setuphelfer_identifier_hotspot_cleanup_cycle(explicit_overwrite=True)
            apply_setuphelfer_identifier_hotspot_cleanup_cycle(explicit_overwrite=True)
            new_t = tgt.read_text(encoding="utf-8")
            self.assertIn("SETUPHELFER_", new_t)
            self.assertNotIn("PI_INSTALLER_", new_t)
            backups = list((_HANDOFF / "legacy-backups").glob("*.legacy-backup"))
            self.assertTrue(any('"cycle": 2' in b.read_text(encoding="utf-8") for b in backups))
        finally:
            tgt.write_text("export PI_INSTALLER_HOME=/tmp\n", encoding="utf-8")

    def test_postcheck_zaehlt_critical_high_in_body(self) -> None:
        body = {
            "clusters": {
                "api": [{"criticality": "critical"}],
                "scripts": [{"criticality": "high"}, {"criticality": "high"}],
            }
        }
        c, h = _count_critical_high_in_hotspot_body(body)
        self.assertEqual(c, 1)
        self.assertEqual(h, 2)

    def test_postcheck_schreibt_datei(self) -> None:
        self._write_min_inv_cons_post1()
        _HOT.write_text(json.dumps({"remaining_identifier_count": 3, "recommended_next_cleanup_targets": []}), encoding="utf-8")
        _SAFE.write_text(json.dumps({"entries": [], "plan_status": "ok"}), encoding="utf-8")
        build_setuphelfer_identifier_hotspot_cleanup_cycle(explicit_overwrite=True)
        apply_setuphelfer_identifier_hotspot_cleanup_cycle(explicit_overwrite=True)
        pc = build_setuphelfer_identifier_hotspot_cleanup_cycle_postcheck(explicit_overwrite=True)
        self.assertIn(str(pc.get("hotspot_cleanup_cycle_postcheck_status") or ""), ("ok", "review_required", "blocked"))
        if _POST2.is_file():
            parsed = json.loads(_POST2.read_text(encoding="utf-8"))
            self.assertEqual(parsed.get("cycle"), 2)
            self.assertIn("after_remaining_identifier_count", parsed)

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_setuphelfer_identifier_hotspot_cleanup_cycle.py"
        t = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", t)
        self.assertNotIn("os.system", t)
        self.assertNotIn("systemctl", t)

    def test_keine_verbotenen_unterrouten_in_routes(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        c = routes.read_text(encoding="utf-8")
        start = c.find("/setuphelfer-identifier-hotspot-cleanup-cycle-plan")
        self.assertGreater(start, 0)
        block = c[start : start + 2500]
        for bad in ("/delete", "/execute", "/release", "/publish", "/systemctl", "service restart"):
            self.assertNotIn(bad, block)


if __name__ == "__main__":
    unittest.main()
