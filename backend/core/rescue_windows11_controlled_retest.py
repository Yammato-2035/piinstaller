"""Controlled Windows 11 retest (PI-RS-ASUS-WIN11-RETEST-005).

Stage A under BIOS G513QM.331 with WinPE log collection.
Stage B BIOS 335 only after justified gate. No automatic flash.
Linux stays locked until Windows postcheck passes.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

CONTRACT_VERSION = 1
SCHEMA_VERSION = 1
TASK_ID = "PI-RS-ASUS-WIN11-RETEST-005"

PHRASE_IDENTITY = "WINDOWS-ZIEL G513QM BESTÄTIGT"
PHRASE_DESTRUCTIVE = "WINDOWS-NVME VOLLSTÄNDIG LÖSCHEN"

ENDSTATUSES = frozenset(
    {
        "ready_for_windows_retest_bios331",
        "windows_installed_on_bios_331",
        "diagnosis_complete_windows_fix_pending",
        "ready_for_bios_335_controlled_update",
        "bios_335_installed_retest_pending",
        "windows_installed_on_bios_335",
        "windows_installed_linux_pending",
        "blocked_linux_nvme_isolation",
        "blocked_install_media_corrupt",
        "blocked_bios_update",
        "blocked_workspace_runtime_or_identity_gate",
        "failed",
        "bios_causality_not_tested",
    }
)

CAUSALITY_LABELS = frozenset(
    {
        "not_tested",
        "inconclusive",
        "unlikely",
        "plausible",
        "strongly_implicated",
    }
)

WINPE_COLLECTOR_REQUIRED = (
    "README_DE.txt",
    "README_EN.txt",
    "collect-win11-setup-logs.cmd",
    "collect-win11-setup-logs.ps1",
    "collect-win11-disk-info.cmd",
    "collect-win11-disk-info.ps1",
    "collect-win11-boot-info.cmd",
    "SETUP_LOGS.TAG",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short(value: str | None, n: int = 12) -> str:
    return str(value or "")[:n]


def _hash_plan(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def build_target_role_binding(
    *,
    machine_profile: str,
    machine_fingerprint_hash: str,
    windows_target: Mapping[str, Any],
    linux_target: Mapping[str, Any],
    operator_confirmed: bool,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Operator-bound Windows/Linux NVMe roles. write_allowed stays false here."""
    win = dict(windows_target)
    lin = dict(linux_target)
    win_hash = str(win.get("nvme_identity_hash") or "")
    lin_hash = str(lin.get("nvme_identity_hash") or "")
    same = bool(win_hash and win_hash == lin_hash)
    for side in (win, lin):
        side["confirmed"] = bool(side.get("confirmed")) and operator_confirmed and not same
        side["write_allowed"] = False
    ok = (
        bool(machine_profile)
        and bool(machine_fingerprint_hash)
        and bool(win_hash)
        and bool(lin_hash)
        and not same
        and win_hash != lin_hash
        and str(win.get("eui") or "") != str(lin.get("eui") or "")
        and str(win.get("pci_path") or "") != str(lin.get("pci_path") or "")
        and operator_confirmed
        and bool(win.get("confirmed"))
        and bool(lin.get("confirmed"))
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "task_id": TASK_ID,
        "machine_profile": machine_profile,
        "machine_fingerprint_hash": machine_fingerprint_hash,
        "windows_target": win,
        "linux_target": lin,
        "same_device": same,
        "created_at": created_at or _utc_now(),
        "operator_confirmed": bool(operator_confirmed),
        "binding_ok": ok,
        "write_allowed": False,
    }


