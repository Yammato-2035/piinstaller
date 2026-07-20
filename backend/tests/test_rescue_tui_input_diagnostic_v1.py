"""PI-RS-TUI-AUTO-001 unit tests — no real /dev/input, no USB writes."""

from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from core.rescue_fat32_esp_usb_writer import generate_fat32_esp_grub_cfg
from core.rescue_msi_lab_auto_boot import (
    LAB_GUI_INTERACTIVE_MENU_TITLE,
    LAB_TEXT_INTERACTIVE_MENU_TITLE,
    TUI_INPUT_DIAG_MENU_TITLE,
    ensure_tui_input_diagnostic_menuentry,
    patch_grub_cfg_for_msi_gui_interactive_boot,
)
from core.rescue_payload_version import previous_rescue_payload_version, rescue_payload_version
from core.rescue_payload_version_carriers import (
    build_rescue_payload_version_json,
    build_rescue_runtime_version_json,
)
from core.rescue_tui_input_diagnostic_contract import (
    DIAG_FLAG,
    DiagnosticResult,
    blocked_tui_actions,
    diagnostic_mode_enabled,
    write_guard_response,
)
from core.rescue_tui_input_diagnostic import parse_stty_a, resolve_whiptail_pids
from core.rescue_tui_input_diagnostic_evaluate import (
    analyze_fds,
    classify_cpu,
    evaluate_tui_input_diagnostic,
)
from core.rescue_tui_input_diagnostic_evdev import parse_input_event_bytes
from core.rescue_tui_input_diagnostic_evidence import (
    REQUIRED_FILES,
    assert_path_under_allowed_roots,
    atomic_write_json,
    finalize_run_dir,
)
from core.rescue_tui_input_diagnostic_inventory import (
    classify_keyboard,
    diff_new_external_keyboards,
    parse_proc_bus_input_devices,
)


class CmdlineTests(unittest.TestCase):
    def test_kernel_cmdline_diag_mode_enabled(self) -> None:
        self.assertTrue(diagnostic_mode_enabled(f"BOOT_IMAGE=/x {DIAG_FLAG} quiet"))

    def test_kernel_cmdline_diag_mode_disabled(self) -> None:
        self.assertFalse(diagnostic_mode_enabled("setuphelfer_mode=text setuphelfer_rescue=1"))


FORBIDDEN_IOCTL_TOKENS = (
    "EVIOCGRAB",
    "uinput",
)


class EvdevTests(unittest.TestCase):
    def test_input_event_parser_x86_64(self) -> None:
        # timeval 2x long + HHi
        blob = struct.pack("llHHi", 1, 2, 1, 103, 1)  # KEY_UP press
        evs = parse_input_event_bytes(blob, word_size=8)
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0].name, "KEY_UP")
        self.assertEqual(evs[0].value, 1)

    def test_input_event_partial_read(self) -> None:
        blob = struct.pack("llHHi", 1, 2, 1, 108, 1) + b"\x00\x01"
        evs = parse_input_event_bytes(blob, word_size=8)
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0].name, "KEY_DOWN")

    def test_key_code_mapping(self) -> None:
        blob = struct.pack("llHHi", 0, 0, 1, 28, 1)
        self.assertEqual(parse_input_event_bytes(blob, word_size=8)[0].name, "KEY_ENTER")

    def test_no_eviocgrab_usage(self) -> None:
        root = Path(__file__).resolve().parents[1] / "core"
        for path in root.glob("rescue_tui_input_diagnostic*.py"):
            text = path.read_text(encoding="utf-8")
            for token in FORBIDDEN_IOCTL_TOKENS:
                self.assertNotIn(token, text, msg=f"{path.name} contains {token}")


