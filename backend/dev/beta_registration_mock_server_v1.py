"""
Beta registration mock server V1 — port 8100, no PII persistence.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

MOCK_PORT = 8100


class BetaMockHandler(BaseHTTPRequestHandler):
  def log_message(self, format: str, *args: object) -> None:
    return

  def _json(self, code: int, body: dict[str, Any]) -> None:
    data = json.dumps(body).encode("utf-8")
    self.send_response(code)
    self.send_header("Content-Type", "application/json")
    self.end_headers()
    self.wfile.write(data)

  def do_GET(self) -> None:
    if self.path in {"/health", "/public/v1/beta/status"}:
      self._json(200, {
        "status": "beta_mock",
        "registration_open": True,
        "mfa_required": True,
        "email_verification_required": True,
      })
      return
    self._json(404, {"error": "not_found"})

  def do_POST(self) -> None:
    length = int(self.headers.get("Content-Length") or 0)
    raw = self.rfile.read(length) if length else b"{}"
    try:
      body = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
      self._json(400, {"error": "invalid_json"})
      return
    if self.path.endswith("/register"):
      self._json(200, {"status": "pending_email_verification", "mfa_setup_required": True})
      return
    if self.path.endswith("/internal/v1/sticks/check-upload-permission"):
      self._json(200, {
        "upload_allowed": body.get("agreement_valid", False),
        "quarantine_required": not body.get("agreement_valid", False),
      })
      return
    self._json(404, {"error": "not_found"})


def run_server(host: str = "127.0.0.1", port: int = MOCK_PORT) -> None:
  HTTPServer((host, port), BetaMockHandler).serve_forever()


if __name__ == "__main__":
  run_server()
