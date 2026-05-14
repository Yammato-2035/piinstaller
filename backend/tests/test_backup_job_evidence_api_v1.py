"""API /api/backup/jobs/{id}/evidence und progress_optional JSON-Kompatibilitaet."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

try:
    from fastapi.testclient import TestClient

    from app import app as fastapi_app
    from app import _normalize_evidence_api_payload, _runner_status_to_job

    _HAS_TC = True
except Exception:  # noqa: BLE001
    TestClient = None  # type: ignore[misc, assignment]
    fastapi_app = None
    _normalize_evidence_api_payload = None  # type: ignore[misc, assignment]
    _runner_status_to_job = None  # type: ignore[misc, assignment]
    _HAS_TC = False


class BackupJobEvidenceApiV1Tests(unittest.TestCase):
    @unittest.skipUnless(_HAS_TC, "FastAPI TestClient oder app nicht verfügbar")
    def test_get_evidence_unknown_job_not_500(self) -> None:
        c = TestClient(fastapi_app, base_url="http://localhost")
        r = c.get("/api/backup/jobs/safejob001/evidence")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body.get("status"), "success")
        ev = body.get("evidence") or {}
        self.assertEqual(ev.get("evidence_status"), "not_available")

    @unittest.skipUnless(_HAS_TC, "FastAPI TestClient oder app nicht verfügbar")
    def test_get_evidence_invalid_job_id_contract(self) -> None:
        c = TestClient(fastapi_app, base_url="http://localhost")
        r = c.get("/api/backup/jobs/bad!/evidence")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body.get("status"), "error")
        ev = body.get("evidence") or {}
        self.assertEqual(ev.get("evidence_status"), "invalid_job_id")

    @unittest.skipUnless(_HAS_TC, "FastAPI TestClient oder app nicht verfügbar")
    def test_post_evidence_permission_denied_no_500(self) -> None:
        c = TestClient(fastapi_app, base_url="http://localhost")
        manifest = {
            "output_dir": "/tmp/setuphelfer-evidence-testjob",
            "artifacts": [],
            "captures": [],
            "permission_denied": ["journal_unit_tail"],
        }
        with patch("app._run_backup_evidence_collect", return_value=(manifest, None)):
            r = c.post("/api/backup/jobs/testjob/evidence")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body.get("status"), "success")
        ev = body.get("evidence") or {}
        self.assertEqual(ev.get("evidence_status"), "ok")
        self.assertIn("journal_unit_tail", ev.get("permission_denied_sources") or [])

    def test_normalize_evidence_payload_minimal(self) -> None:
        self.assertIsNotNone(_normalize_evidence_api_payload)
        out = _normalize_evidence_api_payload(None, None)
        self.assertEqual(out["evidence_status"], "not_available")
        man = {
            "output_dir": "/tmp/x",
            "artifacts": [{"name": "status.json", "status": "copied"}],
            "captures": [{"label": "dmesg_tail", "ok": False, "permission_denied": True}],
            "permission_denied": ["dmesg_tail"],
        }
        out2 = _normalize_evidence_api_payload(man, None)
        self.assertEqual(out2["evidence_status"], "ok")
        self.assertTrue(len(out2["collected_sources"]) >= 2)

    def test_runner_status_passes_progress_optional_dict(self) -> None:
        self.assertIsNotNone(_runner_status_to_job)
        j = _runner_status_to_job(
            {
                "status": "running",
                "job_id": "abc",
                "backup_type": "data",
                "code": "backup.job.running",
                "progress_optional": {"phase": "archiving", "bytes_current": 12, "bytes_total_estimate": None},
            }
        )
        po = j.get("progress_optional")
        self.assertIsInstance(po, dict)
        self.assertEqual(po.get("phase"), "archiving")


class BackupProgressUiI18nKeysTests(unittest.TestCase):
    def test_de_locale_has_running_backup_progress_keys(self) -> None:
        root = _backend.parent
        p = root / "frontend" / "src" / "locales" / "de.json"
        de = json.loads(p.read_text(encoding="utf-8"))
        keys = [
            "runningBackup.progress.phase.preflight",
            "runningBackup.progress.activeNoPercent",
            "runningBackup.evidence.create",
            "runningBackup.evidence.hintPaths",
        ]
        for k in keys:
            self.assertIn(k, de, msg=k)
            self.assertTrue(str(de[k]).strip(), msg=k)


if __name__ == "__main__":
    unittest.main()
