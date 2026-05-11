from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_laptop_failure_final_acceptance_gate import (
    evaluate_manual_laptop_failure_final_acceptance,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_SNAP = _HANDOFF / "laptop_failure_final_snapshot.json"
_OUT = _HANDOFF / "laptop_failure_final_acceptance.json"


def _canonical_without_snapshot_sha256(doc: dict) -> bytes:
    cpy = dict(doc)
    cpy.pop("snapshot_sha256", None)
    return json.dumps(cpy, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _snapshot(status: str, event_count: int = 1) -> dict:
    body = {
        "snapshot_schema_version": 1,
        "strict_mode": "laptop_failure_final_snapshot",
        "generated_at": "2026-05-09T10:00:00Z",
        "timeline_path": "docs/evidence/runtime-results/handoff/laptop_failure_evidence_timeline.json",
        "timeline_sha256": "abc",
        "event_count": event_count,
        "snapshot_status": status,
    }
    body["snapshot_sha256"] = hashlib.sha256(_canonical_without_snapshot_sha256(body)).hexdigest()
    return body


class DeployRunnerManualRuntimeLaptopFailureFinalAcceptanceGateV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in (_SNAP, _OUT):
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("laptop_failure_final_acceptance.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_snapshot(self, body: dict) -> None:
        _SNAP.write_text(json.dumps(body, indent=2, sort_keys=True), encoding="utf-8")

    def test_accepted(self) -> None:
        self._write_snapshot(_snapshot("ok"))
        res = evaluate_manual_laptop_failure_final_acceptance(explicit_overwrite=True)
        self.assertEqual(res.get("acceptance_status"), "accepted")

    def test_review_required(self) -> None:
        self._write_snapshot(_snapshot("review_required"))
        res = evaluate_manual_laptop_failure_final_acceptance(explicit_overwrite=True)
        self.assertEqual(res.get("acceptance_status"), "review_required")

    def test_blocked_by_status(self) -> None:
        self._write_snapshot(_snapshot("blocked"))
        res = evaluate_manual_laptop_failure_final_acceptance(explicit_overwrite=True)
        self.assertEqual(res.get("acceptance_status"), "blocked")

    def test_blocked_by_bad_hash(self) -> None:
        bad = _snapshot("ok")
        bad["snapshot_sha256"] = "00"
        self._write_snapshot(bad)
        res = evaluate_manual_laptop_failure_final_acceptance(explicit_overwrite=True)
        self.assertEqual(res.get("acceptance_status"), "blocked")
        self.assertIn("FINAL_ACCEPTANCE_SNAPSHOT_SHA_MISMATCH", res.get("blocked_reasons") or [])

    def test_overwrite_blockiert(self) -> None:
        self._write_snapshot(_snapshot("ok"))
        first = evaluate_manual_laptop_failure_final_acceptance(explicit_overwrite=True)
        self.assertEqual(first.get("acceptance_status"), "accepted")
        second = evaluate_manual_laptop_failure_final_acceptance(explicit_overwrite=False)
        self.assertEqual(second.get("acceptance_status"), "blocked")
        self.assertIn("FINAL_ACCEPTANCE_EXISTS_NO_OVERWRITE", second.get("blocked_reasons") or [])

    def test_atomisches_schreiben(self) -> None:
        self._write_snapshot(_snapshot("ok"))
        evaluate_manual_laptop_failure_final_acceptance(explicit_overwrite=True)
        self.assertTrue(_OUT.is_file())
        self.assertFalse((_HANDOFF / "laptop_failure_final_acceptance.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_manual_runtime_laptop_failure_final_acceptance_gate.py"
        t = src.read_text(encoding="utf-8")
        for bad in ("subprocess", "os.system", "mkfs", "dd ", "wipefs", "mount", "umount", "restore"):
            self.assertNotIn(bad, t)

    def test_keine_verbotenen_unterrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        chunk = routes.read_text(encoding="utf-8")
        start = chunk.find("laptop-failure-final-acceptance")
        self.assertGreater(start, 0)
        block = chunk[start : start + 1200]
        for bad in ("execute", "apply", "install", "delete", "release"):
            self.assertNotIn(bad, block)


if __name__ == "__main__":
    unittest.main()
