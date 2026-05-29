from __future__ import annotations

import re
from typing import Any


def classify_vm_boot_smoke_logs(
    *,
    stdout_text: str,
    stderr_text: str,
    qemu_exit_code: int | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    combined = f"{stdout_text}\n{stderr_text}".lower()
    timeout_reached = qemu_exit_code == 124 or "terminating on signal 15" in stderr_text.lower()

    bios_seen = bool(re.search(r"seabios|ipxe", combined, re.I))
    bootloader_seen = bool(
        re.search(r"isolinux|syslinux|booting from dvd|booting from cd", combined, re.I)
    )
    kernel_started = bool(re.search(r"linux version|kernel", combined, re.I))
    initrd_started = bool(re.search(r"initrd|initial ramdisk", combined, re.I))
    live_system_started = bool(
        re.search(r"debian.*live|live\/\d|welcome|login:", combined, re.I)
    )
    setuphelfer_marker_seen = "setuphelfer" in combined

    if re.search(r"no bootable|not a bootable|boot failed", combined, re.I):
        classification = "boot_failed_no_bootable_medium"
    elif re.search(r"kernel panic|panic -", combined, re.I):
        classification = "boot_failed_kernel_panic"
    elif live_system_started or setuphelfer_marker_seen:
        classification = "live_system_started"
    elif initrd_started:
        classification = "initrd_started"
    elif kernel_started:
        classification = "kernel_started"
    elif bootloader_seen:
        classification = "bootloader_seen"
    elif bios_seen and timeout_reached:
        classification = "bios_seen"
    elif timeout_reached and not stdout_text.strip():
        classification = "timeout_no_boot_signal"
    elif timeout_reached:
        classification = "timeout_no_boot_signal_again"
    elif qemu_exit_code not in (None, 0):
        classification = "boot_failed_unknown"
    else:
        classification = "unsafe_or_unknown"

    return {
        "bios_seen": bios_seen,
        "bootloader_seen": bootloader_seen,
        "kernel_started": kernel_started,
        "initrd_started": initrd_started,
        "live_system_started": live_system_started,
        "setuphelfer_marker_seen": setuphelfer_marker_seen,
        "timeout_reached": timeout_reached,
        "classification": classification,
    }
