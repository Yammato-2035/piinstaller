"""Graphical rescue boot menu assets — static validation (no ISO/USB)."""

from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path

from rescue.rescue_graphical_assets import (
    FORBIDDEN_BRAND_PHRASES,
    build_asset_manifest,
    ui_text_has_forbidden_brand,
    validate_rescue_menu_items,
)

REPO = Path(__file__).resolve().parents[2]
RESCUE_SRC = REPO / "frontend/src/rescue"
ASSETS = REPO / "assets/rescue"
MENU_ITEMS_TS = RESCUE_SRC / "rescueMenuItems.ts"
STAGE_SCRIPT = REPO / "scripts/rescue-live/stage-rescue-graphical-assets.sh"
PREPARE = REPO / "scripts/rescue-live/prepare-controlled-live-build-tree.sh"
MANIFEST = REPO / "build/rescue/asset-manifest.json"


def _menu_item_blocks(ts: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for match in re.finditer(r"\{\s*id:\s*'([^']+)'.*?\n\s*\},", ts, re.DOTALL):
        blocks[match.group(1)] = match.group(0)
    return blocks


def _ts_item_to_manifest(block: str) -> dict[str, object]:
    def pick(name: str, default: object = None) -> object:
        m = re.search(rf"{name}:\s*'([^']*)'", block)
        if m:
            return m.group(1)
        m = re.search(rf"{name}:\s*(true|false)", block)
        if m:
            return m.group(1) == "true"
        return default

    return {
        "id": pick("id"),
        "titleKey": pick("titleKey"),
        "subtitleKey": pick("subtitleKey"),
        "actionTarget": pick("actionTarget"),
        "safetyLevel": pick("safetyLevel"),
        "write_risk": pick("writeRisk"),
        "enabled": pick("enabled", False),
        "requires_confirmation": pick("requiresConfirmation", False),
    }


class RescueGraphicalAssetsTests(unittest.TestCase):
    def test_canonical_assets_exist_and_readable(self) -> None:
        manifest = build_asset_manifest(REPO)
        self.assertTrue(manifest["complete"], manifest.get("missing_required"))
        for entry in manifest["entries"]:
            self.assertTrue(entry["readable"], entry["source_path"])
            self.assertGreater(entry["size_bytes"], 64)
            self.assertRegex(entry["sha256"], r"^[a-f0-9]{64}$")

    def test_i18n_json_valid_and_keys_present(self) -> None:
        required = (
            "menu.system_analyze.title",
            "menu.backup_create.title",
            "menu.backup_verify.title",
            "menu.restore.title",
            "menu.malware_scan.title",
            "menu.cloudserver_manage.title",
            "menu.settings.title",
            "footer.help",
            "footer.language",
            "footer.select",
        )

        def get_path(data: dict, key: str) -> str:
            cur: object = data
            for part in key.split("."):
                self.assertIsInstance(cur, dict)
                cur = cur[part]  # type: ignore[index]
            self.assertIsInstance(cur, str)
            return str(cur)

        for loc in ("de", "en"):
            data = json.loads((RESCUE_SRC / "i18n" / f"{loc}.json").read_text(encoding="utf-8"))
            self.assertEqual(data["title"], "Setuphelfer")
            for key in required:
                get_path(data, key)

    def test_no_forbidden_brand_in_new_rescue_ui(self) -> None:
        scan_paths = [
            RESCUE_SRC / "RescueStartCenter.tsx",
            RESCUE_SRC / "RescueApp.tsx",
            RESCUE_SRC / "rescueMenuItems.ts",
            RESCUE_SRC / "i18n/de.json",
            RESCUE_SRC / "i18n/en.json",
        ]
        for path in scan_paths:
            text = path.read_text(encoding="utf-8")
            hits = ui_text_has_forbidden_brand(text)
            self.assertEqual(hits, [], f"{path}: {hits}")

    def test_menu_items_no_direct_write_actions(self) -> None:
        ts = MENU_ITEMS_TS.read_text(encoding="utf-8")
        blocks = _menu_item_blocks(ts)
        self.assertEqual(
            set(blocks),
            {
                "system_analyze",
                "backup_create",
                "backup_verify",
                "restore",
                "malware_scan",
                "cloudserver_manage",
                "settings",
            },
        )
        items = [_ts_item_to_manifest(block) for block in blocks.values()]
        errors = validate_rescue_menu_items(items)
        self.assertEqual(errors, [], errors)
        for high_risk in ("backup_create", "restore", "cloudserver_manage"):
            self.assertIn("enabled: false", blocks[high_risk], high_risk)

    def test_stage_script_and_prepare_hook_present(self) -> None:
        self.assertTrue(STAGE_SCRIPT.is_file())
        proc = subprocess.run(["bash", "-n", str(STAGE_SCRIPT)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        prep = PREPARE.read_text(encoding="utf-8")
        self.assertIn("write_rescue_graphical_assets_overlay", prep)
        self.assertIn("stage-rescue-graphical-assets.sh", prep)

    def test_asset_manifest_file_when_staged(self) -> None:
        if not MANIFEST.is_file():
            self.skipTest("asset-manifest.json not generated yet — run stage-rescue-graphical-assets.sh")
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertTrue(data.get("complete"))
        self.assertGreaterEqual(len(data.get("entries", [])), 5)

    def test_grub_theme_stub_documents_fallback(self) -> None:
        theme = (REPO / "build/rescue/theme/grub/setuphelfer/theme.txt").read_text(encoding="utf-8")
        self.assertIn("Setuphelfer", theme)
        self.assertIn("desktop-image", theme)
        self.assertIn("Fallback", theme)


if __name__ == "__main__":
    unittest.main()
