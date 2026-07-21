"""Unit tests for rescue GUI HTTP server (PI-RS-BVR-GUI-DCC-001)."""

from __future__ import annotations

import ast
import json
import socket
import tempfile
import threading
import time
import unittest
from http.client import HTTPConnection
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SERVER = REPO / "scripts/rescue-live/image/setuphelfer-rescue-ui-http-server"


class RescueGuiHttpServerTests(unittest.TestCase):
    def test_server_source_parses_and_has_no_non_ascii_bytes_literals(self) -> None:
        text = SERVER.read_text(encoding="utf-8")
        ast.parse(text)
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, bytes):
                self.assertTrue(
                    all(b < 128 for b in node.value),
                    msg="bytes literal must be ASCII-only",
                )

    def _load_server_module(self):
        import sys
        import types

        name = "rescue_ui_http_dcc001"
        mod = types.ModuleType(name)
        mod.__file__ = str(SERVER)
        sys.modules[name] = mod
        code = compile(SERVER.read_text(encoding="utf-8"), str(SERVER), "exec")
        exec(code, mod.__dict__)
        return mod

    def test_health_ready_with_assets(self) -> None:
        mod = self._load_server_module()

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "auto-e2e-progress.html").write_text("<html></html>", encoding="utf-8")
            loc = root / "locales"
            loc.mkdir()
            for name in ("de-DE", "en-US", "fr-FR", "nl-NL"):
                (loc / f"{name}.json").write_text("{}", encoding="utf-8")
            health = mod.build_health(root, index_name="auto-e2e-progress.html")
            self.assertTrue(health["index_exists"])
            self.assertEqual(health["i18n_validation"], "passed")

    def test_health_fails_when_locale_missing(self) -> None:
        mod = self._load_server_module()

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "auto-e2e-progress.html").write_text("<html></html>", encoding="utf-8")
            (root / "locales").mkdir()
            (root / "locales" / "de-DE.json").write_text("{}", encoding="utf-8")
            health = mod.build_health(root, index_name="auto-e2e-progress.html")
            self.assertEqual(health["i18n_validation"], "failed")
            self.assertIn("en-US.json", health["missing_locales"])

    def test_bind_and_health_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "auto-e2e-progress.html").write_text("<html>ok</html>", encoding="utf-8")
            loc = root / "locales"
            loc.mkdir()
            for name in ("de-DE", "en-US", "fr-FR", "nl-NL"):
                (loc / f"{name}.json").write_text(json.dumps({"title": name}), encoding="utf-8")

            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
            sock.close()

            import subprocess

            proc = subprocess.Popen(
                [
                    "python3",
                    str(SERVER),
                    "--bind",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--document-root",
                    str(root),
                    "--index-name",
                    "auto-e2e-progress.html",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                ready = False
                last_err = ""
                for _ in range(40):
                    if proc.poll() is not None:
                        last_err = proc.stderr.read() if proc.stderr else "exited early"
                        break
                    try:
                        conn = HTTPConnection("127.0.0.1", port, timeout=0.5)
                        conn.request("GET", "/health.json")
                        resp = conn.getresponse()
                        body = json.loads(resp.read().decode("utf-8"))
                        conn.close()
                        if resp.status == 200 and body.get("status") == "ready":
                            ready = True
                            break
                    except OSError:
                        time.sleep(0.05)
                self.assertTrue(ready, last_err or "not ready")
            finally:
                proc.kill()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass

    def test_index_missing_exit_code(self) -> None:
        import subprocess

        with tempfile.TemporaryDirectory() as td:
            proc = subprocess.run(
                [
                    "python3",
                    str(SERVER),
                    "--document-root",
                    td,
                    "--index-name",
                    "missing.html",
                    "--port",
                    "17965",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 3)
            self.assertIn("rescue.gui.index_missing", proc.stderr)


class RescueGuiLauncherContractRegression(unittest.TestCase):
    def test_launcher_contract_still_ok(self) -> None:
        from rescue.rescue_ui_launcher_contract import validate_launcher_script_contract

        text = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-ui-launch").read_text(
            encoding="utf-8"
        )
        result = validate_launcher_script_contract(text)
        self.assertTrue(result["contract_ok"], result["errors"])
        self.assertIn("setuphelfer-rescue-ui-http-server", text)
        self.assertIn("health.json", text)
        self.assertIn("no_graphical_browser_available_or_not_started", text)


if __name__ == "__main__":
    unittest.main()