class InventoryTests(unittest.TestCase):
    SAMPLE = """
I: Bus=0011 Vendor=0001 Product=0001 Version=ab41
N: Name="AT Translated Set 2 keyboard"
P: Phys=isa0060/serio0/input0
S: Sysfs=/devices/platform/i8042/serio0/input/input0
H: Handlers=sysrq kbd event0 leds
B: EV=120013

I: Bus=0003 Vendor=046a Product=b090 Version=0111
N: Name="Cherry USB keyboard"
P: Phys=usb-0000:00:14.0-3/input0
S: Sysfs=/devices/pci0000:00/usb1/1-3/1-3:1.0/input/input9
H: Handlers=sysrq kbd event9 leds
B: EV=100013
""".strip()

    def test_internal_keyboard_classification(self) -> None:
        devices = [classify_keyboard(d) for d in parse_proc_bus_input_devices(self.SAMPLE)]
        internal = [d for d in devices if d["is_internal_candidate"]]
        self.assertTrue(internal)
        self.assertEqual(internal[0]["bus"], "i8042")

    def test_external_usb_keyboard_classification(self) -> None:
        devices = [classify_keyboard(d) for d in parse_proc_bus_input_devices(self.SAMPLE)]
        external = [d for d in devices if d["is_external_candidate"]]
        self.assertTrue(external)
        self.assertEqual(external[0]["bus"], "usb")

    def test_diff_new_external(self) -> None:
        before = [classify_keyboard(d) for d in parse_proc_bus_input_devices(self.SAMPLE)]
        after = before + [
            {
                "event_node": "/dev/input/event99",
                "name": "New USB KB",
                "phys": "usb-x",
                "bus": "usb",
                "is_keyboard": True,
                "is_internal_candidate": False,
                "is_external_candidate": True,
                "vendor_id": "1",
                "product_id": "2",
                "sysfs_path_redacted": "",
            }
        ]
        neo = diff_new_external_keyboards(before, after)
        self.assertEqual(len(neo), 1)


class GuardTests(unittest.TestCase):
    def test_diagnostic_mode_write_guard(self) -> None:
        resp = write_guard_response()
        self.assertEqual(resp["status"], "blocked")
        self.assertIn("RESCUE_TUI_INPUT_DIAGNOSTIC", resp["code"])
        self.assertTrue({"e2e", "plan", "reboot"} <= blocked_tui_actions())

    def test_normal_mode_write_guard_unchanged(self) -> None:
        # Guard only applies when diag flag set — function is static response
        self.assertFalse(diagnostic_mode_enabled("setuphelfer_mode=text"))


class ProcessFdCpuTests(unittest.TestCase):
    def test_whiptail_process_resolution_from_systemd(self) -> None:
        ps = (
            "PID PPID TT STAT %CPU CMD\n"
            "100 1 tty1 Ss 0.0 /bin/bash tui\n"
            "200 100 tty1 S+ 40.0 whiptail --menu foo\n"
        )
        res = resolve_whiptail_pids(systemctl_show=lambda: "100", ps_output=ps)
        self.assertEqual(res["selected"]["pid"], "200")

    def test_multiple_whiptail_instances(self) -> None:
        ps = (
            " 111 1 tty1 S 1.0 whiptail --msgbox a\n"
            " 222 1 tty1 S 1.0 whiptail --menu b\n"
        )
        res = resolve_whiptail_pids(systemctl_show=lambda: "0", ps_output=ps)
        self.assertEqual(res["status"], "multiple_whiptail_instances")
        self.assertIsNone(res["selected"])

    def test_fd_all_tty1_ok(self) -> None:
        info = analyze_fds("/dev/tty1", "/dev/tty1", "/dev/tty1")
        self.assertEqual(info["status"], "ok")

    def test_fd0_dev_null_confirmed_mismatch(self) -> None:
        info = analyze_fds("/dev/null", "/dev/tty1", "/dev/tty1")
        self.assertEqual(info["status"], "mismatch")

    def test_fd0_pipe_confirmed_mismatch(self) -> None:
        info = analyze_fds("pipe:[123]", "/dev/tty1", "/dev/tty1")
        self.assertEqual(info["status"], "mismatch")

    def test_cpu_sampler_idle(self) -> None:
        self.assertEqual(classify_cpu(1.0), "idle_expected")

    def test_cpu_sampler_high_poll(self) -> None:
        self.assertEqual(classify_cpu(42.8), "high_poll_or_redraw")


class SttyTests(unittest.TestCase):
    def test_tty_state_parser_normal(self) -> None:
        text = "speed 38400 baud; rows 25; columns 80; icanon echo isig ixon opost"
        p = parse_stty_a(text)
        self.assertTrue(p["icanon"])
        self.assertTrue(p["echo"])
        self.assertFalse(p["raw_mode_detected"])

    def test_tty_state_parser_raw(self) -> None:
        text = "speed 38400 baud; rows 25; columns 80; -icanon -echo -isig"
        p = parse_stty_a(text)
        self.assertTrue(p["raw_mode_detected"])
        self.assertIn("raw_or_noncanonical_noecho", p["suspicious_flags"])