def validate_target_role_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    win = dict(binding.get("windows_target") or {})
    lin = dict(binding.get("linux_target") or {})
    errors: list[str] = []
    if binding.get("same_device"):
        errors.append("same_device")
    if not win.get("nvme_identity_hash") or not lin.get("nvme_identity_hash"):
        errors.append("missing_identity_hash")
    if win.get("nvme_identity_hash") == lin.get("nvme_identity_hash"):
        errors.append("identical_identity_hash")
    if win.get("eui") and lin.get("eui") and win.get("eui") == lin.get("eui"):
        errors.append("identical_eui")
    if win.get("pci_path") and lin.get("pci_path") and win.get("pci_path") == lin.get("pci_path"):
        errors.append("identical_pci_path")
    if not binding.get("operator_confirmed"):
        errors.append("operator_not_confirmed")
    if not win.get("confirmed") or not lin.get("confirmed"):
        errors.append("targets_not_confirmed")
    if win.get("write_allowed") or lin.get("write_allowed"):
        errors.append("write_allowed_premature")
    return {
        "ok": not errors,
        "errors": errors,
        "windows_identity_short": _short(str(win.get("nvme_identity_hash") or "")),
        "linux_identity_short": _short(str(lin.get("nvme_identity_hash") or "")),
    }


def build_linux_nvme_isolation(
    *,
    method: str,
    linux_identity_hash: str,
    windows_identity_hash: str,
    verified_in_winpe: bool,
    linux_writable_for_setup: bool,
    notes: str = "",
    operator_documented: bool = False,
) -> dict[str, Any]:
    """Document Linux NVMe isolation (physical / UEFI disable / WinPE offline)."""
    method_l = (method or "").strip().lower()
    allowed = {"physical_remove", "uefi_disable", "winpe_offline", "unverified"}
    if method_l not in allowed:
        method_l = "unverified"
    ok = (
        method_l in {"physical_remove", "uefi_disable", "winpe_offline"}
        and bool(linux_identity_hash)
        and bool(windows_identity_hash)
        and linux_identity_hash != windows_identity_hash
        and verified_in_winpe
        and not linux_writable_for_setup
        and operator_documented
    )
    status = "isolated" if ok else "blocked_linux_nvme_isolation"
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "task_id": TASK_ID,
        "method": method_l,
        "linux_identity_hash": linux_identity_hash,
        "windows_identity_hash": windows_identity_hash,
        "verified_in_winpe": bool(verified_in_winpe),
        "linux_writable_for_setup": bool(linux_writable_for_setup),
        "operator_documented": bool(operator_documented),
        "notes": notes,
        "status": status,
        "ok": ok,
        "created_at": _utc_now(),
    }


def build_bios_331_baseline(
    *,
    installed_version: str = "G513QM.331",
    bios_date: str = "2023-02-24",
    uefi_mode: bool = True,
    secure_boot: str = "unknown",
    tpm: str = "unknown",
    boot_order: Sequence[str] | None = None,
    fast_boot: str = "unknown",
    csm_legacy: bool = False,
    storage_mode: str = "unknown",
    uefi_boot_entries: Sequence[str] | None = None,
    linux_nvme_isolated: bool = False,
    windows_identity_hash: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "task_id": TASK_ID,
        "installed_version": installed_version,
        "bios_date": bios_date,
        "uefi_mode": bool(uefi_mode),
        "secure_boot": secure_boot,
        "tpm": tpm,
        "boot_order": list(boot_order or []),
        "fast_boot": fast_boot,
        "csm_legacy": bool(csm_legacy),
        "storage_mode": storage_mode,
        "uefi_boot_entries": list(uefi_boot_entries or []),
        "linux_nvme_isolated": bool(linux_nvme_isolated),
        "windows_identity_hash": windows_identity_hash,
        "flash_performed": False,
        "created_at": _utc_now(),
    }


