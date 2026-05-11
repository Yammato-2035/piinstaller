import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

try:
    from fastapi.testclient import TestClient
    from app import app

    _HAS = True
except Exception:
    _HAS = False
    TestClient = None
    app = None


@unittest.skipUnless(_HAS, "FastAPI TestClient oder app nicht verfuegbar")
class TestDiagnosticsEvidenceApiV1(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, base_url="http://localhost")

    def test_evidence_schema(self):
        r = self.client.get("/api/diagnostics/evidence/schema")
        self.assertEqual(r.status_code, 200, r.text)
        payload = r.json()
        self.assertIn("properties", payload)
        self.assertIn("matched_diagnosis_ids", payload.get("properties", {}))

    def test_evidence_sample(self):
        r = self.client.get("/api/diagnostics/evidence/sample")
        self.assertEqual(r.status_code, 200, r.text)
        payload = r.json()
        self.assertIn("sample", payload)
        self.assertIn("total_records", payload)


if __name__ == "__main__":
    unittest.main()
