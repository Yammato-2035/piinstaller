"""Runtime-Gate Exit-Codes: dokumentierte Matrix + bash -n fuer Shell-Skripte."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent

GATE_EXIT_MATRIX = {
    0: "ok",
    10: "backend_inactive",
    11: "backend_api_unreachable",
    12: "project_version_mismatch",
    13: "backend_runtime_path_invalid",
    14: "deploy_backend_files_recommended",
    15: "restart_backend_manual_recommended",
    16: "deploy_manifest_mismatch",
    17: "backend_hanging_active_port_but_http_timeout",
    18: "backend_version_endpoint_timeout",
    20: "deploy_drift_gray_or_dashboard_missing",
}


class TestBackendHealthcheckGateV1(unittest.TestCase):
    def test_gate_exit_matrix_documents_hang_and_version_timeout(self) -> None:
        self.assertEqual(GATE_EXIT_MATRIX[17], "backend_hanging_active_port_but_http_timeout")
        self.assertEqual(GATE_EXIT_MATRIX[18], "backend_version_endpoint_timeout")

    def test_runtime_gate_script_syntax(self) -> None:
        script = _REPO / "scripts" / "check-runtime-deploy-gate.sh"
        proc = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

    def test_backend_version_gate_script_syntax(self) -> None:
        script = _REPO / "scripts" / "check-backend-version-gate.sh"
        proc = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

    def test_healthcheck_script_syntax(self) -> None:
        script = _REPO / "scripts" / "healthcheck" / "setuphelfer-backend-healthcheck.sh"
        self.assertTrue(script.is_file(), script)
        proc = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

    def test_runtime_gate_script_mentions_exit_18(self) -> None:
        text = (_REPO / "scripts" / "check-runtime-deploy-gate.sh").read_text(encoding="utf-8")
        self.assertIn("backend_version_endpoint_timeout", text)
        self.assertIn("exit 18", text.lower())