def build_windows_media_result(
    *,
    source: str,
    architecture: str = "x64",
    sha256: str = "",
    efi_boot: bool = False,
    boot_wim: bool = False,
    install_wim_or_esd: bool = False,
    status: str = "unknown_hash",
    operator_override: bool = False,
) -> dict[str, Any]:
    st = (status or "unknown_hash").lower()
    if st not in {"valid", "unknown_hash", "corrupt", "unsupported"}:
        st = "unknown_hash"
    if st == "corrupt":
        install_allowed = False
        block = "blocked_install_media_corrupt"
    elif st == "unsupported":
        install_allowed = False
        block = "blocked_install_media_unsupported"
    elif st == "unknown_hash":
        install_allowed = bool(operator_override)
        block = None if install_allowed else "media_hash_unverified"
    else:
        install_allowed = bool(efi_boot and boot_wim and install_wim_or_esd and architecture.lower() == "x64")
        block = None if install_allowed else "media_structure_incomplete"
    return {
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "architecture": architecture,
        "sha256": sha256,
        "efi_boot": bool(efi_boot),
        "boot_wim": bool(boot_wim),
        "install_wim_or_esd": bool(install_wim_or_esd),
        "status": st,
        "verified_claim": st == "valid",
        "operator_override": bool(operator_override),
        "install_start_allowed": install_allowed,
        "block_reason": block,
        "iso_not_in_repo": True,
    }


def build_stage_a_preflight(
    *,
    machine_profile: str,
    bios_version: str,
    binding: Mapping[str, Any],
    isolation: Mapping[str, Any],
    media: Mapping[str, Any],
    windows_smart_critical: bool,
    uefi: bool,
    tpm_ok: bool,
    ram_gb: float,
    collector_reachable: bool,
    setup_logs_writable: bool,
    ac_power: bool,
) -> dict[str, Any]:
    blockers: list[str] = []
    if machine_profile != "asus_rog_gabriel":
        blockers.append("machine_profile")
    if not str(bios_version).endswith(".331") and "G513QM.331" not in str(bios_version):
        blockers.append("bios_not_331")
    if not binding.get("binding_ok"):
        blockers.append("target_binding")
    if not isolation.get("ok"):
        blockers.append("linux_nvme_isolation")
    if media.get("status") == "corrupt":
        blockers.append("media_corrupt")
    elif not media.get("install_start_allowed"):
        blockers.append("media_not_ready")
    if windows_smart_critical:
        blockers.append("windows_nvme_smart_critical")
    if not uefi:
        blockers.append("uefi_required")
    if not tpm_ok:
        blockers.append("tpm")
    if ram_gb < 8:
        blockers.append("ram")
    if not collector_reachable:
        blockers.append("winpe_collector")
    if not setup_logs_writable:
        blockers.append("setup_logs_not_writable")
    if not ac_power:
        blockers.append("ac_power")

    if blockers:
        status = "blocked"
    elif media.get("status") == "unknown_hash" or isolation.get("method") == "winpe_offline":
        status = "review_required"
    else:
        status = "ready"

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "status": status,
        "blockers": blockers,
        "write_allowed_windows_only": False,
        "bios_stage": "331",
        "created_at": _utc_now(),
    }


def build_destructive_authorization(
    *,
    machine_fingerprint_hash: str,
    windows_identity_hash: str,
    boot_id: str,
    preflight_id: str,
    identity_phrase: str,
    destructive_phrase: str,
    linux_offline_ack: bool,
    no_backup_ack: bool,
    expires_at: str,
) -> dict[str, Any]:
    identity_ok = identity_phrase.strip() == PHRASE_IDENTITY
    destructive_ok = destructive_phrase.strip() == PHRASE_DESTRUCTIVE
    ok = all(
        [
            identity_ok,
            destructive_ok,
            bool(machine_fingerprint_hash),
            bool(windows_identity_hash),
            bool(boot_id),
            bool(preflight_id),
            linux_offline_ack,
            no_backup_ack,
            bool(expires_at),
        ]
    )
    plan = {
        "machine_fingerprint_hash": machine_fingerprint_hash,
        "windows_identity_hash": windows_identity_hash,
        "boot_id": boot_id,
        "preflight_id": preflight_id,
        "expires_at": expires_at,
        "phrases": [PHRASE_IDENTITY, PHRASE_DESTRUCTIVE],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": ok,
        "write_allowed": False,  # still false until operator executes Windows Setup wipe
        "execute_handoff_allowed": ok,
        "plan_hash": _hash_plan(plan),
        "bound_to": plan,
        "requires": [
            "identity_phrase",
            "destructive_phrase",
            "linux_offline_ack",
            "no_backup_ack",
            "binding_ids",
        ],
        "note": "Authorization binds plan; Windows Setup performs the wipe on the confirmed Windows NVMe only.",
    }


