#!/usr/bin/env python3
"""Entry point for rescue telemetry LAN proxy (imports backend core)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from core.rescue_telemetry_lan_proxy import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
