"""Contract tests for G513QM Kernel A/B/C control + Control-C diagnostic path."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from backend.core import rescue_install_assistant_grub as grub

ROOT = Path(__file__).resolve().parents[2]


class G513qmKernelAbcContractTests(unittest.TestCase):
    def test_control_isos_marked_unmodified(self) -> None:
        p = ROOT / "docs/evidence/rescue/g513qm-kernel-abc/control_matrix.json"
        data = json.loads(p.read_text())
        self.assertFalse(data["control_a"]["modified"])
        self.assertFalse(data["control_b"]["modified"])
        self.assertTrue(data["control_c"]["setuphelfer_modified"])
        self.assertFalse(data["control_c"]["uses_rescue_target"])

    def test_verify_script_blocks_bad_checksum(self) -> None:
        script = (
            ROOT / "scripts/rescue/g513qm-kernel-abc/verify-control-iso.sh"
        ).read_text()
        self.assertIn("checksum_failed", script)
        self.assertIn("signature_failed", script)
        self.assertIn("BLOCKED", script)
        self.assertIn("exit 19", script)
        self.assertIn("exit 17", script)

    def test_control_c_not_rescue_target(self) -> None:
        cfg = grub.generate_gabriel_install_grub_cfg()
        m = re.search(
            rf'menuentry "{re.escape(grub.MINT_CONTROL_C1_TITLE)}" \{{(.*?)^\}}',
            cfg,
            re.S | re.M,
        )
        self.assertIsNotNone(m)
        assert m is not None
        body = m.group(1)
        self.assertNotIn("systemd.unit=rescue.target", body)
        self.assertIn("systemd.unit=multi-user.target", body)
        self.assertIn("systemd.debug-shell=1", body)

    def test_debug_shell_lab_only_not_product_default(self) -> None:
        cfg = grub.generate_gabriel_install_grub_cfg()
        first = re.search(r'menuentry "([^"]+)"', cfg)
        self.assertIsNotNone(first)
        assert first is not None
        self.assertEqual(first.group(1), grub.MINT_CASPER_RESCUE_TITLE)
        # Product emergency still uses rescue; Control C is not default
        self.assertNotEqual(first.group(1), grub.MINT_CONTROL_C1_TITLE)

    def test_control_c_blacklists_amdgpu_and_nvidia(self) -> None:
        body = grub._profile_cmdline("g513qm_control_c1_standard")
        self.assertIn("amdgpu", body)
        self.assertIn("nvidia_drm", body)
        self.assertIn("nouveau", body)
        self.assertIn("modprobe.blacklist=", body)
        self.assertNotIn("nomodeset", body)

    def test_single_param_profiles_not_combined(self) -> None:
        c2 = grub._profile_cmdline("g513qm_control_c2_dc0")
        c3 = grub._profile_cmdline("g513qm_control_c3_aspm0")
        c4 = grub._profile_cmdline("g513qm_control_c4_recovery")
        self.assertIn("amdgpu.dc=0", c2)
        self.assertNotIn("amdgpu.aspm=0", c2)
        self.assertNotIn("amdgpu.gpu_recovery=1", c2)
        self.assertIn("amdgpu.aspm=0", c3)
        self.assertNotIn("amdgpu.dc=0", c3)
        self.assertIn("amdgpu.gpu_recovery=1", c4)
        self.assertNotIn("amdgpu.dc=0", c4)

    def test_gpu_wrapper_commands_present(self) -> None:
        script = (
            ROOT / "scripts/rescue/rog-pack-g513qm/scripts/setuphelfer-gpu"
        ).read_text()
        for cmd in (
            "status",
            "load-amdgpu",
            "unload-amdgpu",
            "capture",
            "finalize",
            "network-status",
            "shutdown",
        ):
            self.assertIn(cmd, script)
        self.assertIn("no nvme write", script)
        self.assertIn("no installer", script)
        self.assertIn("modprobe amdgpu", script)

    def test_netconsole_receiver_no_overwrite(self) -> None:
        script = (
            ROOT / "scripts/rescue/g513qm-netconsole-receiver.sh"
        ).read_text()
        self.assertIn("Refusing to overwrite", script)
        self.assertIn("g513qm-netconsole", script)

    def test_profiles_json_control_c_flags(self) -> None:
        data = json.loads(
            (ROOT / "config/rescue/g513qm_graphics_profiles.json").read_text()
        )
        by_id = {x["id"]: x for x in data["profiles"]}
        c1 = by_id["g513qm_control_c1_standard"]
        self.assertFalse(c1["uses_rescue_target"])
        self.assertEqual(c1["systemd_unit"], "multi-user.target")
        self.assertTrue(c1["lab_only"])
        self.assertFalse(c1["auto_installer"])
        self.assertFalse(c1["auto_desktop"])
        self.assertEqual(by_id["g513qm_control_c2_dc0"]["amdgpu_extra_params"], ["amdgpu.dc=0"])

    def test_decision_forbids_hardware_defect_confirmed_auto(self) -> None:
        data = json.loads(
            (
                ROOT
                / "docs/evidence/rescue/g513qm-kernel-abc/control_result_decision.json"
            ).read_text()
        )
        self.assertIn("hardware_defect_confirmed", data["forbidden_without_evidence"])

    def test_grub_validate_includes_control_c(self) -> None:
        cfg = grub.generate_gabriel_install_grub_cfg()
        v = grub.validate_gabriel_install_grub(cfg)
        self.assertTrue(v["ok"], v)
        self.assertTrue(v["checks"]["has_control_c1"])
        self.assertTrue(v["checks"]["control_c_no_rescue_target"])
        self.assertTrue(v["checks"]["control_c_multi_user"])


if __name__ == "__main__":
    unittest.main()
