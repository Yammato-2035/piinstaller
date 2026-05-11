from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_evidence_timeline import build_manual_runtime_evidence_timeline

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_TL = _HANDOFF / "validator_evidence_timeline.json"


class DeployRunnerManualRuntimeEvidenceTimelineV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in _HANDOFF.glob("*.seal.json"):
            p.unlink(missing_ok=True)
        for name in (
            "validator_dryrun_report.json",
            "validator_seal_index.json",
            "validator_seal_consistency_audit.json",
            _TL.name,
        ):
            fp = _HANDOFF / name
            fp.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_dryrun(self) -> None:
        (_HANDOFF / "validator_dryrun_report.json").write_text(
            json.dumps(
                {
                    "dryrun_status": "ok",
                    "created_at": "2026-05-10T12:00:00Z",
                    "dryrun_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )

    def _write_index(self) -> None:
        (_HANDOFF / "validator_seal_index.json").write_text(
            json.dumps(
                {
                    "generated_at": "2026-05-08T12:00:00Z",
                    "seals": [],
                }
            ),
            encoding="utf-8",
        )

    def _write_audit(self, invalid: int = 0) -> None:
        (_HANDOFF / "validator_seal_consistency_audit.json").write_text(
            json.dumps(
                {
                    "generated_at": "2026-05-11T12:00:00Z",
                    "invalid_entries": invalid,
                    "audit_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )

    def test_valid_timeline_ok(self) -> None:
        self._write_dryrun()
        self._write_index()
        self._write_audit(0)
        out = build_manual_runtime_evidence_timeline(explicit_overwrite=True)
        self.assertEqual(out["timeline_status"], "ok")
        self.assertGreaterEqual(out["event_count"], 3)
        self.assertTrue(_TL.is_file())

    def test_audit_invalid_entries_review_required(self) -> None:
        self._write_dryrun()
        self._write_index()
        self._write_audit(2)
        out = build_manual_runtime_evidence_timeline(explicit_overwrite=True)
        self.assertEqual(out["timeline_status"], "review_required")

    def test_no_valid_events_blocked(self) -> None:
        out = build_manual_runtime_evidence_timeline(explicit_overwrite=True)
        self.assertEqual(out["timeline_status"], "blocked")
        self.assertIn("TIMELINE_NO_VALID_EVENTS", out["blocked_reasons"])

    def test_sha256_matches_file(self) -> None:
        self._write_dryrun()
        self._write_index()
        self._write_audit(0)
        build_manual_runtime_evidence_timeline(explicit_overwrite=True)
        data = json.loads(_TL.read_text(encoding="utf-8"))
        for ev in data["events"]:
            p = _REPO_ROOT / ev["path"]
            exp = hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(ev["sha256"], exp)

    def test_chronological_order(self) -> None:
        self._write_index()
        self._write_dryrun()
        seal = _HANDOFF / "t.seal.json"
        seal.write_text(
            json.dumps(
                {
                    "sealed_at": "2026-05-09T12:00:00Z",
                    "validator_status": "ok",
                }
            ),
            encoding="utf-8",
        )
        self._write_audit(0)
        build_manual_runtime_evidence_timeline(explicit_overwrite=True)
        data = json.loads(_TL.read_text(encoding="utf-8"))
        ts = [e["timestamp"] for e in data["events"]]
        self.assertEqual(ts, sorted(ts))

    def test_traversal_constant(self) -> None:
        self.assertNotIn("..", Path("docs/evidence/runtime-results/handoff/validator_evidence_timeline.json").parts)

    def test_symlink_input_skipped(self) -> None:
        self._write_index()
        self._write_audit(0)
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write('{"dryrun_status":"ok","created_at":"2026-05-10T12:00:00Z"}')
            ext = tmp.name
        self.addCleanup(lambda: os.path.exists(ext) and os.unlink(ext))
        link = _HANDOFF / "validator_dryrun_report.json"
        link.symlink_to(ext)
        out = build_manual_runtime_evidence_timeline(explicit_overwrite=True)
        self.assertGreaterEqual(out["event_count"], 2)

    def test_existing_timeline_blocks(self) -> None:
        self._write_dryrun()
        self._write_index()
        self._write_audit(0)
        first = build_manual_runtime_evidence_timeline(explicit_overwrite=True)
        self.assertEqual(first["timeline_status"], "ok")
        second = build_manual_runtime_evidence_timeline(explicit_overwrite=False)
        self.assertEqual(second["timeline_status"], "blocked")
        self.assertIn("TIMELINE_EXISTS_NO_OVERWRITE", second["blocked_reasons"])

    def test_explicit_overwrite(self) -> None:
        self._write_dryrun()
        self._write_index()
        self._write_audit(0)
        build_manual_runtime_evidence_timeline(explicit_overwrite=True)
        out = build_manual_runtime_evidence_timeline(explicit_overwrite=True)
        self.assertEqual(out["timeline_status"], "ok")

    def test_atomic_no_tmp(self) -> None:
        self._write_dryrun()
        self._write_index()
        self._write_audit(0)
        build_manual_runtime_evidence_timeline(explicit_overwrite=True)
        self.assertFalse(any(p.name.endswith(".tmp") for p in _HANDOFF.iterdir()))

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_evidence_timeline.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/evidence-timeline", routes)
        for forbidden in [
            "/runner/manual-runtime/evidence-timeline/execute",
            "/runner/manual-runtime/evidence-timeline/apply",
            "/runner/manual-runtime/evidence-timeline/install",
            "/runner/manual-runtime/evidence-timeline/write",
            "/runner/manual-runtime/evidence-timeline/delete",
            "/runner/manual-runtime/evidence-timeline/release",
        ]:
            self.assertNotIn(forbidden, routes)


if __name__ == "__main__":
    unittest.main()
