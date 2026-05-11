from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_evidence_final_snapshot import build_manual_runtime_evidence_final_snapshot
from deploy.runner_manual_runtime_final_acceptance_gate import evaluate_manual_runtime_final_acceptance

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_TL = _HANDOFF / "validator_evidence_timeline.json"
_SNAP = _HANDOFF / "validator_evidence_final_snapshot.json"
_ACC = _HANDOFF / "validator_final_acceptance.json"


def _timeline(events: list[dict], event_count: int | None = None) -> dict:
    ec = event_count if event_count is not None else len(events)
    return {
        "timeline_schema_version": 1,
        "event_count": ec,
        "events": events,
        "generated_at": "2026-05-08T12:00:00Z",
    }


class DeployRunnerManualRuntimeFinalAcceptanceGateV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        _TL.unlink(missing_ok=True)
        _SNAP.unlink(missing_ok=True)
        _ACC.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def test_accepted(self) -> None:
        _TL.write_text(
            json.dumps(
                _timeline([{"path": "x", "status": "ok", "timestamp": "t", "sha256": "a", "event_type": "dryrun_report"}])
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)["snapshot_status"],
            "ok",
        )
        out = evaluate_manual_runtime_final_acceptance(explicit_overwrite=True)
        self.assertEqual(out["acceptance_status"], "accepted")
        data = json.loads(_ACC.read_text(encoding="utf-8"))
        self.assertEqual(data["acceptance_status"], "accepted")
        snap = json.loads(_SNAP.read_text(encoding="utf-8"))
        self.assertEqual(data["snapshot_sha256"], snap["snapshot_sha256"])

    def test_review_required(self) -> None:
        _TL.write_text(
            json.dumps(
                _timeline(
                    [
                        {"path": "x", "status": "review_required", "timestamp": "t", "sha256": "a", "event_type": "seal"},
                    ]
                )
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)["snapshot_status"],
            "review_required",
        )
        out = evaluate_manual_runtime_final_acceptance(explicit_overwrite=True)
        self.assertEqual(out["acceptance_status"], "review_required")
        data = json.loads(_ACC.read_text(encoding="utf-8"))
        self.assertEqual(data["acceptance_status"], "review_required")

    def test_blocked_missing_snapshot(self) -> None:
        _TL.write_text(
            json.dumps(_timeline([{"path": "x", "status": "ok", "timestamp": "t", "sha256": "a", "event_type": "x"}])),
            encoding="utf-8",
        )
        out = evaluate_manual_runtime_final_acceptance(explicit_overwrite=True)
        self.assertEqual(out["acceptance_status"], "blocked")
        self.assertIn("ACCEPTANCE_SNAPSHOT_MISSING", out["blocked_reasons"])

    def test_blocked_event_count(self) -> None:
        _TL.write_text(
            json.dumps(_timeline([{"path": "x", "status": "ok", "timestamp": "t", "sha256": "a", "event_type": "x"}])),
            encoding="utf-8",
        )
        build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        snap = json.loads(_SNAP.read_text(encoding="utf-8"))
        snap["event_count"] = 0
        wo = {k: v for k, v in snap.items() if k != "snapshot_sha256"}
        snap["snapshot_sha256"] = hashlib.sha256(
            json.dumps(wo, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        _SNAP.write_text(json.dumps(snap, indent=2, sort_keys=True), encoding="utf-8")
        out = evaluate_manual_runtime_final_acceptance(explicit_overwrite=True)
        self.assertEqual(out["acceptance_status"], "blocked")
        self.assertIn("ACCEPTANCE_EVENT_COUNT_INVALID", out["blocked_reasons"])

    def test_blocked_snapshot_sha256_mismatch(self) -> None:
        _TL.write_text(
            json.dumps(_timeline([{"path": "x", "status": "ok", "timestamp": "t", "sha256": "a", "event_type": "x"}])),
            encoding="utf-8",
        )
        build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        snap = json.loads(_SNAP.read_text(encoding="utf-8"))
        snap["snapshot_sha256"] = "0" * 64
        _SNAP.write_text(json.dumps(snap, indent=2, sort_keys=True), encoding="utf-8")
        out = evaluate_manual_runtime_final_acceptance(explicit_overwrite=True)
        self.assertEqual(out["acceptance_status"], "blocked")
        self.assertIn("ACCEPTANCE_SNAPSHOT_SHA256_MISMATCH", out["blocked_reasons"])

    def test_blocked_timeline_sha256_mismatch(self) -> None:
        _TL.write_text(
            json.dumps(_timeline([{"path": "x", "status": "ok", "timestamp": "t", "sha256": "a", "event_type": "x"}])),
            encoding="utf-8",
        )
        build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        _TL.write_text(
            json.dumps(_timeline([{"path": "y", "status": "ok", "timestamp": "t2", "sha256": "b", "event_type": "x"}])),
            encoding="utf-8",
        )
        out = evaluate_manual_runtime_final_acceptance(explicit_overwrite=True)
        self.assertEqual(out["acceptance_status"], "blocked")
        self.assertIn("ACCEPTANCE_TIMELINE_SHA256_MISMATCH", out["blocked_reasons"])

    def test_snapshot_sha256_chain(self) -> None:
        _TL.write_text(
            json.dumps(_timeline([{"path": "x", "status": "ok", "timestamp": "t", "sha256": "a", "event_type": "x"}])),
            encoding="utf-8",
        )
        build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        snap = json.loads(_SNAP.read_text(encoding="utf-8"))
        wo = {k: v for k, v in snap.items() if k != "snapshot_sha256"}
        exp = hashlib.sha256(json.dumps(wo, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        self.assertEqual(snap["snapshot_sha256"], exp)
        evaluate_manual_runtime_final_acceptance(explicit_overwrite=True)
        self.assertEqual(exp, json.loads(_ACC.read_text(encoding="utf-8"))["snapshot_sha256"])

    def test_traversal_constant(self) -> None:
        self.assertNotIn(
            "..",
            Path("docs/evidence/runtime-results/handoff/validator_final_acceptance.json").parts,
        )

    def test_symlink_snapshot_blocked(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write("{}")
            ext = tmp.name
        self.addCleanup(lambda: os.path.exists(ext) and os.unlink(ext))
        _TL.write_text(
            json.dumps(_timeline([{"path": "x", "status": "ok", "timestamp": "t", "sha256": "a", "event_type": "x"}])),
            encoding="utf-8",
        )
        build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        if _SNAP.exists():
            _SNAP.unlink()
        _SNAP.symlink_to(ext)
        out = evaluate_manual_runtime_final_acceptance(explicit_overwrite=True)
        self.assertEqual(out["acceptance_status"], "blocked")

    def test_overwrite_blocked(self) -> None:
        _TL.write_text(
            json.dumps(_timeline([{"path": "x", "status": "ok", "timestamp": "t", "sha256": "a", "event_type": "x"}])),
            encoding="utf-8",
        )
        build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        evaluate_manual_runtime_final_acceptance(explicit_overwrite=True)
        second = evaluate_manual_runtime_final_acceptance(explicit_overwrite=False)
        self.assertEqual(second["acceptance_status"], "blocked")
        self.assertIn("ACCEPTANCE_EXISTS_NO_OVERWRITE", second["blocked_reasons"])

    def test_atomic_no_tmp(self) -> None:
        _TL.write_text(
            json.dumps(_timeline([{"path": "x", "status": "ok", "timestamp": "t", "sha256": "a", "event_type": "x"}])),
            encoding="utf-8",
        )
        build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        evaluate_manual_runtime_final_acceptance(explicit_overwrite=True)
        self.assertFalse(any(p.name.endswith(".tmp") for p in _HANDOFF.iterdir()))

    def test_no_forbidden_systemcalls(self) -> None:
        src = (
            _REPO_ROOT / "backend/deploy/runner_manual_runtime_final_acceptance_gate.py"
        ).read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/final-acceptance", routes)
        for forbidden in [
            "/runner/manual-runtime/final-acceptance/execute",
            "/runner/manual-runtime/final-acceptance/apply",
            "/runner/manual-runtime/final-acceptance/install",
            "/runner/manual-runtime/final-acceptance/write",
            "/runner/manual-runtime/final-acceptance/delete",
            "/runner/manual-runtime/final-acceptance/release",
        ]:
            self.assertNotIn(forbidden, routes)


if __name__ == "__main__":
    unittest.main()
