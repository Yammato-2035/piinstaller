"""
Local-only cloud target credentials on rescue stick — never committed to git.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.telemetry_redaction_contract import redact_telemetry_payload

LOCAL_DIR = Path(os.environ.get("SETUPHELFER_RESCUE_LOCAL_DIR", "/var/lib/setuphelfer-rescue/local"))
CONFIG_FILE = LOCAL_DIR / "cloud_target.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def save_cloud_target_config(
    *,
    endpoint: str,
    username: str = "",
    password: str = "",
    bucket: str = "",
    enabled: bool = True,
) -> dict[str, Any]:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    body = {
        "schema_version": 1,
        "updated_at": _utc_now(),
        "enabled": enabled,
        "endpoint": endpoint.strip(),
        "username": username.strip(),
        "bucket": bucket.strip(),
        "password_set": bool(password.strip()),
        "private_only": True,
        "public_repo": False,
    }
    stored = {
        **body,
        "password": password.strip(),
    }
    CONFIG_FILE.write_text(json.dumps(stored, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except OSError:
        pass
    safe = dict(body)
    safe["password"] = "***" if body["password_set"] else ""
    return {"status": "ok", "config": redact_telemetry_payload(safe), "path": str(CONFIG_FILE)}


def cloud_target_status() -> dict[str, Any]:
    if not CONFIG_FILE.is_file():
        return {
            "status": "not_configured",
            "enabled": False,
            "cloud_target_mode": "local_unlock_test",
            "public_repo": False,
        }
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "error", "enabled": False}
    return {
        "status": "configured" if data.get("enabled") else "disabled",
        "enabled": bool(data.get("enabled")),
        "endpoint": data.get("endpoint", ""),
        "username": data.get("username", ""),
        "bucket": data.get("bucket", ""),
        "password_set": bool(data.get("password_set") or data.get("password")),
        "updated_at": data.get("updated_at"),
        "cloud_target_mode": "local_unlock_test",
        "public_repo": False,
    }
