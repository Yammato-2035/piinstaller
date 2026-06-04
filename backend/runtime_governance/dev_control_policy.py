"""Development control (DCC) capability policy."""

from __future__ import annotations

from runtime_governance.models import RuntimeCapabilities


def dev_control_enabled(capabilities: RuntimeCapabilities) -> bool:
    return capabilities.dev_control_enabled
