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
