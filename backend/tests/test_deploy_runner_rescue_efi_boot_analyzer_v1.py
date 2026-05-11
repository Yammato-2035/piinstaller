from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_efi_boot_analyzer import build_rescue_efi_boot_analysis

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_DISC = _H / "rescue_storage_discovery_result.json"
_MNT = _H / "readonly_mount_result.json"
_OUT = _H / "rescue_efi_boot_analysis.json"


class DeployRunnerRescueEfiBootAnalyzerV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._backs = {p: p.read_bytes() if p.exists() else None for p in (_DISC, _MNT, _OUT)}
        for p in (_DISC, _MNT, _OUT):
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def test_grub_missing_warning(self) -> None:
        _DISC.write_text(
            json.dumps({"lsblk_rows": [{"name": "p1", "fstype": "vfat", "label": "EFI", "uuid": "u1"}]}),
            encoding="utf-8",
        )
        _MNT.write_text(
            json.dumps({"evaluation": {"readonly_mount_eval_status": "ok", "readonly_enforced": True}}),
            encoding="utf-8",
        )
        r = build_rescue_efi_boot_analysis(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_efi_boot_analysis_status"), "ok")
        body = r.get("rescue_efi_boot_analysis") or {}
        self.assertTrue(body.get("efi_present"))
        self.assertFalse(body.get("grub_configuration_hints"))
        self.assertIn("RESCUE_EFI_GRUB_NOT_DETECTED_IN_HINTS", r.get("warnings") or [])

    def test_uuid_conflict_fstab_hint(self) -> None:
        _DISC.write_text(
            json.dumps(
                {
                    "lsblk_rows": [{"name": "p1", "fstype": "vfat", "label": "EFI", "uuid": "dup"}],
                    "classification": {"uuid_conflicts": ["dup"], "flags": {}, "row_count": 1},
                }
            ),
            encoding="utf-8",
        )
        _MNT.write_text(
            json.dumps({"evaluation": {"readonly_mount_eval_status": "ok", "readonly_enforced": True}}),
            encoding="utf-8",
        )
        r = build_rescue_efi_boot_analysis(explicit_overwrite=True)
        body = r.get("rescue_efi_boot_analysis") or {}
        self.assertTrue(body.get("fstab_problems_hint"))
        self.assertEqual(body.get("uuid_conflicts"), ["dup"])
