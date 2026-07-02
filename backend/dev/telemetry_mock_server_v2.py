"""
Telemetry mock server V2 — lab target on port 8101 (stdlib HTTP).
No persistence, no remote commands, no secrets.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

MOCK_PORT = 8101
FORBIDDEN_PATH_PREFIXES = (
  "/execute",
  "/command",
  "/shell",
  "/remote-help",
  "/fix",
  "/apply",
  "/write",
  "/mount",
  "/wipe",
  "/restore",
)

_state: dict[str, Any] = {
  "stick_known": True,
  "agreement_valid": True,
  "device_approved": True,
  "ingest_status": "accepted",
}


class TelemetryMockHandler(BaseHTTPRequestHandler):
  def log_message(self, format: str, *args: object) -> None:
    return

  def _json(self, code: int, body: dict[str, Any]) -> None:
    data = json.dumps(body).encode("utf-8")
    self.send_response(code)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(data)))
    self.end_headers()
    self.wfile.write(data)

  def do_GET(self) -> None:
    if self.path in {"/health", "/v1/telemetry/health"}:
      self._json(200, {"status": "ok", "service": "telemetry-mock-v2", "port": MOCK_PORT})
      return
    for prefix in FORBIDDEN_PATH_PREFIXES:
      if self.path.startswith(prefix):
        self._json(403, {"error": "forbidden_route"})
        return
    self._json(404, {"error": "not_found"})

  def do_POST(self) -> None:
    for prefix in FORBIDDEN_PATH_PREFIXES:
      if self.path.startswith(prefix):
        self._json(403, {"error": "forbidden_route"})
        return
    length = int(self.headers.get("Content-Length") or 0)
    raw = self.rfile.read(length) if length else b"{}"
    try:
      payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
      self._json(400, {"accepted": False, "status": "rejected_schema"})
      return
    if self.path.endswith("/dry-run"):
      self._json(200, {"accepted": True, "status": "dry_run_ok", "event_id": payload.get("event_id")})
      return
    if self.path.endswith("/ingest"):
      if not _state.get("stick_known"):
        self._json(403, {"accepted": False, "status": "rejected_auth"})
        return
      if not _state.get("agreement_valid"):
        self._json(202, {
          "accepted": False,
          "status": "quarantine_pending_agreement",
          "diagnostics_forwarded": False,
          "learning_export_allowed": False,
        })
        return
      status = _state.get("ingest_status", "accepted")
      self._json(200, {
        "accepted": status == "accepted",
        "status": status,
        "event_id": payload.get("event_id"),
        "redaction_applied": True,
        "diagnostics_forwarded": status == "accepted",
        "learning_export_allowed": status == "accepted",
        "message_de": "Mock-Ingest",
        "message_en": "Mock ingest",
      })
      return
    self._json(404, {"error": "not_found"})


def run_server(host: str = "127.0.0.1", port: int = MOCK_PORT) -> None:
  HTTPServer((host, port), TelemetryMockHandler).serve_forever()


if __name__ == "__main__":
  run_server()