def decide_stage_a_outcome(
    *,
    install_succeeded: bool,
    firmware_related: bool | None,
    concrete_non_firmware_cause: str | None = None,
    unclear: bool = False,
) -> dict[str, Any]:
    if install_succeeded:
        endstatus = "windows_installed_on_bios_331"
        next_step = "windows_postcheck"
    elif concrete_non_firmware_cause and firmware_related is False:
        endstatus = "diagnosis_complete_windows_fix_pending"
        next_step = f"fix:{concrete_non_firmware_cause}"
    elif unclear:
        endstatus = "ready_for_windows_retest_bios331"
        next_step = "review_logs_then_decide_bios335"
    elif firmware_related:
        endstatus = "ready_for_bios_335_controlled_update"
        next_step = "bios_335_update_gate"
    else:
        endstatus = "diagnosis_complete_windows_fix_pending"
        next_step = "classify_setup_failure"
    return {
        "stage": "A",
        "bios": "G513QM.331",
        "endstatus": endstatus,
        "next_step": next_step,
        "bios_flash_authorized": False,
    }


def bios_335_update_gate(
    *,
    model: str,
    board: str,
    installed: str,
    target: str,
    official_ez_flash_file: bool,
    checksum_documented: bool,
    ac_power: bool,
    battery_ok: bool,
    no_running_install: bool,
    operator_approved: bool,
) -> dict[str, Any]:
    blockers: list[str] = []
    if "G513QM" not in model.upper() and "G513QM" not in board.upper():
        blockers.append("wrong_model")
    if "331" not in installed:
        blockers.append("installed_not_331")
    if "335" not in target:
        blockers.append("target_not_335")
    if not official_ez_flash_file:
        blockers.append("not_official_ez_flash")
    if not checksum_documented:
        blockers.append("checksum")
    if not ac_power:
        blockers.append("ac_power")
    if not battery_ok:
        blockers.append("battery")
    if not no_running_install:
        blockers.append("install_in_progress")
    if not operator_approved:
        blockers.append("operator_approval")
    ok = not blockers
    return {
        "ok": ok,
        "blockers": blockers,
        "auto_flash": False,
        "method": "asus_ez_flash_uefi",
        "linux_flash_forbidden": True,
        "fwupdmgr_forbidden": True,
        "flashrom_forbidden": True,
        "status": "ready" if ok else "blocked_bios_update",
    }


def evaluate_bios_causality(
    *,
    stage_a_result: str,
    stage_b_result: str | None,
    same_media: bool,
    same_windows_nvme: bool,
    same_linux_isolation: bool,
    other_variables_changed: bool,
) -> dict[str, Any]:
    """Honest A/B BIOS causality. Never claim sole cause."""
    if other_variables_changed or not (same_media and same_windows_nvme and same_linux_isolation):
        label = "inconclusive"
        strongly = False
        unlikely = False
        note = "bios_causality_inconclusive"
    elif stage_b_result is None:
        label = "not_tested"
        strongly = False
        unlikely = False
        note = "stage_b_pending_or_skipped"
    elif stage_a_result == "failed" and stage_b_result == "passed":
        label = "strongly_implicated"
        strongly = True
        unlikely = False
        note = "bios_335_strongly_implicated"
    elif stage_a_result == "failed" and stage_b_result == "failed":
        label = "unlikely"
        strongly = False
        unlikely = True
        note = "bios_unlikely_primary_cause"
    elif stage_a_result == "passed" and stage_b_result == "passed":
        label = "unlikely"
        strongly = False
        unlikely = True
        note = "original_failure_not_reproduced"
    elif stage_a_result == "passed":
        label = "unlikely"
        strongly = False
        unlikely = True
        note = "old_bios_not_required_for_failure"
    else:
        label = "plausible"
        strongly = False
        unlikely = False
        note = "firmware_related_signals_present"

    assert label in CAUSALITY_LABELS
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "stage_a_result": stage_a_result,
        "stage_b_result": stage_b_result,
        "same_media": same_media,
        "same_windows_nvme": same_windows_nvme,
        "same_linux_isolation": same_linux_isolation,
        "other_variables_changed": other_variables_changed,
        "causality": label,
        "bios_335_strongly_implicated": strongly,
        "bios_unlikely_primary_cause": unlikely,
        "sole_cause_claimed": False,
        "note": note,
    }


