"""PI-RS-TEL-001 environment configuration (no secrets in code)."""

from __future__ import annotations

import os

from core.rescue_lab_telemetry_model import RESCUE_LAB_CLIENT_ID_DEFAULT, RescueLabTelemetryConfig

ENV_LAB_BASE_URL = "SETUPHELPER_TELEMETRY_LAB_BASE_URL"
ENV_CLIENT_ID = "SETUPHELPER_LAB_CLIENT_FAKE_RESCUE_STICK_ID"
ENV_CLIENT_SECRET = "SETUPHELPER_LAB_CLIENT_FAKE_RESCUE_STICK_SECRET"
ENV_LIVE_TEST = "SETUPHELPER_ENABLE_LIVE_LAB_TELEMETRY_TEST"


def load_rescue_lab_telemetry_config() -> RescueLabTelemetryConfig:
    return RescueLabTelemetryConfig(
        lab_base_url=(os.environ.get(ENV_LAB_BASE_URL) or "").strip() or None,
        client_id=(os.environ.get(ENV_CLIENT_ID) or RESCUE_LAB_CLIENT_ID_DEFAULT).strip(),
        secret=(os.environ.get(ENV_CLIENT_SECRET) or "").strip() or None,
    )
