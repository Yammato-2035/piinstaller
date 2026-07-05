"""
Diagnostics mock server V1 — port 8102, learning import simulation.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

MOCK_PORT = 8102
PII_KEYS = frozenset({"email", "phone", "ip", "mac", "account_id"})


class DiagnosticsMockHandler(BaseHTTPRequestHandler):
  def log_message(self, format: str, *args: object) -> None:
    return

  def _json(self, code: int, body: dict[str, Any]) -> None:
    data = json.dumps(body).encode("utf-8")
    self.send_response(code)
    self.send_header("Content-Type", "application/json")
    self.end_headers()
    self.wfile.write(data)

  def _has_pii(self, obj: Any) -> bool:
    if isinstance(obj, dict):
      for k, v in obj.items():
        if str(k).lower() in PII_KEYS:
          return True
        if self._has_pii(v):
          return True
    elif isinstance(obj, list):
      return any(self._has_pii(i) for i in obj)
    return False

  def do_GET(self) -> None:
    if self.path == "/health":
      self._json(200, {"status": "ok", "service": "diagnostics-mock-v1"})
      return
    self._json(404, {"error": "not_found"})

  def do_POST(self) -> None:
    length = int(self.headers.get("Content-Length") or 0)
    raw = self.rfile.read(length) if length else b"{}"
    try:
      payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
      self._json(400, {"import_status": "rejected_schema"})
      return
    if self._has_pii(payload):
      self._json(422, {"import_status": "rejected_pii", "review_required": True})
      return
    if self.path.endswith("/learning/import"):
      self._json(200, {
        "import_status": "accepted",
        "review_required": True,
        "hardware_key": payload.get("hardware_key", "unknown"),
      })
      return
    self._json(404, {"error": "not_found"})


def run_server(host: str = "127.0.0.1", port: int = MOCK_PORT) -> None:
  HTTPServer((host, port), DiagnosticsMockHandler).serve_forever()


if __name__ == "__main__":
  run_server()
