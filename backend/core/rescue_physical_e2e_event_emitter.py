"""Event emitter — binds operations to journal, consent, and HTTPS send."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from core.rescue_physical_e2e_consent import consent_allows_send
from core.rescue_physical_e2e_journal import append_event_journal, read_json
from core.rescue_physical_e2e_models import PhysicalE2ESession
from core.rescue_physical_e2e_send import send_telemetry_event
from core.rescue_physical_e2e_telemetry_payload import (
    build_physical_e2e_telemetry_payload,
    new_event_id,
)

HttpTransportFn = Callable[[str, bytes, dict[str, str], int], tuple[int, str, dict[str, str]]]


class PhysicalE2EEventEmitter:
    def __init__(
        self,
        session: PhysicalE2ESession,
        journal_dir: Path,
        *,
        ingest_url: str | None = None,
        token_file: str | None = None,
        http_transport: HttpTransportFn | None = None,
    ) -> None:
        self.session = session
        self.journal_dir = journal_dir
        self.ingest_url = ingest_url
        self.token_file = token_file
        self.http_transport = http_transport
        self._event_ids: dict[str, str] = {}

    def _event_id_for(self, operation_event: str) -> str:
        if operation_event not in self._event_ids:
            self._event_ids[operation_event] = new_event_id()
        return self._event_ids[operation_event]

    def emit(
        self,
        operation_event: str,
        *,
        assessment: dict[str, Any] | None = None,
        operation_status: str = "completed",
        send: bool | None = None,
    ) -> dict[str, Any]:
        event_id = self._event_id_for(operation_event)
        payload = build_physical_e2e_telemetry_payload(
            operation_event=operation_event,
            event_id=event_id,
            e2e_run_id=self.session.e2e_run_id,
            rescue_session_id=self.session.rescue_session_id,
            device_id_hash=self.session.device_id_hash,
            rescue_version=self.session.payload_version,
            payload_sha256=self.session.payload_sha256,
            backup_job_id=self.session.backup_job_id,
            restore_job_id=self.session.restore_job_id,
            assessment=assessment,
            operation_status=operation_status,
        )
        local_record = {
            "event_id": event_id,
            "operation_event": operation_event,
            "e2e_run_id": self.session.e2e_run_id,
            "state": "locally_recorded",
        }
        append_event_journal(self.journal_dir, local_record)

        should_send = send if send is not None else consent_allows_send(self.session.consent)
        if not should_send:
            append_event_journal(
                self.journal_dir,
                {**local_record, "state": "consent_blocked", "telemetry_status": "consent_not_granted"},
            )
            return {"event_id": event_id, "sent": False, "state": "consent_blocked", "payload": payload}

        send_result = send_telemetry_event(
            payload=payload,
            e2e_run_id=self.session.e2e_run_id,
            journal_dir=self.journal_dir,
            ingest_url=self.ingest_url,
            token_file=self.token_file,
            http_transport=self.http_transport,
        )
        return {
            "event_id": event_id,
            "sent": bool(send_result.get("accepted")),
            "state": send_result.get("send_status"),
            "receipt": send_result,
            "payload": payload,
        }

    def retry_pending(self) -> list[dict[str, Any]]:
        status = read_json(self.journal_dir / "send-status.json")
        if status.get("send_status") != "queued_offline":
            return []
        pending_event = status.get("last_event_id")
        if not pending_event:
            return []
        results: list[dict[str, Any]] = []
        for operation, event_id in self._event_ids.items():
            if event_id != pending_event:
                continue
            results.append(
                self.emit(operation, send=True)
            )
        return results

    def summary(self) -> dict[str, Any]:
        receipts = read_json(self.journal_dir / "receipts.json")
        return {
            "events_recorded": len(self._event_ids),
            "receipts_stored": int(receipts.get("count") or 0),
            "event_ids": dict(self._event_ids),
        }
