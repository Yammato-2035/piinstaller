"""Inspect Phase 2 – Klassifikation und Empfehlung (reine Logik, keine I/O)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load_module(mod_name: str, rel_path: str):
    path = _BACKEND / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if not spec or not spec.loader:
        raise ImportError(rel_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_classifier_mod = _load_module("setuphelfer_inspect_classifier_test", "inspect/classifier.py")
_advisor_mod = _load_module("setuphelfer_inspect_advisor_test", "inspect/advisor.py")
classify_system = _classifier_mod.classify_system
generate_advice = _advisor_mod.generate_advice


def _minimal_result(**overrides: dict) -> dict:
    base = {
        "system": {},
        "storage": {"devices_raw": [], "devices_classified": [], "mountability": []},
        "filesystems": {"detected": {}, "uuid_conflicts": {}},
        "boot": {
            "codes": ["rescue.boot.layout_ok"],
            "esp": {"present": False},
            "fstab_exists": True,
            "fstab_parse_ok": True,
            "kernel_files": ["vmlinuz"],
            "initrd_files": ["initrd.img"],
        },
        "network": {},
        "capabilities": {"os_hints": {}},
        "warnings": [],
        "errors": [],
        "source_modules": [],
    }
    base.update(overrides)
    return base


class TestInspectClassification(unittest.TestCase):
    def test_unknown_fallback_empty_payload(self):
        r = classify_system({})
        self.assertEqual(r["system_type"], "UNKNOWN")
        self.assertIsInstance(r["confidence"], float)
        self.assertIsInstance(r["indicators"], list)
        self.assertIn(r["risk_level"], ("low", "medium", "high"))
        a = generate_advice(r, {})
        self.assertIn("recommended_paths", a)
        self.assertIsInstance(a["recommended_paths"], list)

    def test_broken_boot(self):
        r = classify_system(
            _minimal_result(
                boot={"codes": ["rescue.boot.kernel_missing"], "esp": {"present": False}},
            )
        )
        self.assertEqual(r["system_type"], "BROKEN_BOOT")

    def test_broken_boot_priority_over_ntfs_pattern(self):
        """BROKEN_BOOT bleibt vor EFI+NTFS-Muster."""
        detected = {"/dev/sda1": {"type": "vfat"}, "/dev/sda2": {"type": "ntfs"}}
        r = classify_system(
            _minimal_result(
                filesystems={"detected": detected, "uuid_conflicts": {}},
                boot={"codes": ["rescue.boot.kernel_missing"]},
            )
        )
        self.assertEqual(r["system_type"], "BROKEN_BOOT")

    def test_dualboot_ntfs_ext4(self):
        detected = {"/dev/sda1": {"type": "ntfs", "uuid": "x"}, "/dev/sda2": {"type": "ext4", "uuid": "y"}}
        r = classify_system(_minimal_result(filesystems={"detected": detected, "uuid_conflicts": {}}))
        self.assertEqual(r["system_type"], "DUALBOOT")
        self.assertLessEqual(r["confidence"], 0.76)

    def test_linux_only_ext4(self):
        detected = {"/dev/nvme0n1p2": {"type": "ext4", "uuid": "z"}}
        r = classify_system(_minimal_result(filesystems={"detected": detected, "uuid_conflicts": {}}))
        self.assertEqual(r["system_type"], "LINUX")

    def test_ntfs_only_without_strong_signal_not_windows(self):
        """Nur NTFS ohne vfat/2×NTFS ⇒ nicht WINDOWS, keine hohe Confidence."""
        detected = {"/dev/sdb1": {"type": "ntfs", "uuid": "w"}}
        r = classify_system(
            _minimal_result(
                filesystems={"detected": detected, "uuid_conflicts": {}},
                boot={
                    "codes": ["rescue.boot.layout_ok"],
                    "esp": {"present": True},
                    "fstab_exists": True,
                    "fstab_parse_ok": True,
                    "kernel_files": [],
                    "initrd_files": [],
                },
            )
        )
        self.assertEqual(r["system_type"], "PARTIAL_SYSTEM")
        self.assertLessEqual(r["confidence"], 0.5)
        self.assertNotEqual(r["system_type"], "WINDOWS")

    def test_windows_requires_vfat_or_multi_ntfs(self):
        """WINDOWS nur mit Zusatzsignal aus bestehendem detected-Map."""
        detected = {
            "/dev/sda1": {"type": "vfat", "uuid": "efi"},
            "/dev/sda2": {"type": "ntfs", "uuid": "sys"},
        }
        r = classify_system(_minimal_result(filesystems={"detected": detected, "uuid_conflicts": {}}))
        self.assertEqual(r["system_type"], "WINDOWS")
        self.assertLessEqual(r["confidence"], 0.76)

    def test_windows_two_ntfs_volumes(self):
        detected = {
            "/dev/n1": {"type": "ntfs"},
            "/dev/n2": {"type": "ntfs"},
        }
        r = classify_system(_minimal_result(filesystems={"detected": detected, "uuid_conflicts": {}}))
        self.assertEqual(r["system_type"], "WINDOWS")

    def test_empty_disk_hint(self):
        r = classify_system(
            _minimal_result(
                capabilities={"os_hints": {"possible_empty_disk": True}},
                storage={"devices_raw": [{"partitions": []}], "devices_classified": [], "mountability": []},
            )
        )
        self.assertEqual(r["system_type"], "EMPTY")

    def test_all_system_types_reachable(self):
        """Stellt sicher, dass jeder deklarierte Typ synthetisch erreichbar ist (Regression)."""
        seen: set[str] = set()
        cases = [
            ("UNKNOWN", {}),
            ("BROKEN_BOOT", _minimal_result(boot={"codes": ["rescue.boot.fstab_missing"]})),
            ("EMPTY", _minimal_result(capabilities={"os_hints": {"possible_empty_disk": True}})),
            (
                "DUALBOOT",
                _minimal_result(
                    filesystems={
                        "detected": {"/a": {"type": "ntfs"}, "/b": {"type": "ext4"}},
                        "uuid_conflicts": {},
                    }
                ),
            ),
            ("LINUX", _minimal_result(filesystems={"detected": {"/x": {"type": "ext4"}}, "uuid_conflicts": {}})),
            (
                "WINDOWS",
                _minimal_result(
                    filesystems={
                        "detected": {"/e": {"type": "vfat"}, "/n": {"type": "ntfs"}},
                        "uuid_conflicts": {},
                    },
                ),
            ),
            (
                "PARTIAL_SYSTEM",
                _minimal_result(
                    storage={"devices_raw": [{"partitions": [{}]}], "devices_classified": [], "mountability": []},
                    filesystems={"detected": {}, "uuid_conflicts": {}},
                    capabilities={"os_hints": {"unknown_layout": True}},
                ),
            ),
        ]
        for expected_type, payload in cases:
            out = classify_system(payload)
            seen.add(out["system_type"])
            self.assertEqual(
                out["system_type"],
                expected_type,
                msg=f"expected {expected_type}, got {out} for keys {list(payload.keys())}",
            )
            adv = generate_advice(out, payload)
            self.assertTrue(adv.get("recommended_paths"))

        # NTFS-only ambigu ergänzt PARTIAL_SYSTEM — zusätzlicher Fall ohne WINDOWS-Erwartung
        ntfs_only = classify_system(
            _minimal_result(filesystems={"detected": {"/solo": {"type": "ntfs"}}, "uuid_conflicts": {}})
        )
        self.assertEqual(ntfs_only["system_type"], "PARTIAL_SYSTEM")

        required = {"EMPTY", "WINDOWS", "LINUX", "DUALBOOT", "BROKEN_BOOT", "PARTIAL_SYSTEM", "UNKNOWN"}
        self.assertTrue(required.issubset(seen), f"missing types: {required - seen}")
