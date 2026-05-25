from __future__ import annotations

import inspect
import os
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from core import deploy_orchestrator as orchestrator


def _base_state() -> dict:
    return {
        "status": "ready",
        "workspace": "/home/volker/piinstaller",
        "runtime_path": "/opt/setuphelfer",
        "workspace_dirty_count": 0,
        "helper": {
            "systemd_unit_present": True,
            "can_start_without_password": "unknown",
            "requires_operator_setup": False,
        },
        "next_action": {"type": "deploy_required", "label": "deploy", "commands": []},
        "runtime_gate": {"exit_code": 14, "status": "yellow"},
        "deploy_drift": {"status": "yellow", "suggested_actions": ["deploy_backend_files"]},
        "last_job": {"status": "idle", "deploy_exit_code": None},
    }


class DeployOrchestratorTests(unittest.TestCase):
    def test_request_without_confirm_is_blocked(self) -> None:
        with patch.object(orchestrator, "build_deploy_job_state", return_value=_base_state()), patch.object(
            orchestrator.subprocess, "run"
        ) as run_mock:
            result = orchestrator.request_controlled_deploy(False)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("operator_confirm_required", result["errors"])
        run_mock.assert_not_called()

    def test_request_with_confirm_calls_only_systemctl_start_unit(self) -> None:
        latest = _base_state()
        latest["status"] = "running"
        with (
            patch.object(orchestrator, "build_deploy_job_state", side_effect=[_base_state(), latest]),
            patch.object(
                orchestrator.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(
                    ["systemctl", "start", orchestrator.DEFAULT_SYSTEMD_UNIT], 0, "", ""
                ),
            ) as run_mock,
        ):
            result = orchestrator.request_controlled_deploy(True)
        self.assertIn(result["status"], ("running", "ready", "success", "blocked"))
        run_mock.assert_called_once()
        self.assertEqual(
            run_mock.call_args[0][0],
            ["systemctl", "start", orchestrator.DEFAULT_SYSTEMD_UNIT],
        )

    def test_permission_denied_becomes_operator_required(self) -> None:
        proc = subprocess.CompletedProcess(
            ["systemctl", "start", orchestrator.DEFAULT_SYSTEMD_UNIT],
            1,
            "",
            "Access denied",
        )
        with (
            patch.object(orchestrator, "build_deploy_job_state", return_value=_base_state()),
            patch.object(orchestrator.subprocess, "run", return_value=proc),
        ):
            result = orchestrator.request_controlled_deploy(True)
        self.assertEqual(result["status"], "operator_required")
        self.assertIn("permission_denied", result["errors"])
        self.assertIn("operator_setup", result)

    def test_backend_never_calls_deploy_to_opt_directly(self) -> None:
        source = inspect.getsource(orchestrator.request_controlled_deploy)
        self.assertNotIn("deploy-to-opt.sh", source)

    def test_operator_setup_commands_are_only_returned(self) -> None:
        with patch.object(orchestrator.subprocess, "run") as run_mock:
            payload = orchestrator.build_deploy_operator_setup_commands()
        self.assertEqual(payload["status"], "operator_required")
        joined = "\n".join(payload["commands"])
        self.assertIn("systemctl daemon-reload", joined)
        self.assertIn("setuphelfer-deploy-helper-root.sh", joined)
        run_mock.assert_not_called()

    def test_operator_setup_commands_contain_no_forbidden_actions(self) -> None:
        payload = orchestrator.build_deploy_operator_setup_commands()
        joined = "\n".join(payload["commands"]).lower()
        for token in ("apt ", "dd ", "mkfs", "restore", "backup", "deploy-to-opt.sh"):
            self.assertNotIn(token, joined)

    def test_no_shell_injection_via_workspace_path(self) -> None:
        weird = '/tmp/x"; touch /tmp/pwned; echo "'
        with (
            patch.dict(os.environ, {"SETUPHELFER_DEPLOY_WORKSPACE_ROOT": weird}, clear=False),
            patch.object(orchestrator, "build_deploy_job_state", side_effect=[_base_state(), _base_state()]),
            patch.object(
                orchestrator.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(
                    ["systemctl", "start", orchestrator.DEFAULT_SYSTEMD_UNIT], 0, "", ""
                ),
            ) as run_mock,
        ):
            orchestrator.request_controlled_deploy(True)
        self.assertEqual(
            run_mock.call_args[0][0],
            ["systemctl", "start", orchestrator.DEFAULT_SYSTEMD_UNIT],
        )


if __name__ == "__main__":
    unittest.main()
