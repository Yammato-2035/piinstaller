"""RS-001 stick acceptance tests — no USB writes."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.rescue_fat32_esp_usb_writer import generate_fat32_esp_grub_cfg
from rescue.rescue_grub_branding import stage_grub_theme_to_fat32_staging
from rescue.rescue_stick_acceptance import (
    ACCEPTANCE_EXIT_BLOCKED,
    ACCEPTANCE_EXIT_GRUB_BRANDING,
    ACCEPTANCE_EXIT_SQUASHFS_HASH,
    ACCEPTANCE_EXIT_TARGET_INVALID,
    evaluate_fat32_layout,
    evaluate_grub_branding_on_mount,
    evaluate_squashfs_hash,
    evaluate_stick_acceptance,
    target_blocked,
)

REPO = Path(__file__).resolve().parents[2]
EXPECTED_SHA = "a3e58964ffffe032fd7e543e5e28bd64156981347647a0ba9208101cb9d7726d"
SQUASHFS = REPO / "build/rescue/filesystem.squashfs.repacked-1.7.10.1"


class Rs001StickAcceptanceTests(unittest.TestCase):
    def test_target_blocked_for_sda(self) -> None:
        blocked, errors = target_blocked("/dev/sda")
        self.assertTrue(blocked)
        self.assertTrue(errors)

    def test_layout_detects_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "boot/grub").mkdir(parents=True)
            (root / "boot/grub/grub.cfg").write_text('menuentry "Setuphelfer Rettung starten" {}', encoding="utf-8")
            layout = evaluate_fat32_layout(root)
            self.assertFalse(layout["layout_ok"])
            self.assertIn("live/filesystem.squashfs", layout["missing_files"])

    def test_squashfs_hash_mismatch(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            path = Path(tmp.name)
            path.write_bytes(b"x")
            result = evaluate_squashfs_hash(path, EXPECTED_SHA)
            self.assertFalse(result["hash_ok"])

    def test_grub_branding_fails_without_theme_on_mount(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = generate_fat32_esp_grub_cfg()
            (root / "boot/grub").mkdir(parents=True)
            (root / "boot/grub/grub.cfg").write_text(cfg, encoding="utf-8")
            branding = evaluate_grub_branding_on_mount(root)
            self.assertFalse(branding["branding_ok"])
            self.assertIn("GRUB_THEME_TXT_MISSING", branding["errors"])

    def test_grub_branding_passes_when_staged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage_grub_theme_to_fat32_staging(root, REPO)
            cfg = generate_fat32_esp_grub_cfg()
            (root / "boot/grub/grub.cfg").write_text(cfg, encoding="utf-8")
            branding = evaluate_grub_branding_on_mount(root)
            self.assertTrue(branding["branding_ok"], branding["errors"])

    def test_hardware_retest_not_allowed_when_branding_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in (
                "EFI/BOOT/BOOTX64.EFI",
                "live/vmlinuz",
                "live/initrd.img",
                "setuphelfer/rescue/boot-branding.txt",
            ):
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b"x" * 64)
            sq = root / "live/filesystem.squashfs"
            sq.write_bytes(b"test-payload")
            expected = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
            (root / "boot/grub").mkdir(parents=True, exist_ok=True)
            (root / "boot/grub/grub.cfg").write_text(
                'search --label SETUPHELFER\nmenuentry "Setuphelfer Rettung starten" {}',
                encoding="utf-8",
            )
            with mock.patch(
                "rescue.rescue_stick_acceptance.evaluate_squashfs_content",
                return_value={"content_ok": True, "errors": []},
            ):
                with mock.patch(
                    "rescue.rescue_stick_acceptance.evaluate_launcher_contracts_from_squashfs",
                    return_value={
                        "launcher_contract_ok": True,
                        "fallback_tui_contract_ok": True,
                        "network_menu_contract_ok": True,
                        "errors": [],
                    },
                ):
                    with mock.patch(
                        "rescue.rescue_stick_acceptance.evaluate_verify_probe",
                        return_value={"ok": True, "errors": []},
                    ):
                        result = evaluate_stick_acceptance(
                            mount_root=root,
                            target_device="/dev/sdb",
                            target_partition="/dev/sdb1",
                            expected_squashfs_sha256=expected,
                        )
            self.assertFalse(result.hardware_retest_allowed)
            self.assertEqual(result.rs001_status, "yellow")
            self.assertFalse(result.grub_branding_contract_ok)

    def test_acceptance_json_shape(self) -> None:
        payload = evaluate_stick_acceptance(
            mount_root=REPO,
            target_device="/dev/sda",
            target_partition="/dev/sda1",
            expected_squashfs_sha256=EXPECTED_SHA,
        ).to_json()
        for key in (
            "acceptance_status",
            "fat32_layout_ok",
            "squashfs_hash_ok",
            "hardware_retest_allowed",
            "rs001_status",
        ):
            self.assertIn(key, payload)
        self.assertEqual(payload["rs001_status"], "yellow")

    def test_no_write_commands_in_acceptance_script(self) -> None:
        text = (REPO / "scripts/rescue-live/check-rs001-stick-acceptance.sh").read_text(encoding="utf-8")
        for forbidden in ("dd ", "mkfs", "wipefs", "sgdisk", "payload-update", "execute-update"):
            self.assertNotIn(forbidden, text)


class Rs001StickAcceptanceIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(Path("/dev/sdb").exists(), "stick /dev/sdb not present")
    def test_live_stick_readonly_acceptance_runs(self) -> None:
        import subprocess

        proc = subprocess.run(
            [
                str(REPO / "scripts/rescue-live/check-rs001-stick-acceptance.sh"),
                "--target",
                "/dev/sdb",
                "--expected-squashfs-sha256",
                EXPECTED_SHA,
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO),
            env={**dict(__import__("os").environ), "PYTHONPATH": str(REPO / "backend")},
            timeout=300,
        )
        self.assertTrue(proc.stdout.strip().startswith("{"), proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["rs001_status"], "yellow")
        if data.get("acceptance_status") == "ok":
            self.assertTrue(data["hardware_retest_allowed"])
            self.assertEqual(proc.returncode, 0)
        else:
            self.assertFalse(data["hardware_retest_allowed"])
            self.assertIn(proc.returncode, (0, 14, 15, 16, 17, 20))
        self.assertTrue(data["squashfs_hash_ok"])


if __name__ == "__main__":
    unittest.main()
