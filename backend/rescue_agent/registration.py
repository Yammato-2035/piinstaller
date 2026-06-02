from __future__ import annotations

from datetime import datetime, timedelta, timezone

UTC = timezone.utc


def build_pairing_response(
    *,
    profile: str,
    rescue_pairing_enabled: bool,
    session_id: str,
    server_public_key: str,
    allowed_scopes: list[str] | None = None,
) -> dict:
    if profile == "release" and not rescue_pairing_enabled:
        return {
            "registration_status": "rejected",
            "session_id": "",
            "server_public_key": "",
            "expires_at": "",
            "allowed_scopes": [],
            "errors": ["pairing_disabled_in_release"],
        }
    now = datetime.now(tz=UTC).replace(microsecond=0)
    return {
        "registration_status": "pending" if profile in {"local_lab", "developer"} else "accepted",
        "session_id": session_id,
        "server_public_key": server_public_key,
        "expires_at": (now + timedelta(minutes=15)).isoformat(),
        "allowed_scopes": allowed_scopes or ["heartbeat", "system_report"],
        "errors": [],
    }

