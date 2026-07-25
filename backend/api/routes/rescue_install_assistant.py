"""API routes for PI-RS-INSTALL-ASSISTANT-001 (disk roles, diagnosis, Mint dry-run/handoff)."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Body

from core.rescue_bios_official_compare import check_latest_official_bios
from core.rescue_gabriel_ops_policy import (
    authorize_linux_target_wipe,
    gabriel_capabilities,
    gabriel_ops_enabled,
)
from core.rescue_install_assistant_grub import (
    generate_gabriel_install_grub_cfg,
    validate_gabriel_install_grub,
)
from core.rescue_install_bios_session import build_bios_session, export_bios_session_evidence
from core.rescue_install_diagnosis import (
    build_install_diagnosis,
    redact_install_diagnosis_for_upload,
)
from core.rescue_install_distro_profiles import (
    download_policy_gate,
    list_distro_profiles,
    resolve_iso_status,
    verify_cached_iso,
)
from core.rescue_linux_second_nvme import (
    build_linux_partition_plan,
    check_linux_iso,
    linux_install_execute_gate,
    linux_install_preflight,
    post_install_verify,
)
from core.rescue_nvme_install_target import (
    bind_role_by_identity,
    build_asus_install_targets_manifest,
    evaluate_nvme_health,
    inventory_from_nvme_list_json,
    normalize_nvme_entry,
    resolve_role_after_device_rename,
)

router = APIRouter(prefix="/install-assistant", tags=["rescue-install-assistant"])


@router.get("/status")
async def get_install_assistant_status() -> dict[str, Any]:
    return {
        "contract": "install_assistant_v1",
        "capability": "preview",
        "execute_default": False,
        "windows_nvme_write_allowed": False,
        "auto_bios_flash_allowed": False,
        "p0_distro": "linux_mint",
        "phases": ["A0", "A1", "A2", "A3", "A4", "A5"],
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


@router.post("/storage/bind-role")
async def post_bind_role(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    inventory = list(body.get("devices") or body.get("inventory") or [])
    return bind_role_by_identity(
        inventory,
        serial_hash=str(body.get("serial_hash") or ""),
        role=str(body.get("role") or "unassigned"),
        model=body.get("model"),
        size_bytes=body.get("size_bytes"),
        pci_path=body.get("pci_path") or body.get("pci_address"),
        allow_rescue_usb=bool(body.get("allow_rescue_usb")),
    )


@router.post("/storage/resolve-roles")
async def post_resolve_roles(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    inventory = list(body.get("devices") or body.get("inventory") or [])
    targets = body.get("targets") or {
        "windows_target": body.get("windows_target") or body.get("windows_system"),
        "linux_target": body.get("linux_target"),
    }
    return resolve_role_after_device_rename(inventory, targets)


@router.post("/storage/health")
async def post_storage_health(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    entry = normalize_nvme_entry(body.get("entry") or body)
    health = evaluate_nvme_health(entry)
    health["write_allowed"] = False
    return health


@router.post("/install-targets")
async def post_install_targets(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return build_asus_install_targets_manifest(
        windows=body.get("windows_target") or body.get("windows_system"),
        linux=body.get("linux_target"),
        machine_profile=str(body.get("machine_profile") or "asus_rog_gabriel"),
    )


@router.post("/diagnosis")
async def post_install_diagnosis(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return build_install_diagnosis(
        assessment=body.get("assessment"),
        disk_roles=body.get("disk_roles"),
        bios_compare=body.get("bios_compare"),
        iso_status=body.get("iso_status"),
        secure_boot_enabled=body.get("secure_boot_enabled"),
        boot_device_role=body.get("boot_device_role"),
        nvme_visible_in_installer=body.get("nvme_visible_in_installer"),
        aer_flood=body.get("aer_flood"),
        locale=str(body.get("locale") or "de"),
    )


@router.post("/diagnosis/redact")
async def post_diagnosis_redact(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    diagnosis = body.get("diagnosis") or body
    return {
        "redacted": redact_install_diagnosis_for_upload(diagnosis),
        "dry_run_local": True,
        "upload_path": "assessment_v2_redacted",
    }


@router.get("/distro/profiles")
async def get_distro_profiles() -> dict[str, Any]:
    return list_distro_profiles()


@router.post("/distro/iso-status")
async def post_iso_status(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return resolve_iso_status(
        profile_id=str(body.get("profile_id") or body.get("distro") or "linux_mint"),
        logs_root=body.get("logs_root"),
        iso_path=body.get("iso_path"),
        sha256_expected=body.get("sha256_expected"),
        sha256_actual=body.get("sha256_actual"),
    )


@router.post("/distro/iso-verify")
async def post_iso_verify(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return verify_cached_iso(
        profile_id=str(body.get("profile_id") or "linux_mint"),
        iso_path=str(body.get("iso_path") or ""),
        sha256_expected=str(body.get("sha256_expected") or ""),
        compute_actual=bool(body.get("compute_actual")),
        sha256_actual=body.get("sha256_actual"),
    )


@router.post("/distro/iso-check")
async def post_iso_check(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return check_linux_iso(
        distro=body.get("distro") or body.get("profile_id"),
        version=body.get("version"),
        iso_path=body.get("iso_path"),
        sha256_expected=body.get("sha256_expected"),
        sha256_actual=body.get("sha256_actual"),
        signature_ok=body.get("signature_ok"),
        official_source=body.get("official_source"),
    )


@router.post("/distro/download-policy")
async def post_download_policy(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return download_policy_gate(
        operator_started=bool(body.get("operator_started")),
        profile_id=str(body.get("profile_id") or "linux_mint"),
    )


@router.post("/linux/install-plan")
async def post_linux_install_plan(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    target = normalize_nvme_entry(body.get("linux_target") or body.get("target") or {})
    plan = build_linux_partition_plan(
        target_identity=target,
        root_gib=int(body.get("root_gib") or 200),
        efi_mib=int(body.get("efi_mib") or 1024),
        encrypt_luks=bool(body.get("encrypt_luks")),
        allow_windows_role_as_target=bool(body.get("allow_windows_role_as_target")),
    )
    plan["partitionshelfer"] = {
        "write_allowed": False,
        "preview_only": True,
        "handoff": "apps/partitionshelfer preview contracts",
    }
    return plan


@router.post("/linux/install-preflight")
async def post_linux_install_preflight(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return linux_install_preflight(
        machine=body.get("machine") or {},
        windows_postcheck_ok=bool(body.get("windows_postcheck_ok")),
        windows_target=body.get("windows_target") or body.get("windows_system") or {},
        linux_target=body.get("linux_target") or {},
        iso=body.get("iso") or {},
        plan=body.get("plan") or {},
        nvme_health_linux=body.get("nvme_health_linux") or {},
        ac_power=bool(body.get("ac_power", True)),
        backup_ack=bool(body.get("backup_ack")),
    )


@router.post("/linux/install-execute")
async def post_linux_install_execute(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Handoff gate — executed=False for automatic wipe; may authorize Gabriel linux_target wipe."""
    result = linux_install_execute_gate(
        preflight=body.get("preflight") or {},
        confirm_identity=bool(body.get("confirm_identity")),
        confirm_destructive=bool(body.get("confirm_destructive")),
        current_linux_serial_hash=str(body.get("current_linux_serial_hash") or ""),
        expected_linux_serial_hash=str(body.get("expected_linux_serial_hash") or ""),
        current_machine_id=str(body.get("current_machine_id") or ""),
        expected_machine_id=str(body.get("expected_machine_id") or ""),
        operator_phrase=body.get("operator_phrase"),
        expected_operator_phrase=str(
            body.get("expected_operator_phrase") or "INSTALL LINUX TARGET"
        ),
        gabriel_ops_allowed=bool(body.get("gabriel_ops_allowed")),
        authorize_linux_wipe=bool(body.get("authorize_linux_wipe")),
        linux_wipe_phrase=body.get("linux_wipe_phrase"),
    )
    result["executed"] = False
    result["write_allowed"] = bool(result.get("wipe_authorized"))
    result["windows_nvme_write_allowed"] = False
    return result


