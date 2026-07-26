"""Contract tests for G513QM hybrid graphics STRICT rebuild."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from backend.core import rescue_install_assistant_grub as grub

ROOT = Path(__file__).resolve().parents[2]


class G513qmHybridContractTests(unittest.TestCase):
    def test_contract_json_forbids_windows_write(self) -> None:
        p = ROOT / "config/hardware/asus/g513qm-hybrid-graphics.json"
        data = json.loads(p.read_text())
        self.assertEqual(data["display_gpu_preference"], "amd_igpu")
        self.assertFalse(data["windows_nvme_write_allowed"])
        self.assertFalse(data["automatic_install_allowed"])
        self.assertEqual(data["pci_devices_status"], "pending_physical_capture")
        self.assertEqual(data["pci_devices"], [])

    def test_profiles_standard_has_no_nomodeset(self) -> None:
        p = ROOT / "config/rescue/g513qm_graphics_profiles.json"
        data = json.loads(p.read_text())
        by_id = {x["id"]: x for x in data["profiles"]}
        self.assertFalse(by_id["g513qm_hybrid_auto"]["nomodeset"])
        self.assertFalse(by_id["g513qm_hybrid_auto"]["blacklist_amdgpu"])
        self.assertTrue(by_id["g513qm_basic_emergency"]["nomodeset"])
        self.assertTrue(by_id["g513qm_basic_emergency"].get("emergency"))

    def test_grub_default_is_hybrid_auto(self) -> None:
        cfg = grub.generate_gabriel_install_grub_cfg()
        v = grub.validate_gabriel_install_grub(cfg)
        self.assertTrue(v["ok"], v)
        self.assertEqual(v["checks"]["first_entry"], grub.MINT_CASPER_RESCUE_TITLE)
        self.assertTrue(v["checks"]["first_is_basic_emergency"])
        self.assertIn("systemd.unit=rescue.target", cfg)
        import re

        m = re.search(
            rf'menuentry "{re.escape(grub.MINT_CASPER_RESCUE_TITLE)}" \{{(.*?)^\}}',
            cfg,
            re.S | re.M,
        )
        self.assertIsNotNone(m)
        assert m is not None
        self.assertIn("nomodeset", m.group(1))
        # Hybrid remains present but not default
        h = re.search(
            rf'menuentry "{re.escape(grub.MINT_CASPER_HYBRID_TITLE)}" \{{(.*?)^\}}',
            cfg,
            re.S | re.M,
        )
        self.assertIsNotNone(h)
        assert h is not None
        self.assertNotIn("nomodeset", h.group(1))
        self.assertIn("systemd.unit=rescue.target", h.group(1))

    def test_installer_script_refuses_ubiquity_without_modes(self) -> None:
        script = (
            ROOT
            / "scripts/rescue/rog-pack-g513qm/scripts/install-from-rescue.sh"
        ).read_text()
        self.assertIn("--mode ubiquity", script)
        self.assertIn("installer_preflight", script)
        self.assertIn("nomodeset_active", script)
        self.assertIn("openvt -s", script)  # must document avoidance — check refusal path
        self.assertIn("Do NOT openvt -s", script)
        self.assertIn("queued_offline", script)
        self.assertNotIn("startx /usr/bin/ubiquity", script)

    def test_nvidia_pack_single_abi_580(self) -> None:
        man = ROOT / "scripts/rescue/rog-pack-g513qm/MANIFEST.json"
        data = json.loads(man.read_text())
        debs = [
            f["path"]
            for f in data["files"]
            if f["path"].startswith("debs/nvidia/") and f["path"].endswith(".deb")
        ]
        # No concurrent 535/570 branches mixed with 580 libs
        bad = [d for d in debs if "nvidia-driver-535" in d or "libnvidia-gl-570" in d]
        self.assertEqual(bad, [])
        has_580 = any("580" in d for d in debs)
        self.assertTrue(has_580)


if __name__ == "__main__":
    unittest.main()
