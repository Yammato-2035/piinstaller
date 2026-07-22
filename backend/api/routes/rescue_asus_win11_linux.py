"""API routes for PI-RS-ASUS-WIN11-LINUX-001 (firmware, Win11 diag, Linux second NVMe)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Body

from core.rescue_bios_official_compare import check_latest_official_bios
from core.rescue_firmware_inventory import collect_firmware_inventory
from core.rescue_linux_second_nvme import (
    build_linux_partition_plan,
    check_linux_iso,
    linux_install_execute_gate,
    linux_install_preflight,
)
from core.rescue_machine_identity_profiles import bind_gabriel_operator_profile, build_machine_identity
from core.rescue_nvme_install_target import (
    build_asus_install_targets_manifest,
    evaluate_nvme_health,
    inventory_from_nvme_list_json,
    normalize_nvme_entry,
)
from core.rescue_windows11_install_diag import (
    build_abort_cause_matrix,
    build_windows11_preflight,
    check_windows_install_media,
    scan_windows_setup_evidence,
    windows_postcheck_gate,
    windows_target_destructive_gate,
)

from core.rescue_windows11_controlled_retest import (
    bios_335_update_gate,
    build_destructive_authorization,
    build_linux_nvme_isolation,
    build_stage_a_preflight,
    build_target_role_binding,
    build_win11_retest_dcc,
    build_windows_media_result,
    decide_stage_a_outcome,
    evaluate_bios_causality,
    validate_target_role_binding,
    windows_postcheck_to_linux_gate,
)

router = APIRouter(tags=["rescue-asus-win11-linux"])


@router.get("/hardware/identity")
async def get_hardware_identity() -> dict[str, Any]:
    return build_machine_identity()


@router.post("/hardware/bind-gabriel")
async def post_bind_gabriel(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Operator-only bind of Gabriel's ASUS ROG. Rejects known developer hosts."""
    identity = body.get("machine") or build_machine_identity()
    return bind_gabriel_operator_profile(
        identity,
        operator_confirmed=bool(body.get("operator_confirmed")),
        exact_model_confirmed=str(body.get("exact_model_confirmed") or ""),
        not_developer_host_ack=bool(body.get("not_developer_host_ack")),
        operator_phrase=body.get("operator_phrase"),
    )


@router.get("/hardware/inventory")
async def get_hardware_inventory() -> dict[str, Any]:
    identity = build_machine_identity()
    fw = collect_firmware_inventory()
    return {"identity": identity, "firmware": fw, "write_actions": False}


@router.get("/firmware/inventory")
async def get_firmware_inventory() -> dict[str, Any]:
    return collect_firmware_inventory()


@router.post("/firmware/check-latest")
async def post_firmware_check_latest(body: Optional[dict[str, Any]] = Body(default=None)) -> dict[str, Any]:
    body = body or {}
    machine = body.get("machine") or build_machine_identity()
    return check_latest_official_bios(
        machine=machine,
        online=bool(body.get("online", True)),
    )


@router.get("/storage/nvme-inventory")
async def get_nvme_inventory() -> dict[str, Any]:
    # Live discovery is best-effort; empty inventory is valid without hardware.
    return {
        "devices": [],
        "note": "Pass Devices via POST body helpers or populate from live nvme list on rescue stick",
        "write_allowed": False,
    }