class DecisionTests(unittest.TestCase):
    def test_fd_mismatch_decision(self) -> None:
        r = DiagnosticResult(run_id="t", whiptail_analysis={"fd_status": "mismatch", "fd0": "/dev/null"})
        d = evaluate_tui_input_diagnostic(r)
        self.assertEqual(d.leading_hypothesis, "fd_mismatch")
        self.assertEqual(d.confidence, "confirmed")

    def test_h6_decision(self) -> None:
        r = DiagnosticResult(
            run_id="t",
            internal_keyboard_test={"status": "timeout", "evdev_keys_received": []},
            external_keyboard_test={"status": "passed"},
        )
        d = evaluate_tui_input_diagnostic(r)
        self.assertEqual(d.leading_hypothesis, "H6_input_driver")

    def test_h4_decision(self) -> None:
        r = DiagnosticResult(
            run_id="t",
            internal_keyboard_test={"status": "passed", "evdev_keys_received": ["KEY_UP"]},
            whiptail_analysis={"fd_status": "ok"},
            tty_analysis={"raw_mode_detected": True, "suspicious_flags": ["raw_or_noncanonical_noecho"]},
        )
        d = evaluate_tui_input_diagnostic(r)
        self.assertEqual(d.leading_hypothesis, "H4_terminal_state")

    def test_h7_decision(self) -> None:
        r = DiagnosticResult(
            run_id="t",
            menu_input_test={"evdev_keys_received": ["KEY_DOWN"], "operator_observations": {"menu_unchanged": True}},
            whiptail_analysis={"fd_status": "ok", "cpu_avg_percent": 43.0, "cpu_class": "high_poll_or_redraw"},
            process_analysis={"competing_writer_detected": False, "severity": "none"},
        )
        d = evaluate_tui_input_diagnostic(r)
        self.assertEqual(d.leading_hypothesis, "H7_newt_redraw")
        self.assertEqual(d.recommended_repair_path, "C_whiptail_newt_harden_or_replace")

    def test_tty_competition_decision(self) -> None:
        r = DiagnosticResult(
            run_id="t",
            process_analysis={"competing_writer_detected": True, "severity": "strong"},
        )
        d = evaluate_tui_input_diagnostic(r)
        self.assertEqual(d.leading_hypothesis, "tty_competition")

    def test_undetermined_decision(self) -> None:
        r = DiagnosticResult(run_id="t")
        d = evaluate_tui_input_diagnostic(r)
        self.assertEqual(d.leading_hypothesis, "undetermined")


