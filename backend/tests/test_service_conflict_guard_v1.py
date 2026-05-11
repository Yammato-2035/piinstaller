import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.diagnostics.matcher import match_diagnoses
from core.diagnostics.models import DiagnosticsAnalyzeRequest
from core.diagnostics.registry import get_case_by_id
from core import service_conflict_guard as scg

_LEGACY_OPT = Path("/opt") / "pi-installer"


class TestServiceConflictGuardV1(unittest.TestCase):
    def test_compare_versions(self):
        self.assertLess(scg.compare_versions("1.3.4.15", "1.5.0.0"), 0)
        self.assertGreater(scg.compare_versions("1.5.0.0", "1.3.4.15"), 0)
        self.assertEqual(scg.compare_versions("1.5.0.0", "1.5.0.0"), 0)

    def test_matcher_033_legacy_systemd_active(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={"systemd_pi_installer_service": "active"},
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("SERVICE-CONFLICT-033", ids)

    def test_matcher_034_port_owner_pi_installer(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={"port_8000_owner_text": str(_LEGACY_OPT / "backend" / "venv" / "bin" / "python3")},
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("SERVICE-CONFLICT-034", ids)

    def test_matcher_035_mixed_opt_legacy_enabled(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={"mixed_opt_install": "true", "legacy_systemd_still_enabled": "true"},
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("SERVICE-CONFLICT-035", ids)

    def test_matcher_036_flag(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={"legacy_must_not_overwrite_new": "true"},
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("SERVICE-CONFLICT-036", ids)

    def test_matcher_service_conflict_ids_string(self):
        req = DiagnosticsAnalyzeRequest(
            question="",
            signals={"service_conflict_ids": "SERVICE-CONFLICT-033,SERVICE-CONFLICT-034"},
        )
        ids = [h.id for h in match_diagnoses(req)]
        self.assertIn("SERVICE-CONFLICT-033", ids)
        self.assertIn("SERVICE-CONFLICT-034", ids)

    def test_catalog_has_service_conflict_cases(self):
        for cid in (
            "SERVICE-CONFLICT-033",
            "SERVICE-CONFLICT-034",
            "SERVICE-CONFLICT-035",
            "SERVICE-CONFLICT-036",
        ):
            self.assertIsNotNone(get_case_by_id(cid), cid)

    @patch.object(scg, "_systemctl_is_active")
    @patch.object(scg, "detect_port_owner")
    def test_classify_033_when_legacy_active(self, mock_port, mock_active):
        mock_port.return_value = {"port_in_use": True, "owners": [], "listen_pids": [1], "port": 8000}

        def _active(u: str):
            return u == "pi-installer.service"

        mock_active.side_effect = _active
        ids = [c.conflict_id for c in scg.classify_service_conflicts(8000)]
        self.assertIn("SERVICE-CONFLICT-033", ids)

    @patch.object(scg, "_systemctl_is_active")
    @patch.object(scg, "_curl_local_version")
    @patch.object(scg, "detect_port_owner")
    def test_evaluate_conflict_pi_installer_on_port(self, mock_port, mock_curl, mock_active):
        mock_port.return_value = {
            "port_in_use": True,
            "owners": [
                {
                    "pid": 99,
                    "exe": "/usr/bin/python3",
                    "cmdline": f"{_LEGACY_OPT}/backend/venv/bin/python3 -m uvicorn",
                    "cwd": None,
                }
            ],
            "listen_pids": [99],
            "port": 8000,
        }
        mock_curl.return_value = {"reachable": True, "version": "1.3.4.15"}
        mock_active.return_value = False
        d, msg = scg.evaluate_port_before_bind(8000)
        self.assertEqual(d, "conflict")
        self.assertIn("pi-installer", msg)

    @patch.object(scg, "get_expected_install_root")
    @patch.object(scg, "detect_installation_paths")
    def test_classify_036_newer_on_disk(self, mock_paths, mock_root):
        mock_root.return_value = _LEGACY_OPT
        mock_paths.return_value = {
            "legacy_opt": str(_LEGACY_OPT),
            "legacy_opt_exists": True,
            "setuphelfer_opt": "/opt/setuphelfer",
            "setuphelfer_opt_exists": True,
            "expected_install_root": str(_LEGACY_OPT),
            "legacy_version": "1.3.4.15",
            "setuphelfer_version_on_disk": "9.0.0",
        }
        with patch.object(scg, "detect_runtime_version", return_value="1.3.4.15"):
            with patch.object(scg, "detect_setuphelfer_services", return_value={"units": {}}):
                with patch.object(scg, "detect_port_owner", return_value={"port_in_use": False, "owners": []}):
                    ids = [c.conflict_id for c in scg.classify_service_conflicts(8000)]
        self.assertIn("SERVICE-CONFLICT-036", ids)

    @patch.object(scg, "detect_port_owner")
    @patch.object(scg, "_curl_local_version")
    def test_evaluate_same_instance(self, mock_curl, mock_port):
        root = _backend.parent
        mock_port.return_value = {
            "port_in_use": True,
            "owners": [
                {
                    "pid": 1,
                    "exe": str(root / "backend" / "venv" / "bin" / "python3"),
                    "cmdline": f"{root}/backend/venv/bin/python3 -m uvicorn",
                    "cwd": None,
                }
            ],
            "listen_pids": [1],
            "port": 8000,
        }
        mock_curl.return_value = {"reachable": True, "version": scg.read_version_from_install_root(root) or "0"}
        with patch.object(scg, "get_expected_install_root", return_value=root):
            with patch.object(scg, "detect_runtime_version", return_value=mock_curl.return_value["version"]):
                d, _ = scg.evaluate_port_before_bind(8000)
        self.assertEqual(d, "same_instance")


if __name__ == "__main__":
    unittest.main()
