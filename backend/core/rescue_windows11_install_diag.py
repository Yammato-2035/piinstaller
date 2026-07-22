"""Windows 11 install diagnostics: evidence scan, media check, preflight, abort matrix.

Read-only against NTFS mounts. No partitioning. write_allowed stays false until operator gate.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

CONTRACT_VERSION = 1
SCHEMA_VERSION = 1

PANTHER_RELATIVE = (
    "$WINDOWS.~BT/Sources/Panther",
    "$WINDOWS.~BT/Sources/Rollback",
    "Windows/Panther",
    "Windows/INF",
    "Windows/Logs",
)

INTERESTING_LOG_NAMES = (
    "setupact.log",
    "setuperr.log",
    "BlueBox.log",
    "SetupDiagResults.log",
    "setupapi.dev.log",
)

ERROR_CLASSES = (
    "storage_driver",
    "nvme_controller",
    "intel_vmd_or_rst",
    "partition_layout",
    "gpt_or_uefi_mismatch",
    "secure_boot_or_tpm",
    "unsupported_hardware",
    "memory_error",
    "media_corruption",
    "image_error",
    "driver_installation",
    "update_phase",
    "first_boot_phase",
    "bootloader",
    "unexpected_reboot",
    "power_or_thermal",
    "unknown",
)

_CLASS_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("intel_vmd_or_rst", re.compile(r"vmd|intel.?rst|iaStorA|iaStorV", re.I)),
    ("nvme_controller", re.compile(r"nvme|storahci|stornvme", re.I)),
    ("storage_driver", re.compile(r"storage.?driver|no.?driver.?found.*disk|0x80300024", re.I)),
    ("partition_layout", re.compile(r"partition|diskpart|0x8007045d", re.I)),
    ("gpt_or_uefi_mismatch", re.compile(r"gpt|uefi|efi.?system|csm", re.I)),
    ("secure_boot_or_tpm", re.compile(r"secure.?boot|tpm|0xC1900101", re.I)),
    ("memory_error", re.compile(r"memory.?management|whea.?logger|0x1A", re.I)),
    ("media_corruption", re.compile(r"crc|corrupt|hash.?mismatch|0x80070241", re.I)),
    ("image_error", re.compile(r"install\.wim|install\.esd|image.?apply", re.I)),
    ("driver_installation", re.compile(r"driver.?install|setupapi", re.I)),
    ("update_phase", re.compile(r"safe.?os|downlevel|specialize", re.I)),
    ("first_boot_phase", re.compile(r"oobe|first.?boot|sysprep", re.I)),
    ("bootloader", re.compile(r"bootmgr|bcd|winload", re.I)),
    ("unexpected_reboot", re.compile(r"unexpected.?reboot|bugcheck|bsod", re.I)),
    ("power_or_thermal", re.compile(r"thermal|acpi|power.?failure", re.I)),
    ("unsupported_hardware", re.compile(r"unsupported|compat(?:ibility)?\s*hold", re.I)),
]


def classify_setup_log_text(text: str) -> list[str]:
    hits: list[str] = []
    for name, pat in _CLASS_PATTERNS:
        if pat.search(text or ""):
            hits.append(name)
    return hits or ["unknown"]


def scan_windows_setup_evidence(roots: Sequence[Path]) -> dict[str, Any]:
    found: list[dict[str, Any]] = []
    classes: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for rel in PANTHER_RELATIVE:
            cand = root / rel
            if not cand.exists():
                continue
            for path in cand.rglob("*"):
                if not path.is_file():
                    continue
                name = path.name
                if name.lower() not in {n.lower() for n in INTERESTING_LOG_NAMES} and "panther" not in str(path).lower():
                    if path.suffix.lower() not in {".log", ".xml", ".txt"}:
                        continue
                try:
                    sample = path.read_text(encoding="utf-8", errors="replace")[:200_000]
                except OSError:
                    sample = ""
                hits = classify_setup_log_text(sample)
                classes.update(hits)
                found.append(
                    {
                        "path": str(path),
                        "name": name,
                        "size_bytes": path.stat().st_size if path.exists() else 0,
                        "error_classes": hits,
                        "modified": False,
                    }
                )
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "files": found,
        "error_classes": sorted(classes) if classes else ["unknown"],
        "windows_files_modified": False,
        "mount_mode": "read_only_expected",
        "status": "ok" if found else "insufficient_evidence",
    }


def check_windows_install_media(
    *,
    iso_or_root: Path,
    expected_sha256: str | None = None,
    computed_sha256: str | None = None,
) -> dict[str, Any]:
    root = iso_or_root
    exists = root.exists()
    size = root.stat().st_size if exists and root.is_file() else 0
    structure_ok = False
    arch = "unknown"
    editions: list[str] = []
    boot_wim = False
    install_image = False
    efi_boot = False

    check_root = root if root.is_dir() else None
    if check_root:
        boot_wim = (check_root / "sources" / "boot.wim").is_file()
        install_image = (check_root / "sources" / "install.wim").is_file() or (
            check_root / "sources" / "install.esd"
        ).is_file()
        efi_boot = (check_root / "efi" / "boot" / "bootx64.efi").is_file()
        structure_ok = boot_wim and install_image and efi_boot
        arch = "amd64" if efi_boot else "unknown"

    sha_status = "unknown_hash"
    if expected_sha256 and computed_sha256:
        if expected_sha256.lower() == computed_sha256.lower():
            sha_status = "valid"
        else:
            sha_status = "corrupt"
    elif expected_sha256 and not computed_sha256:
        sha_status = "unknown_hash"

    status = "valid" if structure_ok and sha_status in {"valid", "unknown_hash"} else "review_required"
    if sha_status == "corrupt" or (exists and root.is_dir() and not structure_ok):
        status = "corrupt" if sha_status == "corrupt" else "review_required"
    if not exists:
        status = "review_required"

    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "path": str(root),
        "exists": exists,
        "size_bytes": size,
        "sha256_status": sha_status,
        "expected_sha256": expected_sha256,
        "structure_ok": structure_ok,
        "boot_wim": boot_wim,
        "install_image": install_image,
        "efi_boot": efi_boot,
        "architecture": arch,
        "editions": editions,
        "status": status,
        "install_start_allowed": status == "valid" and sha_status != "corrupt",
    }


def build_windows11_preflight(
    *,
    machine: Mapping[str, Any],
    windows_target: Mapping[str, Any],
    bios: Mapping[str, Any],
    media: Mapping[str, Any],
    nvme_health: Mapping[str, Any],
    previous_setup_findings: Sequence[str] | None = None,
    ram_test_status: str = "pending",
    vmd_or_rst_detected: bool = False,
) -> dict[str, Any]:
    requirements = {
        "uefi": bios.get("boot_mode") == "uefi",
        "gpt_target": True,
        "secure_boot": bios.get("secure_boot") in {"enabled", "disabled", "unknown"},
        "tpm": str(bios.get("tpm") or "") in {"2.0", "1.2", "unknown"},
        "nvme_healthy": nvme_health.get("install_allowed") is True,
        "media_valid": media.get("install_start_allowed") is True,
        "machine_known": machine.get("expected_profile") not in {None, "unknown"}
        and machine.get("confidence") != "low",
    }
    required_actions: list[str] = []
    if not requirements["uefi"]:
        required_actions.append("enable_uefi_disable_csm")
    if bios.get("secure_boot") == "unknown":
        required_actions.append("verify_secure_boot")
    if bios.get("tpm") == "missing":
        required_actions.append("enable_tpm_2_0")
        requirements["tpm"] = False
    if vmd_or_rst_detected:
        required_actions.append("review_intel_vmd_rst_ahci")
    if ram_test_status == "pending":
        required_actions.append("complete_or_accept_ram_smoke")
    if not requirements["nvme_healthy"]:
        required_actions.append("replace_or_review_windows_nvme")
    if media.get("status") == "corrupt":
        required_actions.append("replace_windows_install_media")

    blocked = (
        not requirements["machine_known"]
        or not requirements["nvme_healthy"]
        or media.get("status") == "corrupt"
        or bios.get("tpm") == "missing"
        or not requirements["uefi"]
    )
    review = (not blocked) and (required_actions or ram_test_status == "pending" or vmd_or_rst_detected)
    status = "blocked" if blocked else ("review_required" if review else "ready")

    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "status": status,
        "machine": dict(machine),
        "windows_target": dict(windows_target),
        "requirements": requirements,
        "storage_controller": {"vmd_or_rst_detected": vmd_or_rst_detected},
        "bios": dict(bios),
        "media": dict(media),
        "previous_setup_findings": list(previous_setup_findings or []),
        "required_actions": required_actions,
        "ram_test_status": ram_test_status,
        "write_allowed": False,
        "data_backup_required": False,
        "data_backup_note": "Operator documented: no user data must be preserved on Windows NVMe.",
    }


def build_abort_cause_matrix(evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    classes = set(evidence.get("error_classes") or [])
    hypotheses = [
        "NVMe defekt",
        "NVMe-Firmware",
        "Intel VMD/RST",
        "fehlender Storage-Treiber",
        "BIOS veraltet",
        "UEFI/GPT-Fehler",
        "Secure Boot/TPM",
        "Installationsmedium defekt",
        "RAM instabil",
        "Temperatur/Stromversorgung",
        "Windows-Image/Edition",
        "zweite NVMe beeinflusst Setup",
        "Bootloader/EFI",
    ]
    mapping = {
        "NVMe defekt": ("media_errors" in str(evidence).lower(), "nvme_controller" in classes),
        "Intel VMD/RST": ("intel_vmd_or_rst" in classes, False),
        "fehlender Storage-Treiber": ("storage_driver" in classes, False),
        "UEFI/GPT-Fehler": ("gpt_or_uefi_mismatch" in classes, False),
        "Secure Boot/TPM": ("secure_boot_or_tpm" in classes, False),
        "Installationsmedium defekt": ("media_corruption" in classes, False),
        "RAM instabil": ("memory_error" in classes, False),
        "Temperatur/Stromversorgung": ("power_or_thermal" in classes, False),
        "Bootloader/EFI": ("bootloader" in classes, False),
    }
    rows: list[dict[str, Any]] = []
    for hyp in hypotheses:
        for_ev, against = mapping.get(hyp, (False, False))
        if for_ev and not against:
            status = "supported"
        elif against:
            status = "unlikely"
        elif for_ev is False and hyp in mapping:
            status = "insufficient_evidence"
        else:
            status = "insufficient_evidence"
        rows.append(
            {
                "hypothesis": hyp,
                "evidence_for": "log_class_match" if for_ev else "",
                "evidence_against": "contradiction" if against else "",
                "status": status,
            }
        )
    return rows


def windows_target_destructive_gate(
    *,
    identity_confirmed: bool,
    model: str,
    serial_last4: str,
    pci_path: str,
    destructive_phrase_confirmed: bool,
    linux_nvme_unchanged_ack: bool,
) -> dict[str, Any]:
    ok = all(
        [
            identity_confirmed,
            bool(model),
            len(serial_last4) == 4,
            bool(pci_path),
            destructive_phrase_confirmed,
            linux_nvme_unchanged_ack,
        ]
    )
    return {
        "ok": ok,
        "write_allowed": False if not ok else False,  # still false until separate execute handoff
        "plan_allowed": ok,
        "requires": [
            "identity_confirmation",
            "destructive_confirmation",
            "linux_nvme_unchanged_ack",
        ],
        "note": "Windows Setup should preferably create partitions; rescue stick only plans wipe.",
    }


def windows_postcheck_gate(postcheck: Mapping[str, Any]) -> dict[str, Any]:
    required = [
        postcheck.get("windows_booted") is True,
        postcheck.get("uefi_boot") is True,
        postcheck.get("efi_on_windows_nvme") is True,
        postcheck.get("reboot_ok") is True,
        postcheck.get("target_nvme_confirmed") is True,
        not postcheck.get("critical_storage_errors"),
    ]
    ok = all(required)
    return {
        "ok": ok,
        "linux_install_gate": "ready" if ok else "blocked",
        "missing": [k for k, v in [
            ("windows_booted", postcheck.get("windows_booted")),
            ("uefi_boot", postcheck.get("uefi_boot")),
            ("efi_on_windows_nvme", postcheck.get("efi_on_windows_nvme")),
            ("reboot_ok", postcheck.get("reboot_ok")),
            ("target_nvme_confirmed", postcheck.get("target_nvme_confirmed")),
            ("no_critical_storage_errors", not postcheck.get("critical_storage_errors")),
        ] if not v],
    }


def plan_hash(plan: Mapping[str, Any]) -> str:
    blob = repr(sorted(plan.items())).encode()
    return hashlib.sha256(blob).hexdigest()
