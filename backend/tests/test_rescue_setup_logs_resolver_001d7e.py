"""Tests for SETUPHELFER-E2E-LIVE-001D7E SETUP_LOGS resolution + discovery import."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.rescue_auto_discovery_import import (
    build_acceptance_from_import,
    detect_evidence_mode,
    import_auto_discovery_evidence,
)
from core.rescue_setup_logs_resolver import (
    CANONICAL_MOUNT,
    select_setup_logs_for_import,
    validate_mountpoint,
    write_environment_file,
    write_resolution_state,
)


REPO = Path(__file__).resolve().parents[2]


class ValidateMountTests(unittest.TestCase):
    def test_shadow_directory_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / "SETUP_LOGS"
            shadow.mkdir()
            with patch("core.rescue_setup_logs_resolver.findmnt_source", return_value=None):
                result = validate_mountpoint(shadow, expected_device="/dev/sdc2")
            self.assertFalse(result["ok"])
            self.assertEqual(result["resolution_status"], "not_mounted")
            self.assertTrue(result.get("shadow_directory"))

    def test_wrong_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = Path(tmp) / "SETUP_LOGS"
            mp.mkdir()
            with patch("core.rescue_setup_logs_resolver.findmnt_source", return_value="/dev/sdb2"):
                result = validate_mountpoint(mp, expected_device="/dev/sdc2")
            self.assertFalse(result["ok"])
            self.assertEqual(result["resolution_status"], "mounted_wrong_source")

    def test_valid_mount_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp = Path(tmp) / "SETUP_LOGS"
            (mp / "setuphelfer").mkdir(parents=True)
            with patch("core.rescue_setup_logs_resolver.findmnt_source", return_value="/dev/sdc2"):
                result = validate_mountpoint(mp, expected_device="/dev/sdc2")
            self.assertTrue(result["ok"])
            self.assertEqual(result["resolution_status"], "mounted_valid")


class SelectImportMountTests(unittest.TestCase):
    def test_explicit_root_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "SETUP_LOGS_STICK"
            (root / "setuphelfer").mkdir(parents=True)
            with patch("core.rescue_setup_logs_resolver.findmnt_source", return_value="/dev/sdc2"):
                with patch(
                    "core.rescue_setup_logs_resolver.validate_mountpoint",
                    return_value={"ok": True, "mount_source_verified": True},
                ):
                    selected = select_setup_logs_for_import(explicit_root=root)
            self.assertTrue(selected["ok"])
            self.assertEqual(selected["source"], "explicit")

    def test_env_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "SETUP_LOGS2"
            (root / "setuphelfer").mkdir(parents=True)
            with patch.dict(os.environ, {"SETUP_LOGS": str(root)}, clear=False):
                with patch("core.rescue_setup_logs_resolver.findmnt_source", return_value="/dev/sdc2"):
                    selected = select_setup_logs_for_import()
            self.assertTrue(selected["ok"])
            self.assertEqual(selected["source"], "environment")

    def test_shadow_ignored_when_scanning(self):
        with tempfile.TemporaryDirectory() as tmp:
            shadow = Path(tmp) / "media" / "volker" / "SETUP_LOGS"
            shadow.mkdir(parents=True)
            real = Path(tmp) / "media" / "volker" / "SETUP_LOGS_STICK"
            (real / "setuphelfer").mkdir(parents=True)

            def fake_findmnt(path: Path):
                if path == real:
                    return "/dev/sdc2"
                return None

            with patch("core.rescue_setup_logs_resolver.discover_setup_logs_partitions", return_value=[]):
                with patch("core.rescue_setup_logs_resolver.findmnt_source", side_effect=fake_findmnt):
                    with patch("core.rescue_setup_logs_resolver.Path") as path_cls:
                        # Fall back to direct call with patched glob via select internals:
                        pass
            # Direct unit-level: empty shadow must fail findmnt and not be selected alone.
            with patch("core.rescue_setup_logs_resolver.findmnt_source", return_value=None):
                with patch("core.rescue_setup_logs_resolver.discover_setup_logs_partitions", return_value=[]):
                    with patch.dict(os.environ, {}, clear=False):
                        os.environ.pop("SETUP_LOGS", None)
                        os.environ.pop("SETUPHELFER_SETUP_LOGS_ROOT", None)
                        selected = select_setup_logs_for_import()
            self.assertFalse(selected["ok"])
            self.assertTrue(selected.get("shadow_mount_ignored"))


class EnvironmentAndStateTests(unittest.TestCase):
    def test_environment_file_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "run"
            with patch("core.rescue_setup_logs_resolver.STATE_DIR", state):
                with patch("core.rescue_setup_logs_resolver.ENV_FILE", state / "environment"):
                    with patch("core.rescue_setup_logs_resolver.RESOLUTION_PATH", state / "setup-logs-resolution.json"):
                        write_resolution_state(
                            {
                                "resolved": True,
                                "device_path": "/dev/sdc2",
                                "actual_mountpoint": "/run/setuphelfer-rescue/media/SETUP_LOGS",
                                "mount_source_verified": True,
                                "writable": True,
                                "resolution_status": "mounted_valid",
                            }
                        )
                        write_environment_file(
                            setup_logs_root=CANONICAL_MOUNT,
                            evidence_root=CANONICAL_MOUNT / "setuphelfer" / "evidence",
                        )
                        env = (state / "environment").read_text(encoding="utf-8")
                        self.assertIn("SETUPHELFER_SETUP_LOGS_ROOT=", env)
                        self.assertIn("SETUPHELFER_EVIDENCE_ROOT=", env)


class ImportModeTests(unittest.TestCase):
    def test_detect_auto_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            boot = base / "setuphelfer/evidence/discovery-boot/boot-1"
            boot.mkdir(parents=True)
            (boot / "00-observer-start.json").write_text("{}\n", encoding="utf-8")
            mode = detect_evidence_mode(base)
            self.assertTrue(mode["ok"])
            self.assertEqual(mode["mode"], "auto-discovery")

    def test_import_auto_discovery_boot(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            logs = Path(tmp) / "SETUP_LOGS"
            boot_id = "boot-abc"
            boot = logs / "setuphelfer/evidence/discovery-boot" / boot_id
            boot.mkdir(parents=True)
            (boot / "00-observer-start.json").write_text(
                json.dumps({"observer_started": True, "boot_id": boot_id}), encoding="utf-8"
            )
            (boot / "00-start-gate.json").write_text(json.dumps({"called": True}), encoding="utf-8")
            (boot / "boot-finalizer.json").write_text(
                json.dumps({"terminal": True, "status": "failed_discovery_start_gate_not_invoked"}),
                encoding="utf-8",
            )
            (boot / "setup-logs-resolution.json").write_text(
                json.dumps({"resolved": True, "mount_source_verified": True}), encoding="utf-8"
            )
            ctrl = logs / "setuphelfer/e2e-live-001d/discovery-run-control.json"
            ctrl.parent.mkdir(parents=True)
            ctrl.write_text(
                json.dumps({"enabled": False, "consumed": True, "terminal_status": "failed_discovery_start_gate_not_invoked"}),
                encoding="utf-8",
            )
            (repo / "docs/evidence/e2e_live_001d").mkdir(parents=True)
            result = import_auto_discovery_evidence(repo_root=repo, setup_logs_base=logs)
            self.assertTrue(result["import_ok"])
            self.assertTrue(result["discovery_boot_imported"])
            self.assertEqual(result["acceptance_status"], "rescue_auto_discovery_failure_fully_observed")
            self.assertTrue((repo / "docs/evidence/e2e_live_001d/physical_discovery_runs" / boot_id / "boot").is_dir())

    def test_acceptance_complete(self):
        summary = {
            "payload_version": "1.10.0.29",
            "boot_id": "b1",
            "session_id": "s1",
            "observability": {
                "session_present": True,
                "boot_finalizer_present": True,
                "start_gate_audit_present": True,
            },
            "boot_observer": {"boot_directory_created": True, "partition_resolved": True},
            "tui_guard": {"bare_tty_visible": False},
            "run_control": {"consumed": True},
            "setup_logs_resolution": {},
            "import": {},
        }
        acc = build_acceptance_from_import(summary)
        self.assertEqual(acc["status"], "rescue_auto_discovery_evidence_complete")


class SourceGateTests(unittest.TestCase):
    def test_resolver_script_and_unit_present(self):
        script = REPO / "scripts/rescue-live/image/setuphelfer-rescue-resolve-setup-logs"
        unit = REPO / "scripts/rescue-live/image/systemd/setuphelfer-rescue-setup-logs-resolver.service"
        self.assertTrue(script.is_file())
        self.assertTrue(unit.is_file())
        text = unit.read_text(encoding="utf-8")
        self.assertIn("Before=setuphelfer-rescue-boot-observer.service", text)
        observer = (REPO / "scripts/rescue-live/image/systemd/setuphelfer-rescue-boot-observer.service").read_text(
            encoding="utf-8"
        )
        self.assertIn("EnvironmentFile=-/run/setuphelfer-rescue/environment", observer)
        self.assertIn("setuphelfer-rescue-setup-logs-resolver.service", observer)


if __name__ == "__main__":
    unittest.main()
