from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_laptop_failure_final_snapshot import build_manual_laptop_failure_final_snapshot

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_TIMELINE = _HANDOFF / "laptop_failure_evidence_timeline.json"
_OUT = _HANDOFF / "laptop_failure_final_snapshot.json"


def _canonical_without_snapshot_sha256(doc: dict) -> bytes:
    cpy = dict(doc)
    cpy.pop("snapshot_sha256", None)
    return json.dumps(cpy, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class DeployRunnerManualRuntimeLaptopFailureFinalSnapshotV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in (_TIMELINE, _OUT):
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("laptop_failure_final_snapshot.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_timeline(self, status: str, n: int = 1) -> bytes:
        body = {
            "timeline_status": status,
            "generated_at": "2026-05-09T10:00:00Z",
            "events": [{"path": "x", "timestamp": "2026-05-09T09:00:00Z", "sha256": "a"} for _ in range(n)],
        }
        raw = json.dumps(body, indent=2, sort_keys=True).encode("utf-8")
        _TIMELINE.write_bytes(raw)
        return raw

    def test_snapshot_ok(self) -> None:
        raw = self._write_timeline("ok", 2)
        res = build_manual_laptop_failure_final_snapshot(explicit_overwrite=True)
        written = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertEqual(res.get("snapshot_status"), "ok")
        self.assertEqual(res.get("timeline_sha256"), hashlib.sha256(raw).hexdigest())
        self.assertEqual(res.get("event_count"), 2)
        self.assertEqual(
            written.get("snapshot_sha256"),
            hashlib.sha256(_canonical_without_snapshot_sha256(written)).hexdigest(),
        )

    def test_snapshot_review_required(self) -> None:
        self._write_timeline("review_required")
        res = build_manual_laptop_failure_final_snapshot(explicit_overwrite=True)
        self.assertEqual(res.get("snapshot_status"), "review_required")

    def test_snapshot_blocked(self) -> None:
        self._write_timeline("blocked")
        res = build_manual_laptop_failure_final_snapshot(explicit_overwrite=True)
        self.assertEqual(res.get("snapshot_status"), "blocked")

    def test_overwrite_blockiert(self) -> None:
        self._write_timeline("ok")
        first = build_manual_laptop_failure_final_snapshot(explicit_overwrite=True)
        self.assertEqual(first.get("snapshot_status"), "ok")
        second = build_manual_laptop_failure_final_snapshot(explicit_overwrite=False)
        self.assertEqual(second.get("snapshot_status"), "blocked")
        self.assertIn("FINAL_SNAPSHOT_EXISTS_NO_OVERWRITE", second.get("blocked_reasons") or [])

    def test_atomisches_schreiben(self) -> None:
        self._write_timeline("ok")
        build_manual_laptop_failure_final_snapshot(explicit_overwrite=True)
        self.assertTrue(_OUT.is_file())
        self.assertFalse((_HANDOFF / "laptop_failure_final_snapshot.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_manual_runtime_laptop_failure_final_snapshot.py"
        t = src.read_text(encoding="utf-8")
        for bad in ("subprocess", "os.system", "mkfs", "dd ", "wipefs", "mount", "umount", "restore"):
            self.assertNotIn(bad, t)

    def test_keine_verbotenen_unterrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        chunk = routes.read_text(encoding="utf-8")
        start = chunk.find("laptop-failure-final-snapshot")
        self.assertGreater(start, 0)
        block = chunk[start : start + 1200]
        for bad in ("execute", "apply", "install", "delete", "release"):
            self.assertNotIn(bad, block)


if __name__ == "__main__":
    unittest.main()