@router.post("/storage/nvme-inventory")
async def post_nvme_inventory(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    devices = inventory_from_nvme_list_json(body)
    enriched = []
    for d in devices:
        health = evaluate_nvme_health(d)
        item = dict(d)
        item.update(health)
        item["write_allowed"] = False
        enriched.append(item)
    return {"devices": enriched, "write_allowed": False}


@router.post("/windows11/evidence-scan")
async def post_windows11_evidence_scan(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    roots = [Path(p) for p in (body.get("roots") or [])]
    evidence = scan_windows_setup_evidence(roots)
    evidence["abort_matrix"] = build_abort_cause_matrix(evidence)
    return evidence


@router.post("/windows11/media-check")
async def post_windows11_media_check(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return check_windows_install_media(
        iso_or_root=Path(str(body.get("path") or "")),
        expected_sha256=body.get("expected_sha256"),
        computed_sha256=body.get("computed_sha256"),
    )


@router.post("/windows11/preflight")
async def post_windows11_preflight(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return build_windows11_preflight(
        machine=body.get("machine") or build_machine_identity(),
        windows_target=body.get("windows_target") or {},
        bios=body.get("bios") or {},
        media=body.get("media") or {},
        nvme_health=body.get("nvme_health") or {"install_allowed": False},
        previous_setup_findings=body.get("previous_setup_findings"),
        ram_test_status=str(body.get("ram_test_status") or "pending"),
        vmd_or_rst_detected=bool(body.get("vmd_or_rst_detected")),
    )


@router.post("/windows11/target-plan")
async def post_windows11_target_plan(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    gate = windows_target_destructive_gate(
        identity_confirmed=bool(body.get("identity_confirmed")),
        model=str(body.get("model") or ""),
        serial_last4=str(body.get("serial_last4") or ""),
        pci_path=str(body.get("pci_path") or ""),
        destructive_phrase_confirmed=bool(body.get("destructive_phrase_confirmed")),
        linux_nvme_unchanged_ack=bool(body.get("linux_nvme_unchanged_ack")),
    )
    return {"gate": gate, "write_allowed": False, "linux_write_allowed": False}


@router.post("/windows11/postcheck")
async def post_windows11_postcheck(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return windows_postcheck_gate(body)


@router.post("/linux/iso-check")
async def post_linux_iso_check(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return check_linux_iso(
        distro=body.get("distro"),
        version=body.get("version"),
        iso_path=body.get("iso_path"),
        sha256_expected=body.get("sha256_expected"),
        sha256_actual=body.get("sha256_actual"),
        signature_ok=body.get("signature_ok"),
        official_source=body.get("official_source"),
    )


@router.post("/linux/install-plan")
async def post_linux_install_plan(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    target = normalize_nvme_entry(body.get("linux_target") or {})
    return build_linux_partition_plan(
        target_identity=target,
        root_gib=int(body.get("root_gib") or 200),
        efi_mib=int(body.get("efi_mib") or 1024),
        encrypt_luks=bool(body.get("encrypt_luks")),
    )


@router.post("/linux/install-preflight")
async def post_linux_install_preflight(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return linux_install_preflight(
        machine=body.get("machine") or {},
        windows_postcheck_ok=bool(body.get("windows_postcheck_ok")),
        windows_target=body.get("windows_target") or {},
        linux_target=body.get("linux_target") or {},
        iso=body.get("iso") or {},
        plan=body.get("plan") or {},
        nvme_health_linux=body.get("nvme_health_linux") or {},
        ac_power=bool(body.get("ac_power", True)),
    )


@router.post("/linux/install-execute")
async def post_linux_install_execute(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return linux_install_execute_gate(
        preflight=body.get("preflight") or {},
        confirm_identity=bool(body.get("confirm_identity")),
        confirm_destructive=bool(body.get("confirm_destructive")),
        current_linux_serial_hash=str(body.get("current_linux_serial_hash") or ""),
        expected_linux_serial_hash=str(body.get("expected_linux_serial_hash") or ""),
        current_machine_id=str(body.get("current_machine_id") or ""),
        expected_machine_id=str(body.get("expected_machine_id") or ""),
    )


@router.post("/install-targets/asus")
async def post_asus_install_targets(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return build_asus_install_targets_manifest(
        windows=body.get("windows_target"),
        linux=body.get("linux_target"),
        machine_profile=str(body.get("machine_profile") or "asus_rog_gabriel"),
    )


@router.post("/win11-retest/target-binding")
async def post_win11_retest_target_binding(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    binding = build_target_role_binding(
        machine_profile=str(body.get("machine_profile") or "asus_rog_gabriel"),
        machine_fingerprint_hash=str(body.get("machine_fingerprint_hash") or ""),
        windows_target=body.get("windows_target") or {},
        linux_target=body.get("linux_target") or {},
        operator_confirmed=bool(body.get("operator_confirmed")),
        created_at=body.get("created_at"),
    )
    validation = validate_target_role_binding(binding)
    return {"binding": binding, "validation": validation}


@router.post("/win11-retest/linux-isolation")
async def post_win11_retest_linux_isolation(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return build_linux_nvme_isolation(
        method=str(body.get("method") or "unverified"),
        linux_identity_hash=str(body.get("linux_identity_hash") or ""),
        windows_identity_hash=str(body.get("windows_identity_hash") or ""),
        verified_in_winpe=bool(body.get("verified_in_winpe")),
        linux_writable_for_setup=bool(body.get("linux_writable_for_setup", True)),
        notes=str(body.get("notes") or ""),
        operator_documented=bool(body.get("operator_documented")),
    )


@router.post("/win11-retest/media-check")
async def post_win11_retest_media_check(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return build_windows_media_result(
        source=str(body.get("source") or ""),
        architecture=str(body.get("architecture") or "x64"),
        sha256=str(body.get("sha256") or ""),
        efi_boot=bool(body.get("efi_boot")),
        boot_wim=bool(body.get("boot_wim")),
        install_wim_or_esd=bool(body.get("install_wim_or_esd")),
        status=str(body.get("status") or "unknown_hash"),
        operator_override=bool(body.get("operator_override")),
    )


@router.post("/win11-retest/stage-a-preflight")
async def post_win11_retest_stage_a_preflight(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return build_stage_a_preflight(
        machine_profile=str(body.get("machine_profile") or ""),
        bios_version=str(body.get("bios_version") or ""),
        binding=body.get("binding") or {},
        isolation=body.get("isolation") or {},
        media=body.get("media") or {},
        windows_smart_critical=bool(body.get("windows_smart_critical")),
        uefi=bool(body.get("uefi", True)),
        tpm_ok=bool(body.get("tpm_ok", True)),
        ram_gb=float(body.get("ram_gb") or 0),
        collector_reachable=bool(body.get("collector_reachable")),
        setup_logs_writable=bool(body.get("setup_logs_writable")),
        ac_power=bool(body.get("ac_power", True)),
    )


@router.post("/win11-retest/destructive-auth")
async def post_win11_retest_destructive_auth(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return build_destructive_authorization(
        machine_fingerprint_hash=str(body.get("machine_fingerprint_hash") or ""),
        windows_identity_hash=str(body.get("windows_identity_hash") or ""),
        boot_id=str(body.get("boot_id") or ""),
        preflight_id=str(body.get("preflight_id") or ""),
        identity_phrase=str(body.get("identity_phrase") or ""),
        destructive_phrase=str(body.get("destructive_phrase") or ""),
        linux_offline_ack=bool(body.get("linux_offline_ack")),
        no_backup_ack=bool(body.get("no_backup_ack")),
        expires_at=str(body.get("expires_at") or ""),
    )


@router.post("/win11-retest/stage-a-decide")
async def post_win11_retest_stage_a_decide(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return decide_stage_a_outcome(
        install_succeeded=bool(body.get("install_succeeded")),
        firmware_related=body.get("firmware_related"),
        concrete_non_firmware_cause=body.get("concrete_non_firmware_cause"),
        unclear=bool(body.get("unclear")),
    )


@router.post("/win11-retest/bios335-gate")
async def post_win11_retest_bios335_gate(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return bios_335_update_gate(
        model=str(body.get("model") or ""),
        board=str(body.get("board") or ""),
        installed=str(body.get("installed") or ""),
        target=str(body.get("target") or "G513QM.335"),
        official_ez_flash_file=bool(body.get("official_ez_flash_file")),
        checksum_documented=bool(body.get("checksum_documented")),
        ac_power=bool(body.get("ac_power")),
        battery_ok=bool(body.get("battery_ok")),
        no_running_install=bool(body.get("no_running_install", True)),
        operator_approved=bool(body.get("operator_approved")),
    )


@router.post("/win11-retest/causality")
async def post_win11_retest_causality(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return evaluate_bios_causality(
        stage_a_result=str(body.get("stage_a_result") or ""),
        stage_b_result=body.get("stage_b_result"),
        same_media=bool(body.get("same_media", True)),
        same_windows_nvme=bool(body.get("same_windows_nvme", True)),
        same_linux_isolation=bool(body.get("same_linux_isolation", True)),
        other_variables_changed=bool(body.get("other_variables_changed")),
    )


@router.post("/win11-retest/postcheck-linux-gate")
async def post_win11_retest_postcheck_linux_gate(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return windows_postcheck_to_linux_gate(body.get("postcheck") or body)


@router.post("/win11-retest/dcc")
async def post_win11_retest_dcc(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return build_win11_retest_dcc(
        bios_installed=str(body.get("bios_installed") or ""),
        bios_update_result=body.get("bios_update_result"),
        causality=str(body.get("causality") or "not_tested"),
        windows_media_status=str(body.get("windows_media_status") or ""),
        windows_target_short=str(body.get("windows_target_short") or ""),
        linux_isolated=bool(body.get("linux_isolated")),
        setup_phase=str(body.get("setup_phase") or ""),
        error_code=str(body.get("error_code") or ""),
        setupdiag=str(body.get("setupdiag") or ""),
        install_result=str(body.get("install_result") or ""),
        postcheck=str(body.get("postcheck") or ""),
        linux_gate=str(body.get("linux_gate") or "blocked"),
        endstatus=str(body.get("endstatus") or "ready_for_windows_retest_bios331"),
    )
