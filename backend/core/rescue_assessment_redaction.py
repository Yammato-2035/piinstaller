"""
Rescue assessment redaction — strip PII before assessment export or telemetry build.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from core.telemetry_redaction_contract import redact_telemetry_payload

REDACTION_VERSION = "assessment.redaction.v2"

_IP_RE = re.compile(
  r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|[01]?\d?\d)){3})\b"
)
_MAC_RE = re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_SERIAL_KEYS = frozenset({"serial", "serial_number", "disk_serial", "nvme_serial"})
_FILE_LIST_KEYS = frozenset({"file_list", "files", "directory_listing", "user_files"})


def _hash_pseudo(value: str) -> str:
  return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]


def scan_forbidden_fields(payload: dict[str, Any]) -> list[str]:
  """Return list of forbidden field markers found in raw assessment."""
  forbidden: list[str] = []
  blob = str(payload)
  if _EMAIL_RE.search(blob):
    forbidden.append("contains_email")
  if _IP_RE.search(blob):
    forbidden.append("contains_ip")
  if _MAC_RE.search(blob):
    forbidden.append("contains_mac")
  for key in _FILE_LIST_KEYS:
    if key in payload:
      forbidden.append("contains_file_list")
      break
  def walk(obj: Any, key: str = "") -> None:
    lk = key.lower()
    if lk in _SERIAL_KEYS and isinstance(obj, str) and len(obj) > 4:
      if not obj.startswith("sha256:"):
        forbidden.append("contains_serial_plaintext")
    if isinstance(obj, dict):
      for k, v in obj.items():
        walk(v, str(k))
    elif isinstance(obj, list):
      for item in obj:
        walk(item, key)
  walk(payload)
  return sorted(set(forbidden))


def redact_assessment_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
  """
  Redact assessment dict and return (redacted_payload, redaction_report).
  """
  before = scan_forbidden_fields(payload)
  redacted = redact_telemetry_payload(dict(payload))
  # Strip raw lsblk serial fields if present
  if "storage" in redacted and isinstance(redacted["storage"], dict):
    disks = redacted["storage"].get("disks")
    if isinstance(disks, list):
      for disk in disks:
        if isinstance(disk, dict) and "serial" in disk:
          raw = str(disk.pop("serial", ""))
          if raw:
            disk["serial_pseudonym"] = _hash_pseudo(raw)
  after = scan_forbidden_fields(redacted)
  report = {
    "redaction_version": REDACTION_VERSION,
    "forbidden_before": before,
    "forbidden_after": after,
    "contains_mac": "contains_mac" in after,
    "contains_ip": "contains_ip" in after,
    "contains_email": "contains_email" in after,
    "contains_serial_plaintext": "contains_serial_plaintext" in after,
    "contains_file_list": "contains_file_list" in after,
    "contains_user_files": False,
    "contains_secrets": False,
    "redaction_applied": True,
  }
  redacted["privacy"] = report
  return redacted, report
