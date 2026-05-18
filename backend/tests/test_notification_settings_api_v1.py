"""API tests for /api/settings/notifications/email (no real SMTP, no secrets in responses)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.notification_settings import (
    ENV_KEYS,
    build_public_settings,
    classify_smtp_error,
    merge_settings_payload,
    notification_env_path,
    parse_env_file,
    run_notification_test_email,
    save_notification_settings,
    serialize_env_lines,
)


class TestNotificationSettingsCoreV1(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.config_dir = Path(self._tmpdir.name) / "etc" / "setuphelfer"
        self.state_dir = Path(self._tmpdir.name) / "var" / "lib" / "setuphelfer"
        self.config_dir.mkdir(parents=True)
        self.state_dir.mkdir(parents=True)

    def _env_path(self) -> Path:
        return self.config_dir / "notification.env"

    def test_get_public_never_returns_password(self) -> None:
        env_path = self.config_dir / "notification.env"
        env_path.write_text(
            serialize_env_lines(
                {
                    ENV_KEYS["enabled"]: "true",
                    ENV_KEYS["email_to"]: "user@example.com",
                    ENV_KEYS["email_from"]: "user@example.com",
                    ENV_KEYS["smtp_host"]: "smtp.gmail.com",
                    ENV_KEYS["smtp_port"]: "587",
                    ENV_KEYS["smtp_username"]: "user@example.com",
                    ENV_KEYS["smtp_password"]: "secret-app-password",
                    ENV_KEYS["smtp_starttls"]: "true",
                    ENV_KEYS["on_backup_success"]: "true",
                    ENV_KEYS["on_backup_failure"]: "false",
                }
            ),
            encoding="utf-8",
        )
        with (
            patch("core.notification_settings.get_config_dir", return_value=self.config_dir),
            patch("core.notification_settings.get_state_dir", return_value=self.state_dir),
            patch("core.notification_settings.notification_env_path", return_value=self._env_path()),
        ):
            pub = build_public_settings()
        raw = json.dumps(pub)
        self.assertNotIn("secret-app-password", raw)
        self.assertNotIn('"smtp_password":', raw)
        self.assertNotIn("smtp_password=", raw)
        self.assertTrue(pub["smtp_password_set"])
        self.assertEqual(pub["email_to"], "user@example.com")

    def test_merge_keeps_password_when_empty_string(self) -> None:
        env_path = self.config_dir / "notification.env"
        env_path.write_text(
            f"{ENV_KEYS['smtp_password']}=keep-me\n",
            encoding="utf-8",
        )
        with patch("core.notification_settings.notification_env_path", return_value=self._env_path()):
            env_map, errs = merge_settings_payload({"smtp_password": "   "})
        self.assertEqual(errs, [])
        self.assertEqual(env_map[ENV_KEYS["smtp_password"]], "keep-me")

    def test_merge_keeps_password_when_omitted(self) -> None:
        env_path = self.config_dir / "notification.env"
        env_path.write_text(
            f"{ENV_KEYS['smtp_password']}=keep-me\n{ENV_KEYS['email_to']}=a@b.com\n",
            encoding="utf-8",
        )
        with patch("core.notification_settings.notification_env_path", return_value=self._env_path()):
            env_map, errs = merge_settings_payload({"email_to": "a@b.com"})
        self.assertEqual(errs, [])
        self.assertEqual(env_map[ENV_KEYS["smtp_password"]], "keep-me")

    def test_merge_overwrites_password_when_set(self) -> None:
        with patch("core.notification_settings.notification_env_path", return_value=self._env_path()):
            env_map, errs = merge_settings_payload(
                {
                    "email_to": "a@b.com",
                    "email_from": "a@b.com",
                    "smtp_password": "new-secret",
                }
            )
        self.assertEqual(env_map[ENV_KEYS["smtp_password"]], "new-secret")

    def test_invalid_email_rejected(self) -> None:
        with patch("core.notification_settings.notification_env_path", return_value=self._env_path()):
            _, errs = merge_settings_payload(
                {"enabled": True, "email_to": "not-an-email", "email_from": "a@b.com"}
            )
        self.assertTrue(any("email" in e.lower() for e in errs))

    def test_invalid_port_rejected(self) -> None:
        with patch("core.notification_settings.notification_env_path", return_value=self._env_path()):
            _, errs = merge_settings_payload({"smtp_port": 99999})
        self.assertTrue(errs)

    def test_classify_smtp_535(self) -> None:
        self.assertEqual(classify_smtp_error("535 Username and Password not accepted"), "smtp_auth_failed")

    def test_save_direct_write(self) -> None:
        with (
            patch("core.notification_settings.get_config_dir", return_value=self.config_dir),
            patch("core.notification_settings.get_state_dir", return_value=self.state_dir),
            patch("core.notification_settings.notification_env_path", return_value=self._env_path()),
        ):
            result = save_notification_settings(
                {
                    "enabled": True,
                    "email_to": "u@example.com",
                    "email_from": "u@example.com",
                    "smtp_host": "smtp.gmail.com",
                    "smtp_port": 587,
                    "smtp_username": "u@example.com",
                    "smtp_password": "pw",
                }
            )
        self.assertEqual(result["status"], "success")
        self.assertEqual(parse_env_file(self._env_path())[ENV_KEYS["smtp_password"]], "pw")

    def test_test_email_mock_smtp(self) -> None:
        env_path = self.config_dir / "notification.env"
        env_path.write_text(
            serialize_env_lines(
                {
                    ENV_KEYS["enabled"]: "true",
                    ENV_KEYS["email_to"]: "u@example.com",
                    ENV_KEYS["email_from"]: "u@example.com",
                    ENV_KEYS["smtp_host"]: "smtp.gmail.com",
                    ENV_KEYS["smtp_port"]: "587",
                    ENV_KEYS["smtp_username"]: "u@example.com",
                    ENV_KEYS["smtp_password"]: "pw",
                    ENV_KEYS["smtp_starttls"]: "true",
                    ENV_KEYS["on_backup_success"]: "true",
                    ENV_KEYS["on_backup_failure"]: "false",
                }
            ),
            encoding="utf-8",
        )

        def _mock_send(cfg, msg):  # noqa: ARG001
            return None

        with (
            patch("core.notification_settings.get_config_dir", return_value=self.config_dir),
            patch("core.notification_settings.get_state_dir", return_value=self.state_dir),
            patch("core.notification_settings.notification_env_path", return_value=self._env_path()),
        ):
            out = run_notification_test_email(smtp_send=_mock_send)
        self.assertEqual(out["status"], "sent")
        self.assertNotIn("pw", json.dumps(out))

    def test_smtp_error_no_password_in_message(self) -> None:
        env_path = self.config_dir / "notification.env"
        env_path.write_text(
            serialize_env_lines(
                {
                    ENV_KEYS["enabled"]: "true",
                    ENV_KEYS["email_to"]: "u@example.com",
                    ENV_KEYS["email_from"]: "u@example.com",
                    ENV_KEYS["smtp_host"]: "smtp.gmail.com",
                    ENV_KEYS["smtp_port"]: "587",
                    ENV_KEYS["smtp_username"]: "u@example.com",
                    ENV_KEYS["smtp_password"]: "pw",
                    ENV_KEYS["smtp_starttls"]: "true",
                    ENV_KEYS["on_backup_success"]: "true",
                    ENV_KEYS["on_backup_failure"]: "false",
                }
            ),
            encoding="utf-8",
        )

        def _fail(cfg, msg):  # noqa: ARG001
            raise Exception("535 Username and Password not accepted")

        with (
            patch("core.notification_settings.get_config_dir", return_value=self.config_dir),
            patch("core.notification_settings.get_state_dir", return_value=self.state_dir),
            patch("core.notification_settings.notification_env_path", return_value=self._env_path()),
        ):
            out = run_notification_test_email(smtp_send=_fail)
        self.assertEqual(out["status"], "failed")
        self.assertEqual(out["error_class"], "smtp_auth_failed")
        self.assertNotIn("pw", str(out.get("message", "")))


if __name__ == "__main__":
    unittest.main()
