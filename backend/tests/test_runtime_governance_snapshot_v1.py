"""Runtime snapshot fields for /api/version compatibility."""

from __future__ import annotations

import os
from unittest.mock import patch

from runtime_governance.runtime_snapshot import build_runtime_ports_fields
from runtime_governance.service import build_runtime_snapshot_parts, resolve_runtime_governance_bundle


def test_snapshot_includes_ports_and_profile():
    with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=False):
        bundle = resolve_runtime_governance_bundle()
        parts = build_runtime_snapshot_parts(bundle, ["/api/version", "/api/fleet/sessions"])
        assert parts.install_profile == "release"
        assert parts.dev_control_enabled is False
        assert "install_profile" in parts.profile_api_dict
        assert "profile_gate_status" in parts.profile_gate_audit
        ports = build_runtime_ports_fields(bundle)
        assert "runtime_ports" in ports
        assert "canonical_urls" in ports
        assert ports["runtime_ports"]["backend_api"]["port"] == 8000
