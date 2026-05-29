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


def classify_live_system_boot_logs(
    *,
    stdout_text: str,
    stderr_text: str,
    qemu_exit_code: int | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Extended classification for kernel/initrd/live/setuphelfer boot stages."""
    base = classify_vm_boot_smoke_logs(
        stdout_text=stdout_text,
        stderr_text=stderr_text,
        qemu_exit_code=qemu_exit_code,
        timeout_seconds=timeout_seconds,
    )
    combined = f"{stdout_text}\n{stderr_text}".lower()

    kernel_started = bool(
        re.search(
            r"linux version|loading vmlinuz|vmlinuz|booting the kernel|starting kernel",
            combined,
            re.I,
        )
    )
    initrd_started = bool(
        re.search(r"initrd|initial ramdisk|loading initrd", combined, re.I)
    )
    squashfs_loaded = bool(re.search(r"squashfs|filesystem\.squashfs", combined, re.I))
    live_system_started = bool(
        re.search(
            r"debian.*live|booting debian|live-image|systemd\[|started.*multi-user",
            combined,
            re.I,
        )
    )
    login_prompt_seen = bool(
        re.search(r"login:|password:|live@|user@|debian login", combined, re.I)
    )
    setuphelfer_bundle_seen = bool(re.search(r"setuphelfer-rescue|/opt/setuphelfer", combined, re.I))
    setuphelfer_ui_seen = bool(re.search(r"setuphelfer.*ui|start-ui-localonly", combined, re.I))

    if re.search(r"initramfs.*shell|drop to.*shell|busybox.*ash", combined, re.I):
        classification = "boot_failed_initramfs_shell"
    elif re.search(r"kernel panic", combined, re.I):
        classification = "boot_failed_kernel_panic"
    elif setuphelfer_ui_seen:
        classification = "setuphelfer_ui_seen"
    elif setuphelfer_bundle_seen:
        classification = "setuphelfer_bundle_seen"
    elif login_prompt_seen or live_system_started:
        classification = "live_system_started" if live_system_started else "login_prompt_seen"
    elif squashfs_loaded:
        classification = "squashfs_loaded"
    elif initrd_started:
        classification = "initrd_started"
    elif kernel_started:
        classification = "kernel_started"
    elif base["bootloader_seen"] and base["timeout_reached"]:
        classification = "timeout_after_bootloader"
    elif base["kernel_started"] and base["timeout_reached"]:
        classification = "timeout_after_kernel"
    else:
        classification = base["classification"]

    return {
        **base,
        "kernel_started": kernel_started or base["kernel_started"],
        "initrd_started": initrd_started or base["initrd_started"],
        "squashfs_loaded": squashfs_loaded,
        "live_system_started": live_system_started or base["live_system_started"],
        "login_prompt_seen": login_prompt_seen,
        "setuphelfer_bundle_seen": setuphelfer_bundle_seen,
        "setuphelfer_ui_seen": setuphelfer_ui_seen,
        "classification": classification,
    }


def classify_visual_live_functional_validation(
    *,
    visual_vm_test_executed: bool,
    operator_authorized: bool,
    login_user_live_success: bool = False,
    bundle_path_present: bool = False,
    backend_service_active: bool = False,
    backend_version_ok: bool = False,
    backend_health_ok: bool = False,
    keyboard_de: bool = False,
    locale_de: bool = False,
    live_system_started: bool = False,
    login_prompt_seen: bool = False,
    bootloader_seen: bool = False,
    kernel_started: bool = False,
    hostname_setuphelfer_rescue: bool = False,
    operator_output_provided: bool = False,
) -> dict[str, Any]:
    """Classify visual live-system functional validation from operator checklist."""
    if not visual_vm_test_executed or not operator_authorized:
        classification = "visual_live_functional_prepared_not_executed"
        rescue_runtime = "yellow"
    elif not operator_output_provided:
        classification = "operator_visual_output_missing"
        rescue_runtime = "yellow"
    elif not live_system_started and not login_prompt_seen:
        classification = "live_boot_failed"
        rescue_runtime = "yellow"
    elif live_system_started and login_prompt_seen and not login_user_live_success:
        classification = "live_boot_login_failed"
        rescue_runtime = "yellow"
    elif login_user_live_success and not bundle_path_present:
        classification = "live_boot_success_bundle_missing"
        rescue_runtime = "yellow"
    elif login_user_live_success and bundle_path_present and not (keyboard_de and locale_de):
        classification = "live_boot_success_keyboard_locale_failed"
        rescue_runtime = "yellow"
    elif (
        login_user_live_success
        and bundle_path_present
        and backend_service_active
        and (backend_version_ok or backend_health_ok)
    ):
        classification = "live_boot_success_login_ok_backend_ok"
        rescue_runtime = "partial_green"
    elif login_user_live_success and bundle_path_present and not backend_service_active:
        classification = "live_boot_success_backend_failed"
        rescue_runtime = "yellow"
    else:
        classification = "unsafe_or_unknown"
        rescue_runtime = "yellow"

    return {
        "visual_vm_test_executed": visual_vm_test_executed,
        "operator_authorized": operator_authorized,
        "bootloader_seen": bootloader_seen,
        "kernel_started": kernel_started,
        "live_system_started": live_system_started,
        "login_prompt_seen": login_prompt_seen,
        "login_user_live_success": login_user_live_success,
        "hostname_setuphelfer_rescue": hostname_setuphelfer_rescue,
        "keyboard_de": keyboard_de,
        "locale_de": locale_de,
        "bundle_path_present": bundle_path_present,
        "backend_service_active": backend_service_active,
        "backend_health_ok": backend_health_ok,
        "backend_version_ok": backend_version_ok,
        "classification": classification,
        "rescue_runtime_functional_status": rescue_runtime,
        "rescue_overall_status": "yellow",
    }
