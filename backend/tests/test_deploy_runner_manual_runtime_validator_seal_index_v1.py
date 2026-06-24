from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_validator_seal_index import build_validator_report_seal_index
from deploy.routes_source_aggregate import read_deploy_routes_aggregate

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_INDEX = "docs/evidence/runtime-results/handoff/validator_seal_index.json"


def _ok_seal(source_report: str = "docs/evidence/runtime-results/handoff/validator_dryrun_report.json") -> dict:
    return {
        "seal_schema_version": 1,
        "sealed_at": "2026-05-08T12:00:00Z",
        "source_report": source_report,
        "source_report_sha256": "abc123",
        "validator_status": "ok",
        "strict_mode": "immutable_validator_report_seal",
    }


class DeployRunnerManualRuntimeValidatorSealIndexV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.handoff = _HANDOFF
        self.handoff.mkdir(parents=True, exist_ok=True)
        self.index_path = self.handoff / "validator_seal_index.json"
        self._cleanup: list[Path] = []
        for p in self.handoff.glob("*.seal.json"):
            p.unlink(missing_ok=True)
        self.index_path.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p in self._cleanup:
            if p.exists() or p.is_symlink():
                p.unlink()
        if self.index_path.exists():
            self.index_path.unlink()
        for tmp in self.handoff.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def _add(self, name: str, body: str | dict) -> Path:
        p = self.handoff / name
        if isinstance(body, dict):
            p.write_text(json.dumps(body), encoding="utf-8")
        else:
            p.write_text(body, encoding="utf-8")
        self._cleanup.append(p)
        return p

    def test_valid_seal_indexed(self) -> None:
        self._add("a.seal.json", _ok_seal())
        out = build_validator_report_seal_index(explicit_overwrite=True)
        self.assertEqual(out["index_status"], "ok")
        self.assertEqual(len(out["indexed_seals"]), 1)
        data = json.loads(self.index_path.read_text(encoding="utf-8"))
        self.assertEqual(data["seal_count"], 1)

    def test_multiple_seals_indexed(self) -> None:
        s1 = _ok_seal()
        s1["sealed_at"] = "2026-05-08T10:00:00Z"
        s1["source_report_sha256"] = "aa"
        s2 = _ok_seal()
        s2["sealed_at"] = "2026-05-08T11:00:00Z"
        s2["source_report_sha256"] = "bb"
        self._add("one.seal.json", s1)
        self._add("two.seal.json", s2)
        out = build_validator_report_seal_index(explicit_overwrite=True)
        self.assertEqual(out["index_status"], "ok")
        self.assertEqual(len(out["indexed_seals"]), 2)

    def test_invalid_json_warns(self) -> None:
        self._add("bad.seal.json", "{not json")
        self._add("good.seal.json", _ok_seal())
        out = build_validator_report_seal_index(explicit_overwrite=True)
        self.assertEqual(out["index_status"], "review_required")
        self.assertTrue(any("invalid_seal_skipped:bad.seal.json" in w for w in out["warnings"]))
        self.assertEqual(len(out["indexed_seals"]), 1)

    def test_missing_sha256_skipped(self) -> None:
        s = _ok_seal()
        del s["source_report_sha256"]
        self._add("nohash.seal.json", s)
        self._add("ok.seal.json", _ok_seal())
        out = build_validator_report_seal_index(explicit_overwrite=True)
        self.assertTrue(any("nohash.seal.json" in w for w in out["warnings"]))

    def test_validator_status_not_ok_skipped(self) -> None:
        s = _ok_seal()
        s["validator_status"] = "fail"
        self._add("badv.seal.json", s)
        self._add("ok.seal.json", _ok_seal())
        out = build_validator_report_seal_index(explicit_overwrite=True)
        self.assertTrue(any("badv.seal.json" in w for w in out["warnings"]))

    def test_symlink_seal_skipped(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write(json.dumps(_ok_seal()))
            ext = tmp.name
        self.addCleanup(lambda: os.path.exists(ext) and os.unlink(ext))
        link = self.handoff / "sym.seal.json"
        link.symlink_to(ext)
        self._cleanup.append(link)
        self._add("ok.seal.json", _ok_seal())
        out = build_validator_report_seal_index(explicit_overwrite=True)
        self.assertTrue(any("sym.seal.json" in w for w in out["warnings"]))

    def test_index_path_no_traversal(self) -> None:
        self.assertNotIn("..", Path(_INDEX).parts)

    def test_existing_index_blocks_without_overwrite(self) -> None:
        self._add("x.seal.json", _ok_seal())
        first = build_validator_report_seal_index(explicit_overwrite=True)
        self.assertEqual(first["index_status"], "ok")
        second = build_validator_report_seal_index(explicit_overwrite=False)
        self.assertEqual(second["index_status"], "blocked")
        self.assertIn("INDEX_EXISTS_NO_OVERWRITE", second["blocked_reasons"])

    def test_explicit_overwrite_rewrites_index(self) -> None:
        self._add("x.seal.json", _ok_seal())
        build_validator_report_seal_index(explicit_overwrite=True)
        out = build_validator_report_seal_index(explicit_overwrite=True)
        self.assertEqual(out["index_status"], "ok")

    def test_atomic_no_tmp_left(self) -> None:
        self._add("x.seal.json", _ok_seal())
        build_validator_report_seal_index(explicit_overwrite=True)
        self.assertFalse(any(p.name.endswith(".tmp") for p in self.handoff.iterdir()))

    def test_no_valid_seals_blocked(self) -> None:
        out = build_validator_report_seal_index(explicit_overwrite=True)
        self.assertEqual(out["index_status"], "blocked")
        self.assertIn("INDEX_NO_VALID_SEALS", out["blocked_reasons"])

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_validator_seal_index.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = read_deploy_routes_aggregate()
        self.assertIn("/runner/manual-runtime/result-validator-seal-index", routes)
        for forbidden in [
            "/runner/manual-runtime/result-validator-seal-index/execute",
            "/runner/manual-runtime/result-validator-seal-index/apply",
            "/runner/manual-runtime/result-validator-seal-index/install",
            "/runner/manual-runtime/result-validator-seal-index/write",
            "/runner/manual-runtime/result-validator-seal-index/delete",
            "/runner/manual-runtime/result-validator-seal-index/release",
        ]:
            self.assertNotIn(forbidden, routes)


if __name__ == "__main__":
    unittest.main()