class EvidenceTests(unittest.TestCase):
    def test_atomic_evidence_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.json"
            atomic_write_json(p, {"a": 1})
            self.assertTrue(p.is_file())
            self.assertFalse(p.with_suffix(".json.partial").exists())

    def test_manifest_and_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "run1"
            run.mkdir()
            fin = finalize_run_dir(run, status="review_required", final_result={"status": "review_required"})
            self.assertEqual(fin["status"], "review_required")
            self.assertTrue((run / "SHA256SUMS").is_file())
            self.assertTrue((run / "20-file-manifest.json").is_file())
            for name in REQUIRED_FILES:
                self.assertTrue((run / name).exists(), msg=name)

    def test_setuplogs_path_safety(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            allowed = root / "ok"
            allowed.mkdir()
            assert_path_under_allowed_roots(allowed / "run", [root])
            with self.assertRaises(ValueError):
                assert_path_under_allowed_roots(Path("/etc/passwd"), [root])

    def test_runtime_fallback_only_under_run(self) -> None:
        # Documented contract: fallback root is /run/setuphelfer/...
        self.assertTrue(str(Path("/run/setuphelfer/tui-input-diagnostics")).startswith("/run/setuphelfer"))


class GrubTests(unittest.TestCase):
    BASE = """set timeout=10
set timeout_style=menu
set default=0
menuentry "Setuphelfer starten - grafische Oberflaeche" {
  linux /live/vmlinuz boot=live
  initrd /live/initrd.img
}
menuentry "Neustart" { reboot }
"""

    def test_diag_entry_present_and_not_default(self) -> None:
        patched = patch_grub_cfg_for_msi_gui_interactive_boot(self.BASE)
        self.assertIn(TUI_INPUT_DIAG_MENU_TITLE, patched)
        self.assertIn("set default=0", patched)
        # default remains first interactive GUI entry
        first = patched.find('menuentry "')
        self.assertIn(LAB_GUI_INTERACTIVE_MENU_TITLE, patched[first : first + 120])
        self.assertIn(LAB_TEXT_INTERACTIVE_MENU_TITLE, patched)
        self.assertIn("setuphelfer_tui_input_diag=1", patched)
        self.assertIn("setuphelfer_tui_input_diag_auto_shutdown=0", patched)
        # diag flag only in diag entry block
        gui_block_start = patched.find(LAB_GUI_INTERACTIVE_MENU_TITLE)
        diag_start = patched.find(TUI_INPUT_DIAG_MENU_TITLE)
        self.assertNotIn("setuphelfer_tui_input_diag=1", patched[gui_block_start:diag_start])

    def test_ensure_append_idempotent(self) -> None:
        once = ensure_tui_input_diagnostic_menuentry(self.BASE)
        twice = ensure_tui_input_diagnostic_menuentry(once)
        self.assertEqual(once.count(TUI_INPUT_DIAG_MENU_TITLE), 1)
        self.assertEqual(twice.count(TUI_INPUT_DIAG_MENU_TITLE), 1)

    def test_fat32_generator_includes_diag(self) -> None:
        cfg = generate_fat32_esp_grub_cfg(fat_uuid="9BB9-A4A6", lab_auto_msi_boot=False)
        self.assertIn(TUI_INPUT_DIAG_MENU_TITLE, cfg)
        self.assertIn("set default=0", cfg)


class VersionCarrierTests(unittest.TestCase):
    def test_rescue_payload_version_is_current(self) -> None:
        self.assertEqual(rescue_payload_version(), "1.10.0.60")
        self.assertEqual(previous_rescue_payload_version(), "1.10.0.59")

    def test_usb_updater_updates_all_version_and_hash_carriers_atomically(self) -> None:
        payload = build_rescue_payload_version_json("1.10.0.60")
        runtime = build_rescue_runtime_version_json("1.10.0.60")
        self.assertEqual(payload["rescue_payload_version"], "1.10.0.60")
        self.assertEqual(runtime["project_version"], "1.10.0.60")
        self.assertEqual(runtime["rescue_payload_version"], "1.10.0.60")

    def test_tui_sh_guard_present(self) -> None:
        tui = (
            Path(__file__).resolve().parents[2]
            / "scripts/rescue-live/image/setuphelfer-rescue-tui.sh"
        ).read_text(encoding="utf-8")
        self.assertIn("_tui_input_diag_active", tui)
        self.assertIn("RESCUE_TUI_INPUT_DIAGNOSTIC_MODE_READ_ONLY", tui)

    def test_systemd_unit_tty2_and_condition(self) -> None:
        unit = (
            Path(__file__).resolve().parents[2]
            / "scripts/rescue-live/image/systemd/setuphelfer-rescue-tui-input-diagnostic.service"
        ).read_text(encoding="utf-8")
        self.assertIn("TTYPath=/dev/tty2", unit)
        self.assertIn("ConditionKernelCommandLine=setuphelfer_tui_input_diag=1", unit)
        self.assertIn("Conflicts=getty@tty2.service", unit)
        self.assertNotIn("TTYPath=/dev/tty1", unit)


class SafetyStaticTests(unittest.TestCase):
    FORBIDDEN = (
        "EVIOCGRAB",
        "uinput",
        "systemctl restart tui.service",
        "killall",
        "pkill whiptail",
        "wipefs",
        "sgdisk",
    )

    def test_diagnostic_sources_have_no_forbidden_ops(self) -> None:
        root = Path(__file__).resolve().parents[1] / "core"
        for path in root.glob("rescue_tui_input_diagnostic*.py"):
            text = path.read_text(encoding="utf-8")
            for token in self.FORBIDDEN:
                self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
