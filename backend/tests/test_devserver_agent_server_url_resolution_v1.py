from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from devserver_agent.config import validate_server_url
from devserver_agent.server_url import (
    DEFAULT_QEMU_HOST_URL,
    candidate_server_urls,
    is_private_or_local_dev_server_url,
    resolve_dev_server_url,
)


class DevAgentServerUrlResolutionTests(unittest.TestCase):
    def test_cli_server_first_in_candidates(self) -> None:
        c = candidate_server_urls(
            cli_server="http://10.0.2.2:8000",
            env_server="http://127.0.0.1:8000",
            mode="local_lab",
        )
        self.assertEqual(c[0]["url"], "http://10.0.2.2:8000")
        self.assertEqual(c[0]["source"], "cli")

    def test_env_server_used(self) -> None:
        c = candidate_server_urls(env_server="http://127.0.0.1:8000", mode="local_lab")
        self.assertTrue(any(x["source"] == "env" for x in c))

    def test_qemu_host_url_allowed(self) -> None:
        ok, err = validate_server_url("http://10.0.2.2:8000")
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertTrue(is_private_or_local_dev_server_url("http://10.0.2.2:8000"))

    def test_public_domain_blocked(self) -> None:
        ok, err = validate_server_url("https://example.com")
        self.assertFalse(ok)
        self.assertEqual(err, "public_domain_blocked")

    def test_public_rescue_no_qemu_fallback_candidates(self) -> None:
        c = candidate_server_urls(
            env_server="http://127.0.0.1:8000",
            mode="public_rescue",
            qemu_host_fallback=True,
        )
        self.assertFalse(any(x["source"] == "qemu_user_nat_fallback" for x in c))

    def test_local_lab_qemu_fallback_candidate(self) -> None:
        c = candidate_server_urls(
            env_server="http://127.0.0.1:8000",
            mode="local_lab",
            qemu_host_fallback=True,
            qemu_host_url=DEFAULT_QEMU_HOST_URL,
        )
        self.assertTrue(any(x["url"] == DEFAULT_QEMU_HOST_URL for x in c))

    def test_resolve_prefers_reachable_10022_over_127(self) -> None:
        def fake_health(url: str, *, timeout: float = 5.0) -> dict:
            if "10.0.2.2" in url:
                return {"ok": True, "health": {"enabled": True, "mode": "local_lab"}}
            return {"ok": False, "health": {}, "error": "refused"}

        with patch("devserver_agent.server_url.health_check", side_effect=fake_health):
            with patch(
                "devserver_agent.server_url.validate_server_health",
                side_effect=lambda h, m: {"ok": h.get("ok", False), "errors": []},
            ):
                r = resolve_dev_server_url(
                    env_server="http://127.0.0.1:8000",
                    mode="local_lab",
                    qemu_host_fallback=True,
                    probe=True,
                )
        self.assertEqual(r["selected_url"], "http://10.0.2.2:8000")
        self.assertEqual(r["source"], "qemu_user_nat_fallback")

    def test_resolve_all_fail_warning(self) -> None:
        with patch("devserver_agent.server_url._probe_health", return_value=False):
            r = resolve_dev_server_url(
                env_server="http://127.0.0.1:8000",
                mode="local_lab",
                qemu_host_fallback=True,
                probe=True,
            )
        self.assertIsNone(r["selected_url"])
        self.assertIn("no_reachable_dev_server_candidate", r["warnings"])

    def test_token_not_in_resolve_output(self) -> None:
        with patch.dict(
            os.environ,
            {"SETUPHELFER_DEV_AGENT_TOKEN": "secret-token-xyz"},
            clear=False,
        ):
            r = resolve_dev_server_url(env_server="http://127.0.0.1:8000", probe=False)
        text = str(r)
        self.assertNotIn("secret-token", text)

    def test_qemu_wrapper_pid_path_not_root(self) -> None:
        text = (
            __import__("pathlib").Path(__file__).resolve().parent.parent.parent
            / "scripts/rescue-live/run-qemu-developer-iso-smoke.sh"
        ).read_text(encoding="utf-8")
        self.assertIn("qemu_gtk_pid.txt", text)
        self.assertNotIn('>"/qemu_gtk_pid.txt"', text)
        self.assertNotIn("> /qemu_gtk_pid.txt", text)
        self.assertIn("WRAPPER_WARNING", text)


if __name__ == "__main__":
    unittest.main()
