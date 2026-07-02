"""Telemetry server ingest contract tests (public schema only)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


class TelemetryServerIngestContractV1Tests(unittest.TestCase):
    def test_ingest_schema_exists(self) -> None:
        path = Path(__file__).resolve().parents[2] / "docs/architecture/telemetry_server_ingest_contract_v1.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("definitions", schema)

    def test_response_status_enum(self) -> None:
        path = Path(__file__).resolve().parents[2] / "docs/architecture/telemetry_server_ingest_contract_v1.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        statuses = schema["definitions"]["ingest_response"]["properties"]["status"]["enum"]
        self.assertIn("quarantine_pending_agreement", statuses)


if __name__ == "__main__":
    unittest.main()
