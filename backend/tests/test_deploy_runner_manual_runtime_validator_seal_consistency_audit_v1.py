from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_validator_seal_consistency_audit import run_validator_seal_consistency_audit
from deploy.routes_source_aggregate import read_deploy_routes_aggregate

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_INDEX = _HANDOFF / "validator_seal_index.json"
_AUDIT = _HANDOFF / "validator_seal_consistency_audit.json"


def _seal_body(source_rel: str, sha: str) -> dict:
    return {
        "seal_schema_version": 1,
        "sealed_at": "2026-05-08T12:00:00Z",
        "source_report": source_rel,
        "source_report_sha256": sha,
        "validator_status": "ok",
        "strict_mode": "immutable_validator_report_seal",
    }


class DeployRunnerManualRuntimeValidatorSealConsistencyAuditV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in _HANDOFF.glob("*.seal.json"):
            p.unlink(missing_ok=True)
        _INDEX.unlink(missing_ok=True)
        _AUDIT.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p in list(_HANDOFF.glob("*.seal.json")) + [_INDEX, _AUDIT]:
            if p.exists() or (isinstance(p, Path) and p.is_symlink()):
                p.unlink(missing_ok=True)
        sym = _HANDOFF / "sym_index.json"
        if sym.exists() or sym.is_symlink():
            sym.unlink(missing_ok=True)

    def _write_index(self, seals: list[dict]) -> None:
        _INDEX.write_text(
            json.dumps({"index_schema_version": 1, "seals": seals}, indent=2),
            encoding="utf-8",
        )

    def test_valid_index_ok(self) -> None:
        src = _HANDOFF / "audit_src.json"
        raw = json.dumps({"x": 1}).encode("utf-8")
        src.write_bytes(raw)
        sha = hashlib.sha256(raw).hexdigest()
        seal = _HANDOFF / "audit_one.seal.json"
        seal.write_text(json.dumps(_seal_body(str(src.relative_to(_REPO_ROOT)), sha)), encoding="utf-8")
        self._write_index(
            [
                {
                    "seal_file": str(seal.relative_to(_REPO_ROOT)),
                    "source_report": str(src.relative_to(_REPO_ROOT)),
                    "source_report_sha256": sha,
                    "sealed_at": "2026-05-08T12:00:00Z",
                }
            ]
        )
        out = run_validator_seal_consistency_audit(explicit_overwrite=True)
        self.assertEqual(out["audit_status"], "ok")
        self.assertEqual(out["valid_entries"], 1)
        self.assertTrue(_AUDIT.is_file())

    def test_missing_seal_warns(self) -> None:
        src = _HANDOFF / "audit_src2.json"
        src.write_bytes(b"{}")
        sha = hashlib.sha256(b"{}").hexdigest()
        self._write_index(
            [
                {
                    "seal_file": "docs/evidence/runtime-results/handoff/nope.seal.json",
                    "source_report": str(src.relative_to(_REPO_ROOT)),
                    "source_report_sha256": sha,
                    "sealed_at": "2026-05-08T12:00:00Z",
                },
                {
                    "seal_file": str((_HANDOFF / "real.seal.json").relative_to(_REPO_ROOT)),
                    "source_report": str(src.relative_to(_REPO_ROOT)),
                    "source_report_sha256": sha,
                    "sealed_at": "2026-05-08T12:00:00Z",
                },
            ]
        )
        real = _HANDOFF / "real.seal.json"
        real.write_text(json.dumps(_seal_body(str(src.relative_to(_REPO_ROOT)), sha)), encoding="utf-8")
        out = run_validator_seal_consistency_audit(explicit_overwrite=True)
        self.assertEqual(out["audit_status"], "review_required")
        self.assertEqual(out["valid_entries"], 1)
        self.assertTrue(any("seal_file_missing" in w for w in out["warnings"]))

    def test_sha256_mismatch_warns(self) -> None:
        src = _HANDOFF / "audit_src3.json"
        src.write_bytes(b"payload")
        sha = hashlib.sha256(b"payload").hexdigest()
        seal = _HANDOFF / "m.seal.json"
        seal.write_text(json.dumps(_seal_body(str(src.relative_to(_REPO_ROOT)), sha)), encoding="utf-8")
        self._write_index(
            [
                {
                    "seal_file": str(seal.relative_to(_REPO_ROOT)),
                    "source_report": str(src.relative_to(_REPO_ROOT)),
                    "source_report_sha256": "0" * 64,
                    "sealed_at": "2026-05-08T12:00:00Z",
                },
                {
                    "seal_file": str((_HANDOFF / "good.seal.json").relative_to(_REPO_ROOT)),
                    "source_report": str(src.relative_to(_REPO_ROOT)),
                    "source_report_sha256": sha,
                    "sealed_at": "2026-05-08T12:00:00Z",
                },
            ]
        )
        good = _HANDOFF / "good.seal.json"
        good.write_text(json.dumps(_seal_body(str(src.relative_to(_REPO_ROOT)), sha)), encoding="utf-8")
        out = run_validator_seal_consistency_audit(explicit_overwrite=True)
        self.assertEqual(out["audit_status"], "review_required")
        self.assertTrue(any("sha256_mismatch" in w for w in out["warnings"]))

    def test_missing_source_report_warns(self) -> None:
        sha = hashlib.sha256(b"x").hexdigest()
        seal = _HANDOFF / "ms.seal.json"
        seal.write_text(
            json.dumps(_seal_body("docs/evidence/runtime-results/handoff/ghost.json", sha)),
            encoding="utf-8",
        )
        self._write_index(
            [
                {
                    "seal_file": str(seal.relative_to(_REPO_ROOT)),
                    "source_report": "docs/evidence/runtime-results/handoff/ghost.json",
                    "source_report_sha256": sha,
                    "sealed_at": "2026-05-08T12:00:00Z",
                },
                {
                    "seal_file": str((_HANDOFF / "g2.seal.json").relative_to(_REPO_ROOT)),
                    "source_report": str((_HANDOFF / "src4.json").relative_to(_REPO_ROOT)),
                    "source_report_sha256": hashlib.sha256(b"y").hexdigest(),
                    "sealed_at": "2026-05-08T12:00:00Z",
                },
            ]
        )
        s4 = _HANDOFF / "src4.json"
        s4.write_bytes(b"y")
        g2 = _HANDOFF / "g2.seal.json"
        g2.write_text(
            json.dumps(_seal_body(str(s4.relative_to(_REPO_ROOT)), hashlib.sha256(b"y").hexdigest())),
            encoding="utf-8",
        )
        out = run_validator_seal_consistency_audit(explicit_overwrite=True)
        self.assertTrue(any("missing_source_report" in w for w in out["warnings"]))

    def test_invalid_seal_json_warns(self) -> None:
        src = _HANDOFF / "audit_src5.json"
        src.write_bytes(b"{}")
        sha = hashlib.sha256(b"{}").hexdigest()
        bad = _HANDOFF / "badjson.seal.json"
        bad.write_text("{", encoding="utf-8")
        good = _HANDOFF / "okjson.seal.json"
        good.write_text(json.dumps(_seal_body(str(src.relative_to(_REPO_ROOT)), sha)), encoding="utf-8")
        self._write_index(
            [
                {
                    "seal_file": str(bad.relative_to(_REPO_ROOT)),
                    "source_report": str(src.relative_to(_REPO_ROOT)),
                    "source_report_sha256": sha,
                    "sealed_at": "2026-05-08T12:00:00Z",
                },
                {
                    "seal_file": str(good.relative_to(_REPO_ROOT)),
                    "source_report": str(src.relative_to(_REPO_ROOT)),
                    "source_report_sha256": sha,
                    "sealed_at": "2026-05-08T12:00:00Z",
                },
            ]
        )
        out = run_validator_seal_consistency_audit(explicit_overwrite=True)
        self.assertTrue(any("invalid_seal_json" in w for w in out["warnings"]))

    def test_no_valid_entries_blocked(self) -> None:
        self._write_index(
            [
                {
                    "seal_file": "docs/evidence/runtime-results/handoff/absent.seal.json",
                    "source_report": "docs/evidence/runtime-results/handoff/absent.json",
                    "source_report_sha256": "ab",
                    "sealed_at": "2026-05-08T12:00:00Z",
                }
            ]
        )
        out = run_validator_seal_consistency_audit(explicit_overwrite=True)
        self.assertEqual(out["audit_status"], "blocked")
        self.assertIn("AUDIT_NO_VALID_ENTRIES", out["blocked_reasons"])

    def test_symlink_index_blocked(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write('{"seals":[]}')
            ext = tmp.name
        self.addCleanup(lambda: os.path.exists(ext) and os.unlink(ext))
        if _INDEX.exists():
            _INDEX.unlink()
        _INDEX.symlink_to(ext)
        out = run_validator_seal_consistency_audit(explicit_overwrite=True)
        self.assertEqual(out["audit_status"], "blocked")

    def test_traversal_path_constant(self) -> None:
        self.assertNotIn("..", Path("docs/evidence/runtime-results/handoff/validator_seal_consistency_audit.json").parts)

    def test_existing_audit_blocks(self) -> None:
        src = _HANDOFF / "audit_src6.json"
        src.write_bytes(b"{}")
        sha = hashlib.sha256(b"{}").hexdigest()
        seal = _HANDOFF / "final.seal.json"
        seal.write_text(json.dumps(_seal_body(str(src.relative_to(_REPO_ROOT)), sha)), encoding="utf-8")
        self._write_index(
            [
                {
                    "seal_file": str(seal.relative_to(_REPO_ROOT)),
                    "source_report": str(src.relative_to(_REPO_ROOT)),
                    "source_report_sha256": sha,
                    "sealed_at": "2026-05-08T12:00:00Z",
                }
            ]
        )
        first = run_validator_seal_consistency_audit(explicit_overwrite=True)
        self.assertEqual(first["audit_status"], "ok")
        second = run_validator_seal_consistency_audit(explicit_overwrite=False)
        self.assertEqual(second["audit_status"], "blocked")
        self.assertIn("AUDIT_OUTPUT_EXISTS_NO_OVERWRITE", second["blocked_reasons"])

    def test_explicit_overwrite(self) -> None:
        src = _HANDOFF / "audit_src7.json"
        src.write_bytes(b"{}")
        sha = hashlib.sha256(b"{}").hexdigest()
        seal = _HANDOFF / "final2.seal.json"
        seal.write_text(json.dumps(_seal_body(str(src.relative_to(_REPO_ROOT)), sha)), encoding="utf-8")
        self._write_index(
            [
                {
                    "seal_file": str(seal.relative_to(_REPO_ROOT)),
                    "source_report": str(src.relative_to(_REPO_ROOT)),
                    "source_report_sha256": sha,
                    "sealed_at": "2026-05-08T12:00:00Z",
                }
            ]
        )
        run_validator_seal_consistency_audit(explicit_overwrite=True)
        out = run_validator_seal_consistency_audit(explicit_overwrite=True)
        self.assertEqual(out["audit_status"], "ok")

    def test_atomic_no_tmp(self) -> None:
        src = _HANDOFF / "audit_src8.json"
        src.write_bytes(b"{}")
        sha = hashlib.sha256(b"{}").hexdigest()
        seal = _HANDOFF / "final3.seal.json"
        seal.write_text(json.dumps(_seal_body(str(src.relative_to(_REPO_ROOT)), sha)), encoding="utf-8")
        self._write_index(
            [
                {
                    "seal_file": str(seal.relative_to(_REPO_ROOT)),
                    "source_report": str(src.relative_to(_REPO_ROOT)),
                    "source_report_sha256": sha,
                    "sealed_at": "2026-05-08T12:00:00Z",
                }
            ]
        )
        run_validator_seal_consistency_audit(explicit_overwrite=True)
        self.assertFalse(any(p.name.endswith(".tmp") for p in _HANDOFF.iterdir()))

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_validator_seal_consistency_audit.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = read_deploy_routes_aggregate()
        self.assertIn("/runner/manual-runtime/result-validator-seal-consistency-audit", routes)
        for forbidden in [
            "/runner/manual-runtime/result-validator-seal-consistency-audit/execute",
            "/runner/manual-runtime/result-validator-seal-consistency-audit/apply",
            "/runner/manual-runtime/result-validator-seal-consistency-audit/install",
            "/runner/manual-runtime/result-validator-seal-consistency-audit/write",
            "/runner/manual-runtime/result-validator-seal-consistency-audit/delete",
            "/runner/manual-runtime/result-validator-seal-consistency-audit/release",
        ]:
            self.assertNotIn(forbidden, routes)


if __name__ == "__main__":
    unittest.main()
