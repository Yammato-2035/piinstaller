"""PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 6: storage_health_normalizer.py and
storage_baseline_diagnostics.py tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.storage_health_normalizer import (
    build_storage_health_normalizer_diagnostics,
    classify_device_class,
    is_usb_backed_device,
    is_virtual_device_name,
    read_block_geometry,
)
from core.storage_baseline_diagnostics import (
    build_storage_baseline_diagnostics,
    check_tool_availability,
    scan_kernel_storage_errors,
    summarize_common_device_state,
)


def _make_block_device(root: Path, name: str, *, rotational: int | None = None, size_sectors: int | None = None, logical: int | None = None, physical: int | None = None, ro: int | None = None, removable: int | None = None) -> Path:
    block_dir = root / "sys" / "block" / name
    queue_dir = block_dir / "queue"
    queue_dir.mkdir(parents=True)
    if rotational is not None:
        (queue_dir / "rotational").write_text(str(rotational))
    if logical is not None:
        (queue_dir / "logical_block_size").write_text(str(logical))
    if physical is not None:
        (queue_dir / "physical_block_size").write_text(str(physical))
    if size_sectors is not None:
        (block_dir / "size").write_text(str(size_sectors))
    if ro is not None:
        (block_dir / "ro").write_text(str(ro))
    if removable is not None:
        (block_dir / "removable").write_text(str(removable))
    return block_dir


class TestIsVirtualDeviceName(unittest.TestCase):
    def test_loop_is_virtual(self) -> None:
        self.assertTrue(is_virtual_device_name("loop0"))

    def test_dm_is_virtual(self) -> None:
        self.assertTrue(is_virtual_device_name("dm-0"))

    def test_sda_is_not_virtual(self) -> None:
        self.assertFalse(is_virtual_device_name("sda"))


class TestIsUsbBackedDevice(unittest.TestCase):
    def test_nonexistent_device_is_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(is_usb_backed_device("sdz", sysfs_root=Path(tmp)))

    def test_usb_symlink_path_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real_dev = root / "sys" / "devices" / "pci0000:00" / "usb1" / "1-1" / "block" / "sdc"
            real_dev.mkdir(parents=True)
            block_dir = root / "sys" / "block" / "sdc"
            block_dir.mkdir(parents=True)
            (block_dir / "device").symlink_to(real_dev)
            self.assertTrue(is_usb_backed_device("sdc", sysfs_root=root))


class TestClassifyDeviceClass(unittest.TestCase):
    def test_nvme_prefix_classified_directly(self) -> None:
        self.assertEqual(classify_device_class("nvme0n1"), "nvme")

    def test_loop_classified_virtual(self) -> None:
        self.assertEqual(classify_device_class("loop0"), "virtual")

    def test_rotational_hdd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_block_device(root, "sda", rotational=1)
            self.assertEqual(classify_device_class("sda", sysfs_root=root), "rotational")

    def test_non_rotational_ssd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_block_device(root, "sdb", rotational=0)
            self.assertEqual(classify_device_class("sdb", sysfs_root=root), "non_rotational")

    def test_unknown_when_missing_block_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(classify_device_class("sdz", sysfs_root=Path(tmp)), "unknown")

    def test_usb_backed_classified_before_rotational_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_block_device(root, "sdc", rotational=0)
            real_dev = root / "sys" / "devices" / "pci0000:00" / "usb1" / "1-1" / "block" / "sdc"
            real_dev.mkdir(parents=True)
            (root / "sys" / "block" / "sdc" / "device").symlink_to(real_dev)
            self.assertEqual(classify_device_class("sdc", sysfs_root=root), "usb_bridge")


class TestReadBlockGeometry(unittest.TestCase):
    def test_full_geometry_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_block_device(root, "sda", size_sectors=2000000, logical=512, physical=4096, ro=0, removable=0)
            geo = read_block_geometry("sda", sysfs_root=root)
            self.assertEqual(geo["logical_block_size"], 512)
            self.assertEqual(geo["physical_block_size"], 4096)
            self.assertEqual(geo["capacity_bytes"], 2000000 * 512)
            self.assertFalse(geo["read_only"])
            self.assertFalse(geo["removable"])

    def test_missing_fields_yield_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            geo = read_block_geometry("sdz", sysfs_root=Path(tmp))
            self.assertIsNone(geo["logical_block_size"])
            self.assertIsNone(geo["capacity_bytes"])


class TestScanKernelStorageErrors(unittest.TestCase):
    def test_io_error_detected(self) -> None:
        text = "[ 100.0] blk_update_request: I/O error, dev sda, sector 12345\n"
        scan = scan_kernel_storage_errors("sda", text)
        self.assertGreaterEqual(scan["io_error_count"], 1)

    def test_reset_timeout_detected(self) -> None:
        text = "[ 100.0] ata1.00: exception Emask 0x0 SAct 0x0 SErr 0x0 action 0x6 sda\n[ 100.0] ata1: hard resetting link, sda command timeout\n"
        scan = scan_kernel_storage_errors("sda", text)
        self.assertGreaterEqual(scan["reset_timeout_count"], 1)

    def test_link_error_detected(self) -> None:
        text = "[ 100.0] ata2.00: sdb: failed command: READ FPDMA QUEUED, link is down\n"
        scan = scan_kernel_storage_errors("sdb", text)
        self.assertGreaterEqual(scan["link_error_count"], 1)

    def test_unrelated_device_not_matched(self) -> None:
        text = "[ 100.0] blk_update_request: I/O error, dev sdb, sector 1\n"
        scan = scan_kernel_storage_errors("sda", text)
        self.assertEqual(scan["io_error_count"], 0)

    def test_missing_dmesg_tool_reported(self) -> None:
        scan = scan_kernel_storage_errors("sda", None, runner=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
        self.assertIn("dmesg", scan["missing_tools"])


class TestCheckToolAvailability(unittest.TestCase):
    def test_missing_smartctl_is_false(self) -> None:
        self.assertFalse(check_tool_availability("smartctl", runner=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError())))

    def test_present_tool_is_true(self) -> None:
        class R:
            stdout = "smartctl 7.3\n"

        self.assertTrue(check_tool_availability("smartctl", runner=lambda *a, **k: R()))


class TestSummarizeCommonDeviceState(unittest.TestCase):
    def test_mounted_device(self) -> None:
        summary = summarize_common_device_state(device_id="/dev/sda1", capacity_bytes=1000, mountpoints=("/",))
        self.assertTrue(summary["is_mounted"])

    def test_unmounted_device(self) -> None:
        summary = summarize_common_device_state(device_id="/dev/sdb", capacity_bytes=1000)
        self.assertFalse(summary["is_mounted"])


class TestDiagnostics(unittest.TestCase):
    def test_normalizer_diagnostics_read_only(self) -> None:
        self.assertTrue(build_storage_health_normalizer_diagnostics()["read_only"])

    def test_baseline_diagnostics_never_starts_self_test(self) -> None:
        diag = build_storage_baseline_diagnostics()
        self.assertFalse(diag["starts_smart_self_test"])
        self.assertFalse(diag["installs_tools"])


if __name__ == "__main__":
    unittest.main()
