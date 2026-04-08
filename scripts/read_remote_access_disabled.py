#!/usr/bin/env python3
"""Liest remote_access_disabled aus Setuphelfer-config. Exit 0 = deaktiviert, 1 = aktiviert (Remote erlaubt)."""
import json
import sys
from pathlib import Path

_CANDIDATES = [
    Path("/etc/setuphelfer/config.json"),
    Path("/etc/pi-installer/config.json"),
    Path.home() / ".config" / "setuphelfer" / "config.json",
    Path.home() / ".config" / "pi-installer" / "config.json",
]
for p in _CANDIDATES:
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            disabled = data.get("settings", {}).get("network", {}).get("remote_access_disabled", False)
            sys.exit(0 if disabled else 1)
        except Exception:
            pass
sys.exit(1)