def windows_postcheck_to_linux_gate(postcheck: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "windows_booted": postcheck.get("windows_booted") is True,
        "oobe_or_intermediate_ok": postcheck.get("oobe_or_intermediate_ok") is True,
        "two_reboots_ok": postcheck.get("two_reboots_ok") is True,
        "system_on_windows_nvme": postcheck.get("system_on_windows_nvme") is True,
        "efi_on_windows_nvme": postcheck.get("efi_on_windows_nvme") is True,
        "linux_nvme_unchanged": postcheck.get("linux_nvme_unchanged") is True,
        "no_critical_disk_events": not postcheck.get("critical_disk_events"),
        "no_whea_critical": not postcheck.get("whea_critical"),
    }
    ok = all(required.values())
    return {
        "ok": ok,
        "status": "windows_postcheck_passed" if ok else "windows_postcheck_failed",
        "linux_install_gate": "ready_for_planning" if ok else "blocked",
        "missing": [k for k, v in required.items() if not v],
        "linux_write_allowed": False,
    }


def build_win11_retest_dcc(
    *,
    bios_installed: str,
    bios_update_result: str | None,
    causality: str,
    windows_media_status: str,
    windows_target_short: str,
    linux_isolated: bool,
    setup_phase: str,
    error_code: str,
    setupdiag: str,
    install_result: str,
    postcheck: str,
    linux_gate: str,
    endstatus: str,
) -> dict[str, Any]:
    if endstatus.startswith("blocked_") or endstatus == "failed":
        overall = "red"
    elif endstatus in {
        "windows_installed_linux_pending",
        "windows_installed_on_bios_331",
        "windows_installed_on_bios_335",
    }:
        overall = "green"
    elif endstatus == "ready_for_windows_retest_bios331":
        overall = "yellow"
    else:
        overall = "yellow"

    # Never green solely because installer started.
    if install_result in {"started", "in_progress"}:
        overall = "yellow"

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "title": "Gabriel – Win11 Retest BIOS 331/335",
        "bios": {
            "installed": bios_installed,
            "update_result": bios_update_result or "not_run",
            "causality": causality if causality in CAUSALITY_LABELS else "not_tested",
            "tone": "yellow" if "331" in bios_installed else "green",
        },
        "windows_retest": {
            "media": windows_media_status,
            "target_nvme": windows_target_short,
            "linux_nvme_isolated": linux_isolated,
            "bios_version": bios_installed,
            "setup_phase": setup_phase,
            "error_code": error_code,
            "setupdiag": setupdiag,
            "install_result": install_result,
            "postcheck": postcheck,
            "tone": "yellow" if install_result != "passed" else "green",
        },
        "causality": {
            "label": causality if causality in CAUSALITY_LABELS else "not_tested",
            "sole_cause_claimed": False,
        },
        "linux": {
            "gate": linux_gate,
            "status": "locked" if linux_gate != "ready_for_planning" else "ready_for_planning",
            "tone": "yellow" if linux_gate == "ready_for_planning" else "gray",
        },
        "endstatus": endstatus,
        "overall_tone": overall,
        "write_authorization": False,
        "fake_green_guard": True,
    }


def assert_winpe_collector_files(root) -> list[str]:
    missing = [name for name in WINPE_COLLECTOR_REQUIRED if not (root / name).is_file()]
    return missing
