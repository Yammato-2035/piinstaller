from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_evidence_final_snapshot import build_manual_runtime_evidence_final_snapshot

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_TL = _HANDOFF / "validator_evidence_timeline.json"
_SNAP = _HANDOFF / "validator_evidence_final_snapshot.json"


def _timeline(events: list[dict], event_count: int | None = None) -> dict:
    ec = event_count if event_count is not None else len(events)
    return {
        "timeline_schema_version": 1,
        "event_count": ec,
        "events": events,
        "generated_at": "2026-05-08T12:00:00Z",
    }


class DeployRunnerManualRuntimeEvidenceFinalSnapshotV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        _TL.unlink(missing_ok=True)
        _SNAP.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def test_ok(self) -> None:
        _TL.write_text(
            json.dumps(
                _timeline([{"path": "x", "status": "ok", "timestamp": "t", "sha256": "a", "event_type": "dryrun_report"}])
            ),
            encoding="utf-8",
        )
        out = build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        self.assertEqual(out["snapshot_status"], "ok")
        self.assertTrue(_SNAP.is_file())
        data = json.loads(_SNAP.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "ok")

    def test_review_required(self) -> None:
        _TL.write_text(
            json.dumps(
                _timeline(
                    [
                        {"path": "x", "status": "ok", "timestamp": "t", "sha256": "a", "event_type": "seal"},
                        {"path": "y", "status": "review_required", "timestamp": "t2", "sha256": "b", "event_type": "seal"},
                    ]
                )
            ),
            encoding="utf-8",
        )
        out = build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        self.assertEqual(out["snapshot_status"], "review_required")
        data = json.loads(_SNAP.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "review_required")

    def test_blocked_no_events(self) -> None:
        _TL.write_text(json.dumps(_timeline([], event_count=0)), encoding="utf-8")
        out = build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        self.assertEqual(out["snapshot_status"], "blocked")
        self.assertIn("SNAPSHOT_TIMELINE_NO_EVENTS", out["blocked_reasons"])

    def test_timeline_sha256(self) -> None:
        raw = json.dumps(_timeline([{"path": "p", "status": "ok", "timestamp": "t", "sha256": "h", "event_type": "x"}])).encode(
            "utf-8"
        )
        _TL.write_bytes(raw)
        build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        data = json.loads(_SNAP.read_text(encoding="utf-8"))
        self.assertEqual(data["timeline_sha256"], hashlib.sha256(raw).hexdigest())

    def test_snapshot_sha256_field(self) -> None:
        _TL.write_text(
            json.dumps(_timeline([{"path": "p", "status": "ok", "timestamp": "t", "sha256": "h", "event_type": "x"}])),
            encoding="utf-8",
        )
        build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        data = json.loads(_SNAP.read_text(encoding="utf-8"))
        wo = {k: v for k, v in data.items() if k != "snapshot_sha256"}
        exp = hashlib.sha256(json.dumps(wo, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        self.assertEqual(data["snapshot_sha256"], exp)

    def test_traversal_constant(self) -> None:
        self.assertNotIn("..", Path("docs/evidence/runtime-results/handoff/validator_evidence_final_snapshot.json").parts)

    def test_symlink_timeline_blocked(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write(json.dumps(_timeline([{"path": "p", "status": "ok", "timestamp": "t", "sha256": "h", "event_type": "x"}])))
            ext = tmp.name
        self.addCleanup(lambda: os.path.exists(ext) and os.unlink(ext))
        if _TL.exists():
            _TL.unlink()
        _TL.symlink_to(ext)
        out = build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        self.assertEqual(out["snapshot_status"], "blocked")

    def test_overwrite_blocked(self) -> None:
        _TL.write_text(
            json.dumps(_timeline([{"path": "p", "status": "ok", "timestamp": "t", "sha256": "h", "event_type": "x"}])),
            encoding="utf-8",
        )
        build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        second = build_manual_runtime_evidence_final_snapshot(explicit_overwrite=False)
        self.assertEqual(second["snapshot_status"], "blocked")
        self.assertIn("SNAPSHOT_EXISTS_NO_OVERWRITE", second["blocked_reasons"])

    def test_atomic_no_tmp(self) -> None:
        _TL.write_text(
            json.dumps(_timeline([{"path": "p", "status": "ok", "timestamp": "t", "sha256": "h", "event_type": "x"}])),
            encoding="utf-8",
        )
        build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        self.assertFalse(any(p.name.endswith(".tmp") for p in _HANDOFF.iterdir()))

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_evidence_final_snapshot.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/evidence-final-snapshot", routes)
        for forbidden in [
            "/runner/manual-runtime/evidence-final-snapshot/execute",
            "/runner/manual-runtime/evidence-final-snapshot/apply",
            "/runner/manual-runtime/evidence-final-snapshot/install",
            "/runner/manual-runtime/evidence-final-snapshot/write",
            "/runner/manual-runtime/evidence-final-snapshot/delete",
            "/runner/manual-runtime/evidence-final-snapshot/release",
        ]:
            self.assertNotIn(forbidden, routes)


if __name__ == "__main__":
    unittest.main()
