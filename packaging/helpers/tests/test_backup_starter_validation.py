from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch


def _has_fastapi() -> bool:
    return importlib.util.find_spec("fastapi") is not None


def _import_app():
    repo = Path(__file__).resolve().parents[3]
    backend = repo / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))
    import app as app_module

    return app_module


def _load_module():
    root = Path(__file__).resolve().parents[1]
    mod_path = root / "setuphelfer-backup-starter.py"
    spec = importlib.util.spec_from_file_location("setuphelfer_backup_starter", mod_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load starter module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestBackupStarterValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = _load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.jobs = self.base / "jobs"
        self.jobs.mkdir(parents=True, exist_ok=True)
        self.allowed = self.base / "mnt" / "setuphelfer" / "backups"
        self.allowed.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_job(self, job_id: str, backup_dir: str) -> None:
        d = self.jobs / job_id
        d.mkdir(parents=True, exist_ok=True)
        (d / "job.json").write_text(
            json.dumps({"job_id": job_id, "backup_dir": backup_dir}),
            encoding="utf-8",
        )

    def test_valid_job_id_accepted(self) -> None:
        self.assertTrue(self.mod._validate_job_id("job-1_A.z"))

    def test_job_id_with_slash_rejected(self) -> None:
        self.assertFalse(self.mod._validate_job_id("bad/id"))

    def test_job_id_with_space_rejected(self) -> None:
        self.assertFalse(self.mod._validate_job_id("bad id"))

    def test_job_id_with_shell_meta_rejected(self) -> None:
        self.assertFalse(self.mod._validate_job_id("bad;id"))

    def test_missing_job_json_rejected(self) -> None:
        with patch.object(self.mod, "JOB_BASE_DIR", self.jobs):
            payload, code = self.mod._load_job("missing")
        self.assertIsNone(payload)
        self.assertEqual(code, "backup.starter_job_not_found")

    def test_backup_dir_outside_allowed_rejected(self) -> None:
        outside = self.base / "tmp" / "x"
        outside.mkdir(parents=True, exist_ok=True)
        with patch.object(self.mod, "ALLOWED_BACKUP_ROOT", self.allowed):
            self.assertFalse(self.mod._validate_backup_dir(str(outside)))

    def test_relative_backup_dir_rejected(self) -> None:
        with patch.object(self.mod, "ALLOWED_BACKUP_ROOT", self.allowed):
            self.assertFalse(self.mod._validate_backup_dir("relative/path"))

    def test_unit_name_built_internally(self) -> None:
        injected = "x.service --force"
        unit = self.mod._unit_name_for(injected)
        self.assertEqual(unit, f"setuphelfer-backup@{injected}.service")
        self.assertTrue(unit.startswith("setuphelfer-backup@"))
        self.assertTrue(unit.endswith(".service"))

    def test_systemctl_called_with_list_and_shell_false(self) -> None:
        self._write_job("job1", str(self.allowed))
        calls = {}

        class _CP:
            returncode = 0
            stdout = ""
            stderr = ""

        def _fake_run(cmd, capture_output, text, check, shell):
            calls["cmd"] = cmd
            calls["shell"] = shell
            return _CP()

        with patch.object(self.mod, "JOB_BASE_DIR", self.jobs):
            with patch.object(self.mod, "ALLOWED_BACKUP_ROOT", self.allowed):
                with patch.object(self.mod, "_authorized_for_starter", return_value=True):
                    with patch.object(self.mod.subprocess, "run", side_effect=_fake_run):
                        rc = self.mod.main(["start", "job1"])
        self.assertEqual(rc, 0)
        self.assertEqual(calls["cmd"], ["systemctl", "start", "setuphelfer-backup@job1.service"])
        self.assertIs(calls["shell"], False)

    def test_symlink_outside_allowed_rejected(self) -> None:
        outside = self.base / "other"
        outside.mkdir(parents=True, exist_ok=True)
        link = self.allowed / "link-out"
        link.symlink_to(outside, target_is_directory=True)
        with patch.object(self.mod, "ALLOWED_BACKUP_ROOT", self.allowed):
            self.assertFalse(self.mod._validate_backup_dir(str(link)))

    def test_invalid_job_id_code(self) -> None:
        rc = self.mod.main(["start", "bad/id"])
        self.assertEqual(rc, 1)


@unittest.skipUnless(_has_fastapi(), "fastapi")
class TestStartBackupViaHelper(unittest.TestCase):
    def setUp(self) -> None:
        self.app = _import_app()
        self.tmp = tempfile.TemporaryDirectory()
        self.helper_path = Path(self.tmp.name) / "setuphelfer-backup-starter"
        self.helper_path.write_text("#!/bin/sh\necho\n", encoding="utf-8")
        self.helper_path.chmod(0o755)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_helper_success_ok_true(self) -> None:
        payload = {"ok": True, "code": "backup.starter_started", "job_id": "abc123def456"}
        out = json.dumps(payload)

        def _fake_run(*args, **kwargs):
            self.assertIs(kwargs.get("shell"), False)
            return subprocess.CompletedProcess(args=args[0], returncode=0, stdout=out, stderr="")

        with patch.dict(os.environ, {"SETUPHELFER_BACKUP_HELPER_PATH": str(self.helper_path)}, clear=False):
            with patch.object(self.app.subprocess, "run", side_effect=_fake_run):
                ok, code, raw = self.app._start_backup_via_helper("abc123def456")
        self.assertTrue(ok)
        self.assertEqual(code, "backup.starter_started")
        self.assertEqual(raw.get("job_id"), "abc123def456")

    def test_invalid_job_id_rejected_before_subprocess(self) -> None:
        called = []

        def _fake_run(*args, **kwargs):
            called.append(True)
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="{}", stderr="")

        with patch.object(self.app.subprocess, "run", side_effect=_fake_run):
            ok, code, raw = self.app._start_backup_via_helper("bad/id")
        self.assertFalse(ok)
        self.assertEqual(code, "backup.starter_invalid_job_id")
        self.assertEqual(called, [])

    def test_helper_not_found(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_BACKUP_HELPER_PATH": "/nonexistent/no-helper"}, clear=False):
            ok, code, raw = self.app._start_backup_via_helper("abc123def456")
        self.assertFalse(ok)
        self.assertEqual(code, "backup.starter_not_found")

    def test_helper_timeout(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_BACKUP_HELPER_PATH": str(self.helper_path)}, clear=False):
            with patch.object(
                self.app.subprocess,
                "run",
                side_effect=subprocess.TimeoutExpired(cmd=[str(self.helper_path)], timeout=10),
            ):
                ok, code, raw = self.app._start_backup_via_helper("abc123def456")
        self.assertFalse(ok)
        self.assertEqual(code, "backup.starter_timeout")

    def test_helper_non_json_stdout(self) -> None:
        def _fake_run(*args, **kwargs):
            return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="NOT_JSON", stderr="")

        with patch.dict(os.environ, {"SETUPHELFER_BACKUP_HELPER_PATH": str(self.helper_path)}, clear=False):
            with patch.object(self.app.subprocess, "run", side_effect=_fake_run):
                ok, code, raw = self.app._start_backup_via_helper("abc123def456")
        self.assertFalse(ok)
        self.assertEqual(code, "backup.starter_invalid_response")

    def test_helper_ok_false_passes_code(self) -> None:
        payload = {"ok": False, "code": "backup.starter_job_not_found"}
        out = json.dumps(payload)

        def _fake_run(*args, **kwargs):
            return subprocess.CompletedProcess(args=args[0], returncode=1, stdout=out, stderr="")

        with patch.dict(os.environ, {"SETUPHELFER_BACKUP_HELPER_PATH": str(self.helper_path)}, clear=False):
            with patch.object(self.app.subprocess, "run", side_effect=_fake_run):
                ok, code, raw = self.app._start_backup_via_helper("abc123def456")
        self.assertFalse(ok)
        self.assertEqual(code, "backup.starter_job_not_found")

    def test_subprocess_run_shell_false_guard(self) -> None:
        seen = {}

        def _fake_run(*args, **kwargs):
            seen["shell"] = kwargs.get("shell")
            return subprocess.CompletedProcess(
                args=args[0], returncode=0, stdout=json.dumps({"ok": True}), stderr=""
            )

        with patch.dict(os.environ, {"SETUPHELFER_BACKUP_HELPER_PATH": str(self.helper_path)}, clear=False):
            with patch.object(self.app.subprocess, "run", side_effect=_fake_run):
                self.app._start_backup_via_helper("abc123def456")
        self.assertIs(seen.get("shell"), False)


class TestStarterPolkitAuth(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = _load_module()

    def test_pkcheck_called_with_shell_false(self) -> None:
        seen: dict[str, Any] = {}

        def _fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            seen["shell"] = kwargs.get("shell")
            cmd = args[0] if args else []
            return subprocess.CompletedProcess(list(cmd), 0, "", "")

        with patch.object(self.mod.os, "geteuid", return_value=1000):
            with patch.object(self.mod.subprocess, "run", side_effect=_fake_run):
                self.mod._authorized_for_starter()
        self.assertIs(seen.get("shell"), False)

    def test_pkcheck_fails_denied(self) -> None:
        with patch.object(self.mod.os, "geteuid", return_value=1000):
            with patch.object(
                self.mod.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(["pkcheck"], 1, "", "no"),
            ):
                self.assertFalse(self.mod._authorized_for_starter())

    def test_pkcheck_success(self) -> None:
        with patch.object(self.mod.os, "geteuid", return_value=1000):
            with patch.object(
                self.mod.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(["pkcheck"], 0, "", ""),
            ):
                self.assertTrue(self.mod._authorized_for_starter())

    def test_root_skips_pkcheck(self) -> None:
        with patch.object(self.mod.os, "geteuid", return_value=0):
            with patch.object(self.mod.subprocess, "run") as m_run:
                self.assertTrue(self.mod._authorized_for_starter())
                m_run.assert_not_called()

    def test_main_emits_permission_denied_when_unauthorized(self) -> None:
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        tmp = tempfile.TemporaryDirectory()
        try:
            jobs = Path(tmp.name) / "jobs"
            jobs.mkdir(parents=True)
            allowed = Path(tmp.name) / "mnt" / "setuphelfer" / "backups"
            allowed.mkdir(parents=True)
            jd = jobs / "jobx"
            jd.mkdir(parents=True)
            (jd / "job.json").write_text(
                json.dumps({"job_id": "jobx", "backup_dir": str(allowed)}),
                encoding="utf-8",
            )
            with patch.object(self.mod, "JOB_BASE_DIR", jobs):
                with patch.object(self.mod, "ALLOWED_BACKUP_ROOT", allowed):
                    with patch.object(self.mod.os, "geteuid", return_value=1000):
                        with patch.object(self.mod, "_authorized_for_starter", return_value=False):
                            with redirect_stdout(buf):
                                rc = self.mod.main(["start", "jobx"])
        finally:
            tmp.cleanup()
        self.assertEqual(rc, 1)
        payload = json.loads(buf.getvalue().strip())
        self.assertEqual(payload.get("code"), "backup.starter_permission_denied")


if __name__ == "__main__":
    unittest.main()

