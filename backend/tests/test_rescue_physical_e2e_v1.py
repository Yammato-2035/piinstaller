"""Tests for SETUPHELFER-E2E-LIVE-001D physical rescue E2E."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.rescue_physical_e2e_consent import consent_allows_send, normalize_consent_choice
from core.rescue_physical_e2e_event_emitter import PhysicalE2EEventEmitter
from core.rescue_physical_e2e_journal import append_event_journal, journal_dir_for_run, read_json, store_receipt
from core.rescue_physical_e2e_manifest import build_directory_summary, compare_manifest_summaries
from core.rescue_physical_e2e_models import OPERATION_EVENTS
from core.rescue_physical_e2e_orchestrator import init_physical_e2e_session, run_physical_e2e_workflow
from core.rescue_physical_e2e_send import send_telemetry_event
from core.rescue_physical_e2e_storage_safety import directory_is_empty, validate_restore_target
from core.rescue_physical_e2e_telemetry_payload import (
    assert_payload_no_pii,
    build_physical_e2e_telemetry_payload,
    new_e2e_run_id,
)


def _mock_transport_accept(*_args, **_kwargs):
    body = json.dumps(
        {
            "accepted": True,
            "receipt_id": "receipt-test-1",
            "forward_outbox_status": "pending",
            "e2e_run_id": "test-run",
        }
    )
    return 200, body, {}


def _mock_transport_offline(*_args, **_kwargs):
    return 0, "offline", {}


class TestPhysicalE2EHelpers(unittest.TestCase):
    def test_e2e_run_id_format(self):
        run_id = new_e2e_run_id()
        self.assertTrue(run_id.startswith("e2e-rescue-physical-"))

    def test_consent_required_for_send(self):
        self.assertFalse(consent_allows_send(normalize_consent_choice("local_only")))
        self.assertTrue(consent_allows_send(normalize_consent_choice("granted")))

    def test_payload_no_pii(self):
        payload = build_physical_e2e_telemetry_payload(
            operation_event="backup_started",
            event_id="evt-1",
            e2e_run_id="run-1",
            rescue_session_id="sess-1",
            device_id_hash="abc123",
            rescue_version="1.10.0.21",
            payload_sha256="a" * 64,
        )
        assert_payload_no_pii(payload)
        with self.assertRaises(ValueError):
            assert_payload_no_pii({**payload, "note": "192.168.1.1"})

    def test_journal_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = journal_dir_for_run(Path(tmp), "run-test")
            journal.mkdir(parents=True)
            append_event_journal(journal, {"event_id": "e1", "state": "locally_recorded"})
            lines = (journal / "event-journal.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertNotIn("token", record)

    def test_receipt_no_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = journal_dir_for_run(Path(tmp), "run-test")
            journal.mkdir(parents=True)
            store_receipt(
                journal,
                {"event_id": "e1", "receipt_id": "r1", "authorization": "Bearer secret"},
            )
            data = read_json(journal / "receipts.json")
            self.assertEqual(data["receipts"][0]["authorization"], "[redacted]")


class TestStorageSafety(unittest.TestCase):
    def test_block_root_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            backup = Path(tmp) / "backup"
            src.mkdir()
            backup.mkdir()
            result = validate_restore_target(Path("/"), source_path=src, backup_path=backup)
            self.assertFalse(result["ok"])

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "empty"
            self.assertTrue(directory_is_empty(target))


class TestPhysicalE2EWorkflow(unittest.TestCase):
    def _prepare_tree(self, base: Path) -> Path:
        source = base / "source"
        source.mkdir()
        (source / "a").mkdir()
        (source / "a" / "f1.txt").write_text("hello\n", encoding="utf-8")
        (source / "b.bin").write_bytes(b"\x00\x01\x02")
        return source

    def test_full_workflow_local_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = self._prepare_tree(base)
            backup = base / "backup" / "e2e.tar.gz"
            restore = base / "restore" / "data"
            backup.parent.mkdir(parents=True)
            restore.parent.mkdir(parents=True)

            result = run_physical_e2e_workflow(
                source_dir=source,
                backup_archive=backup,
                restore_dir=restore,
                consent="local_only",
                operator_approved=True,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
                allowed_restore_prefixes=(base,),
                setup_logs_base=base,
                skip_diagnostics_poll=True,
                lab_tmpfs_mode=True,
            )
            self.assertTrue(result["success"])
            self.assertEqual(result["comparison"]["restore_integrity_status"], "passed")
            self.assertTrue(backup.is_file())
            self.assertTrue(any(restore.rglob("f1.txt")))

    def test_workflow_blocked_without_operator(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = self._prepare_tree(base)
            result = run_physical_e2e_workflow(
                source_dir=source,
                backup_archive=base / "b.tar.gz",
                restore_dir=base / "r",
                consent="granted",
                operator_approved=False,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
                allowed_restore_prefixes=(base,),
            )
            self.assertFalse(result["success"])
            self.assertEqual(result["code"], "operator_gate_blocked")

    def test_telemetry_send_with_mock(self):
        with tempfile.TemporaryDirectory() as tmp:
            session, journal = init_physical_e2e_session(consent="granted", setup_logs_base=Path(tmp))
            emitter = PhysicalE2EEventEmitter(
                session,
                journal,
                token_file="/dev/null",
                http_transport=_mock_transport_accept,
            )
            with patch("core.rescue_physical_e2e_send._token_present", return_value=True), patch(
                "core.rescue_physical_e2e_send._read_bearer_token", return_value="test-token"
            ):
                out = emitter.emit("backup_started")
            self.assertTrue(out["sent"])

    def test_offline_queue_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = journal_dir_for_run(Path(tmp), "offline-run")
            journal.mkdir(parents=True)
            payload = build_physical_e2e_telemetry_payload(
                operation_event="backup_started",
                event_id="evt-offline",
                e2e_run_id="offline-run",
                rescue_session_id="sess",
                device_id_hash="dev",
                rescue_version="1.10.0.21",
                payload_sha256="b" * 64,
            )
            with patch("core.rescue_physical_e2e_send._token_present", return_value=True), patch(
                "core.rescue_physical_e2e_send._read_bearer_token", return_value="test-token"
            ):
                result = send_telemetry_event(
                    payload=payload,
                    e2e_run_id="offline-run",
                    journal_dir=journal,
                    http_transport=_mock_transport_offline,
                )
            self.assertEqual(result["send_status"], "queued_offline")

    def test_retry_keeps_event_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            session, journal = init_physical_e2e_session(consent="granted", setup_logs_base=Path(tmp))
            emitter = PhysicalE2EEventEmitter(session, journal, http_transport=_mock_transport_accept)
            with patch("core.rescue_physical_e2e_send._token_present", return_value=True), patch(
                "core.rescue_physical_e2e_send._read_bearer_token", return_value="test-token"
            ):
                first = emitter.emit("verify_started")
                second = emitter.emit("verify_started")
            self.assertEqual(first["event_id"], second["event_id"])

    def test_manifest_compare(self):
        summary = {"file_count": 2, "total_bytes": 10, "manifest_sha256": "abc"}
        self.assertTrue(compare_manifest_summaries(summary, summary)["manifest_match"])

    def test_operation_events_count(self):
        self.assertEqual(len(OPERATION_EVENTS), 8)


if __name__ == "__main__":
    unittest.main()
