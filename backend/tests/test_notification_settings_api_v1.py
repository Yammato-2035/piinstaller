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
    config_from_env_map,
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

    def test_classify_smtp_tls(self) -> None:
        self.assertEqual(classify_smtp_error("SSL: WRONG_VERSION_NUMBER"), "smtp_tls_failed")

    def test_port_465_without_security_defaults_ssl_in_config(self) -> None:
        env_map = {
            ENV_KEYS["smtp_port"]: "465",
            ENV_KEYS["smtp_starttls"]: "false",
        }
        cfg = config_from_env_map(env_map)
        self.assertEqual(cfg.smtp_security, "ssl")
        self.assertFalse(cfg.smtp_starttls)

    def test_merge_glienke_ssl_465_valid(self) -> None:
        with patch("core.notification_settings.notification_env_path", return_value=self._env_path()):
            env_map, errs = merge_settings_payload(
                {
                    "smtp_host": "mail.glienke.de",
                    "smtp_port": 465,
                    "smtp_security": "ssl",
                    "smtp_starttls": False,
                    "email_to": "volker@example.com",
                    "email_from": "volker@example.com",
                }
            )
        self.assertEqual(errs, [])
        self.assertEqual(env_map[ENV_KEYS["smtp_security"]], "ssl")
        self.assertEqual(env_map[ENV_KEYS["smtp_port"]], "465")
        self.assertEqual(env_map[ENV_KEYS["smtp_starttls"]], "false")

    def test_merge_port_465_starttls_rejected(self) -> None:
        with patch("core.notification_settings.notification_env_path", return_value=self._env_path()):
            _, errs = merge_settings_payload(
                {"smtp_port": 465, "smtp_security": "starttls", "email_to": "a@b.com", "email_from": "a@b.com"}
            )
        self.assertTrue(any("465" in e for e in errs))

    def test_build_public_includes_smtp_security(self) -> None:
        env_path = self.config_dir / "notification.env"
        env_path.write_text(
            serialize_env_lines(
                {
                    ENV_KEYS["enabled"]: "true",
                    ENV_KEYS["email_to"]: "u@example.com",
                    ENV_KEYS["email_from"]: "u@example.com",
                    ENV_KEYS["smtp_host"]: "smtp.example.com",
                    ENV_KEYS["smtp_port"]: "465",
                    ENV_KEYS["smtp_username"]: "u@example.com",
                    ENV_KEYS["smtp_password"]: "pw",
                    ENV_KEYS["smtp_security"]: "ssl",
                    ENV_KEYS["smtp_starttls"]: "false",
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
        self.assertEqual(pub["smtp_security"], "ssl")
        raw = json.dumps(pub)
        self.assertNotIn("pw", raw)

    def test_can_write_when_parent_writable_but_file_readonly(self) -> None:
        env_path = self.config_dir / "notification.env"
        env_path.write_text(f"{ENV_KEYS['email_to']}=a@b.com\n", encoding="utf-8")

        def _access(path, mode):  # noqa: ARG001
            if path == env_path:
                return False
            if path == env_path.parent and mode == os.W_OK:
                return True
            return os.access(path, mode)

        with (
            patch("core.notification_settings.notification_env_path", return_value=env_path),
            patch("os.access", side_effect=_access),
        ):
            from core.notification_settings import can_write_notification_env_direct

            self.assertTrue(can_write_notification_env_direct())

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

    def test_parse_env_file_invalid_utf8(self) -> None:
        env_path = self.config_dir / "notification.env"
        env_path.write_bytes(b"g\xff\xffbage\nSETUPHELFER_NOTIFY_EMAIL_TO=a@b.com\n")
        parsed = parse_env_file(env_path)
        self.assertEqual(parsed.get(ENV_KEYS["email_to"]), "a@b.com")

    def test_parse_env_file_empty(self) -> None:
        env_path = self.config_dir / "notification.env"
        env_path.write_text("", encoding="utf-8")
        self.assertEqual(parse_env_file(env_path), {})

    def test_parse_env_file_skips_bad_lines(self) -> None:
        env_path = self.config_dir / "notification.env"
        env_path.write_text("no_equals_line\nSETUPHELFER_NOTIFY_EMAIL_TO=a@b.com\n", encoding="utf-8")
        self.assertEqual(parse_env_file(env_path).get(ENV_KEYS["email_to"]), "a@b.com")

    def test_build_public_never_raises_on_broken_config(self) -> None:
        with (
            patch("core.notification_settings.get_config_dir", return_value=self.config_dir),
            patch("core.notification_settings.get_state_dir", return_value=self.state_dir),
            patch("core.notification_settings.notification_env_path", return_value=self._env_path()),
            patch(
                "core.notification_settings._build_public_settings_impl",
                side_effect=RuntimeError("simulated"),
            ),
        ):
            pub = build_public_settings()
        self.assertEqual(pub["last_test_error_class"], "settings_read_failed")
        self.assertFalse(pub["configured"])

    def test_save_write_oserror_json_no_secret(self) -> None:
        with (
            patch("core.notification_settings.get_config_dir", return_value=self.config_dir),
            patch("core.notification_settings.get_state_dir", return_value=self.state_dir),
            patch("core.notification_settings.notification_env_path", return_value=self._env_path()),
            patch("core.notification_settings.can_write_notification_env_direct", return_value=True),
            patch(
                "core.notification_settings.write_notification_env_atomic",
                side_effect=PermissionError("denied"),
            ),
        ):
            result = save_notification_settings(
                {
                    "enabled": True,
                    "email_to": "u@example.com",
                    "email_from": "u@example.com",
                    "smtp_host": "smtp.gmail.com",
                    "smtp_port": 587,
                    "smtp_username": "u@example.com",
                    "smtp_password": "secret123",
                }
            )
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["write_status"], "write_failed")
        self.assertNotIn("secret123", str(result))
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