@router.post("/gabriel/wipe-authorize")
async def post_gabriel_wipe_authorize(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return authorize_linux_target_wipe(
        gabriel_ops=gabriel_ops_enabled(
            cmdline=str(body.get("cmdline") or ""),
            machine=body.get("machine") or {},
            operator_explicit=bool(body.get("operator_explicit")),
        ),
        confirm_identity=bool(body.get("confirm_identity")),
        confirm_destructive=bool(body.get("confirm_destructive")),
        operator_phrase=str(body.get("operator_phrase") or ""),
        linux_serial_hash=str(body.get("linux_serial_hash") or ""),
        expected_linux_serial_hash=str(body.get("expected_linux_serial_hash") or ""),
        windows_serial_hash=str(body.get("windows_serial_hash") or ""),
    )


@router.get("/gabriel/grub-preview")
async def get_gabriel_grub_preview() -> dict[str, Any]:
    cfg = generate_gabriel_install_grub_cfg()
    return {
        "grub_cfg": cfg,
        "validation": validate_gabriel_install_grub(cfg),
        "capabilities": gabriel_capabilities(
            machine={"board_name": "G513QM", "gabriel_bound": True},
            operator_explicit=True,
        ),
    }


@router.post("/linux/post-verify")
async def post_linux_post_verify(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    return post_install_verify(
        linux_target=body.get("linux_target") or {},
        windows_target=body.get("windows_target") or body.get("windows_system") or {},
        linux_bootable=bool(body.get("linux_bootable")),
        windows_unchanged=bool(body.get("windows_unchanged")),
        evidence_paths=list(body.get("evidence_paths") or []),
    )


@router.post("/firmware/check-latest")
async def post_firmware_check_latest(body: Optional[dict[str, Any]] = Body(default=None)) -> dict[str, Any]:
    body = body or {}
    return check_latest_official_bios(
        machine=body.get("machine") or {},
        online=bool(body.get("online", True)),
    )


@router.post("/bios/session")
async def post_bios_session(body: Optional[dict[str, Any]] = Body(default=None)) -> dict[str, Any]:
    body = body or {}
    return build_bios_session(
        machine=body.get("machine") or {},
        online=bool(body.get("online", True)),
        locale=str(body.get("locale") or "de"),
        skip_reason=body.get("skip_reason"),
    )


@router.post("/bios/session/export")
async def post_bios_session_export(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    session = body.get("session") or body
    return export_bios_session_evidence(session)
