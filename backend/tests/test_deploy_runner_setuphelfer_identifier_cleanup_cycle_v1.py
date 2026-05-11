from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_setuphelfer_identifier_cleanup_cycle import (
    apply_setuphelfer_identifier_cleanup_cycle,
    build_setuphelfer_identifier_cleanup_cycle,
    build_setuphelfer_identifier_cleanup_cycle_postcheck,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_SAFE = _HANDOFF / "setuphelfer_safe_rewrite_plan.json"
_CYCLE_PLAN = _HANDOFF / "setuphelfer_identifier_cleanup_cycle_1_plan.json"
_CYCLE_RESULT = _HANDOFF / "setuphelfer_identifier_cleanup_cycle_1_result.json"
_CYCLE_POST = _HANDOFF / "setuphelfer_identifier_cleanup_cycle_1_postcheck.json"


class DeployRunnerSetuphelferIdentifierCleanupCycleV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._safe_bak = _SAFE.read_text(encoding="utf-8") if _SAFE.exists() else None
        self._plan_bak = _CYCLE_PLAN.read_text(encoding="utf-8") if _CYCLE_PLAN.exists() else None
        self._res_bak = _CYCLE_RESULT.read_text(encoding="utf-8") if _CYCLE_RESULT.exists() else None
        self._post_bak = _CYCLE_POST.read_text(encoding="utf-8") if _CYCLE_POST.exists() else None
        for p in (_CYCLE_PLAN, _CYCLE_RESULT, _CYCLE_POST):
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._safe_bak is None:
            _SAFE.unlink(missing_ok=True)
        else:
            _SAFE.write_text(self._safe_bak, encoding="utf-8")
        if self._plan_bak is None:
            _CYCLE_PLAN.unlink(missing_ok=True)
        else:
            _CYCLE_PLAN.write_text(self._plan_bak, encoding="utf-8")
        if self._res_bak is None:
            _CYCLE_RESULT.unlink(missing_ok=True)
        else:
            _CYCLE_RESULT.write_text(self._res_bak, encoding="utf-8")
        if self._post_bak is None:
            _CYCLE_POST.unlink(missing_ok=True)
        else:
            _CYCLE_POST.write_text(self._post_bak, encoding="utf-8")

    def test_cycle_plan_nur_erlaubter_scope(self) -> None:
        entries = [
            {
                "source_file": "backend/tests/_cycle_scope_ok.txt",
                "legacy_token": "PI_INSTALLER_",
                "replacement": "SETUPHELFER_",
                "write_allowed": True,
                "classification": "rename_now",
                "reason": "t",
            },
            {
                "source_file": "docs/evidence/runtime-results/handoff/x.json",
                "legacy_token": "pi-installer",
                "replacement": "setuphelfer",
                "write_allowed": True,
                "classification": "rename_now",
                "reason": "t",
            },
        ]
        _SAFE.write_text(json.dumps({"entries": entries, "plan_status": "ok"}, indent=2), encoding="utf-8")
        res = build_setuphelfer_identifier_cleanup_cycle(explicit_overwrite=True)
        planned = (res.get("cycle_plan") or {}).get("planned_entries") or []
        paths = {p.get("source_file") for p in planned}
        self.assertIn("backend/tests/_cycle_scope_ok.txt", paths)
        self.assertNotIn("docs/evidence/runtime-results/handoff/x.json", paths)

    def test_max_100_und_deferred(self) -> None:
        entries = []
        for i in range(101):
            entries.append(
                {
                    "source_file": f"backend/tests/_cycle_bulk_{i}.txt",
                    "legacy_token": "PI_INSTALLER_",
                    "replacement": "SETUPHELFER_",
                    "write_allowed": True,
                    "classification": "rename_now",
                    "reason": "t",
                }
            )
        _SAFE.write_text(json.dumps({"entries": entries, "plan_status": "ok"}, indent=2), encoding="utf-8")
        res = build_setuphelfer_identifier_cleanup_cycle(explicit_overwrite=True)
        body = res.get("cycle_plan") or {}
        self.assertLessEqual(len(body.get("planned_entries") or []), 100)
        self.assertEqual(len(body.get("deferred_entries") or []), 1)
        self.assertEqual(body.get("planned_changes"), 100)
        self.assertEqual(body.get("deferred_changes"), 1)

    def test_apply_backup_und_nur_geplant(self) -> None:
        fx = _REPO_ROOT / "backend/tests/_cycle_apply_target.txt"
        fx.parent.mkdir(parents=True, exist_ok=True)
        fx.write_text("PI_INSTALLER_X=1\n", encoding="utf-8")
        try:
            _CYCLE_PLAN.write_text(
                json.dumps(
                    {
                        "planned_entries": [
                            {
                                "source_file": "backend/tests/_cycle_apply_target.txt",
                                "legacy_token": "PI_INSTALLER_",
                                "replacement": "SETUPHELFER_",
                                "write_allowed": True,
                                "classification": "rename_now",
                                "reason": "t",
                            }
                        ]
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            res = apply_setuphelfer_identifier_cleanup_cycle(explicit_overwrite=True)
            self.assertIn(res.get("cycle_apply_status"), ("ok", "review_required"))
            self.assertIn("SETUPHELFER_", fx.read_text(encoding="utf-8"))
            backups = list((_HANDOFF / "legacy-backups").glob("*.legacy-backup"))
            self.assertTrue(backups)
            self.assertTrue(any("PI_INSTALLER_" in p.read_text(encoding="utf-8") for p in backups))
        finally:
            fx.write_text("PI_INSTALLER_X=1\n", encoding="utf-8")

    def test_binaerdatei_blockiert(self) -> None:
        binf = _REPO_ROOT / "backend/tests/_cycle_binary.bin"
        binf.write_bytes(b"\x00\x00\x01\xff")
        try:
            _CYCLE_PLAN.write_text(
                json.dumps(
                    {
                        "planned_entries": [
                            {
                                "source_file": "backend/tests/_cycle_binary.bin",
                                "legacy_token": "pi-installer",
                                "replacement": "setuphelfer",
                                "write_allowed": True,
                                "classification": "rename_now",
                                "reason": "t",
                            }
                        ]
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            res = apply_setuphelfer_identifier_cleanup_cycle(explicit_overwrite=True)
            self.assertEqual(res.get("cycle_apply_status"), "review_required")
            self.assertTrue(any("CLEANUP_CYCLE_SKIP_BINARY" in str(x) for x in (res.get("warnings") or [])))
        finally:
            binf.unlink(missing_ok=True)

    def test_postcheck_struktur(self) -> None:
        _CYCLE_RESULT.write_text(
            json.dumps(
                {
                    "cycle_apply": {
                        "before_active_runtime_identifier_count": 3,
                        "apply_status": "ok",
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        res = build_setuphelfer_identifier_cleanup_cycle_postcheck(explicit_overwrite=True)
        body = res.get("cycle_postcheck") or {}
        self.assertIn("after_active_runtime_identifier_count", body)
        self.assertIn("remaining_runtime_identifiers", body)
        self.assertIn(body.get("consistency_status") or "", ("ok", "blocked", "review_required"))
        self.assertIsInstance(body.get("next_cycle_required"), bool)

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_setuphelfer_identifier_cleanup_cycle.py"
        t = src.read_text(encoding="utf-8")
        for bad in ("subprocess", "os.system", "systemctl", "chmod", "chown"):
            self.assertNotIn(bad, t)

    def test_keine_verbotenen_unterrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        c = routes.read_text(encoding="utf-8")
        for marker, bad in (
            ("/setuphelfer-identifier-cleanup-cycle-plan", "/delete"),
            ("/setuphelfer-identifier-cleanup-cycle-apply", "/execute"),
            ("/setuphelfer-identifier-cleanup-cycle-postcheck", "/release"),
        ):
            start = c.find(marker)
            self.assertGreater(start, 0)
            block = c[start : start + 900]
            self.assertNotIn(bad, block)


if __name__ == "__main__":
    unittest.main()
