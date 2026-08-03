"""
Hardware contracts — normalized, read-only hardware/driver/firmware models.

PI-RS-HW-COMPAT-PROVISION-001 Phase 2.

Canonical vocabulary for all new hardware-detection modules (CPU, mainboard, GPU,
USB, input, printer/scanner, Raspberry Pi, driver/firmware resolver, carrier and
provisioning planners). This module defines *shapes only* — no shell execution,
no sysfs reads. Detection modules build these dataclasses; this module never
imports detection modules (one-directional dependency, avoids cycles).

Key rule (see spec PHASE 2): "erkannt" != "betriebsbereit". ``OperationalStatus``
intentionally keeps detection, driver, firmware and readiness as separate stages;
callers must not collapse them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

HARDWARE_CONTRACTS_VERSION = 1


class Bus(str, Enum):
    PCI = "pci"
    USB = "usb"
    PLATFORM = "platform"
    I2C = "i2c"
    SPI = "spi"
    INPUT = "input"
    NETWORK = "network"
    VIRTUAL = "virtual"
    UNKNOWN = "unknown"


class FirmwareStatus(str, Enum):
    PRESENT = "present"
    MISSING = "missing"
    UNKNOWN = "unknown"
    NOT_REQUIRED = "not_required"


class OperationalStatus(str, Enum):
    """Stable, ordered detection→readiness pipeline. Do not collapse stages."""

    DETECTED = "detected"
    IDENTIFIED = "identified"
    DRIVER_AVAILABLE = "driver_available"
    DRIVER_LOADED = "driver_loaded"
    FIRMWARE_PRESENT = "firmware_present"
    FIRMWARE_MISSING = "firmware_missing"
    READY = "ready"
    LIMITED = "limited"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
    REVIEW_REQUIRED = "review_required"


# Device-level summary status used by HardwareDevice.operational_status (spec JSON shape).
# Superset that also allows the "driver_missing" / "firmware_missing" summary terms used
# in the device JSON example — kept distinct from the pipeline-stage OperationalStatus
# used for issue/telemetry aggregation.
DEVICE_OPERATIONAL_STATUS_VALUES: frozenset[str] = frozenset(
    {
        "ready",
        "limited",
        "driver_missing",
        "firmware_missing",
        "blocked",
        "unknown",
        "unsupported",
    }
)


class SupportLevel(str, Enum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    EXPERIMENTAL = "experimental"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class HardwareEvidenceReference:
    """Pointer to an evidence artifact (doc, JSON run, physical test log)."""

    kind: str  # e.g. "doc", "run_json", "physical_test", "catalog_entry"
    path: str
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "path": self.path, "description": self.description}


@dataclass(frozen=True)
class HardwareCapability:
    """A named capability bit a device may expose (e.g. "color_print", "duplex")."""

    name: str
    supported: bool
    confidence: str = "unknown"  # "high" | "medium" | "low" | "unknown"
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "supported": self.supported,
            "confidence": self.confidence,
            "source": self.source,
        }


@dataclass(frozen=True)
class HardwareIssue:
    """A detected problem or limitation for a device."""

    code: str
    severity: str = "info"  # "info" | "warning" | "blocking"
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "severity": self.severity, "message": self.message}


@dataclass(frozen=True)
class HardwareRecommendation:
    """A safe, non-destructive next-step suggestion for a device."""

    code: str
    message: str | None = None
    requires_operator_action: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "requires_operator_action": self.requires_operator_action,
        }


@dataclass(frozen=True)
class HardwareDriverState:
    """Driver-layer state for one device, kept separate from firmware/readiness."""

    kernel_driver_in_use: str | None = None
    kernel_driver_candidates: tuple[str, ...] = field(default_factory=tuple)
    kernel_modules_loaded: tuple[str, ...] = field(default_factory=tuple)
    driver_type: str | None = None  # kernel_in_tree|userspace|firmware_only|proprietary_optional|unsupported
    package_candidates: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kernel_driver_in_use": self.kernel_driver_in_use,
            "kernel_driver_candidates": list(self.kernel_driver_candidates),
            "kernel_modules_loaded": list(self.kernel_modules_loaded),
            "driver_type": self.driver_type,
            "package_candidates": list(self.package_candidates),
        }


@dataclass(frozen=True)
class HardwareFirmwareState:
    """Firmware-layer state for one device, kept separate from driver/readiness."""

    status: FirmwareStatus = FirmwareStatus.UNKNOWN
    candidates: tuple[str, ...] = field(default_factory=tuple)
    missing_firmware_files: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "candidates": list(self.candidates),
            "missing_firmware_files": list(self.missing_firmware_files),
        }


@dataclass(frozen=True)
class HardwarePrivacyFlags:
    contains_serial: bool = False
    serial_redacted: bool = True
    telemetry_allowed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "contains_serial": self.contains_serial,
            "serial_redacted": self.serial_redacted,
            "telemetry_allowed": self.telemetry_allowed,
        }


@dataclass(frozen=True)
class HardwareDevice:
    """Canonical normalized hardware device — see spec PHASE 2 JSON shape."""

    device_id: str
    device_class: str
    subclass: str | None = None
    bus: Bus = Bus.UNKNOWN
    vendor_id: str | None = None
    product_id: str | None = None
    subsystem_vendor_id: str | None = None
    subsystem_product_id: str | None = None
    vendor_name: str | None = None
    product_name: str | None = None
    model_name: str | None = None
    kernel_modalias: str | None = None
    driver: HardwareDriverState = field(default_factory=HardwareDriverState)
    firmware: HardwareFirmwareState = field(default_factory=HardwareFirmwareState)
    operational_status: str = "unknown"
    detection_confidence: float = 0.0
    capabilities: tuple[HardwareCapability, ...] = field(default_factory=tuple)
    issues: tuple[HardwareIssue, ...] = field(default_factory=tuple)
    recommendations: tuple[HardwareRecommendation, ...] = field(default_factory=tuple)
    evidence: tuple[HardwareEvidenceReference, ...] = field(default_factory=tuple)
    privacy: HardwarePrivacyFlags = field(default_factory=HardwarePrivacyFlags)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_class": self.device_class,
            "subclass": self.subclass,
            "bus": self.bus.value if isinstance(self.bus, Bus) else str(self.bus),
            "vendor_id": self.vendor_id,
            "product_id": self.product_id,
            "subsystem_vendor_id": self.subsystem_vendor_id,
            "subsystem_product_id": self.subsystem_product_id,
            "vendor_name": self.vendor_name,
            "product_name": self.product_name,
            "model_name": self.model_name,
            "kernel_modalias": self.kernel_modalias,
            "kernel_driver_in_use": self.driver.kernel_driver_in_use,
            "kernel_driver_candidates": list(self.driver.kernel_driver_candidates),
            "kernel_modules_loaded": list(self.driver.kernel_modules_loaded),
            "firmware_status": self.firmware.status.value,
            "firmware_candidates": list(self.firmware.candidates),
            "operational_status": self.operational_status,
            "detection_confidence": self.detection_confidence,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "issues": [i.to_dict() for i in self.issues],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "evidence": [e.to_dict() for e in self.evidence],
            "privacy": self.privacy.to_dict(),
        }


@dataclass(frozen=True)
class PeripheralCapability:
    """One function of a (possibly composite/multi-function) peripheral device.

    Example: an HP MFP device has separate PeripheralCapability entries for
    "printer", "scanner", "storage_card_reader" — each with its own status, never
    a shared/implied status (spec PHASE 6/8 requirement).
    """

    function: str  # "printer" | "scanner" | "storage_card_reader" | "fax" | ...
    operational_status: str = "unknown"
    detection_confidence: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "function": self.function,
            "operational_status": self.operational_status,
            "detection_confidence": self.detection_confidence,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class PlatformIdentity:
    """Identity of the host platform (x86 board or Raspberry Pi variant)."""

    platform_class: str  # "desktop" | "laptop" | "server" | "single_board_computer" | "unknown"
    architecture: str = "unknown"  # x86_64|i686|armv7|aarch64|unknown
    system_vendor: str | None = None
    system_product: str | None = None
    baseboard_vendor: str | None = None
    baseboard_product: str | None = None
    bios_version: str | None = None
    bios_date: str | None = None
    is_raspberry_pi: bool = False
    raspberry_pi_model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform_class": self.platform_class,
            "architecture": self.architecture,
            "system_vendor": self.system_vendor,
            "system_product": self.system_product,
            "baseboard_vendor": self.baseboard_vendor,
            "baseboard_product": self.baseboard_product,
            "bios_version": self.bios_version,
            "bios_date": self.bios_date,
            "is_raspberry_pi": self.is_raspberry_pi,
            "raspberry_pi_model": self.raspberry_pi_model,
        }


@dataclass(frozen=True)
class HardwareInventory:
    """Top-level read-only hardware inventory snapshot."""

    run_id: str
    collected_at: str
    platform: PlatformIdentity
    devices: tuple[HardwareDevice, ...] = field(default_factory=tuple)
    capability_missing_tools: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = "hardware-inventory.v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "collected_at": self.collected_at,
            "platform": self.platform.to_dict(),
            "devices": [d.to_dict() for d in self.devices],
            "capability_missing_tools": list(self.capability_missing_tools),
            "device_count": len(self.devices),
        }


def build_hardware_contracts_diagnostics() -> dict[str, Any]:
    """Lightweight, read-only self-description (no hardware access)."""
    return {
        "contracts_version": HARDWARE_CONTRACTS_VERSION,
        "module": "core.hardware_contracts",
        "models": [
            "HardwareInventory",
            "HardwareDevice",
            "HardwareDriverState",
            "HardwareFirmwareState",
            "HardwareCapability",
            "HardwareIssue",
            "HardwareRecommendation",
            "HardwareEvidenceReference",
            "PlatformIdentity",
            "PeripheralCapability",
            "HardwarePrivacyFlags",
        ],
        "enums": ["Bus", "FirmwareStatus", "OperationalStatus", "SupportLevel"],
        "read_only": True,
        "writes_allowed": False,
        "shell_execution": False,
    }


__all__ = [
    "HARDWARE_CONTRACTS_VERSION",
    "Bus",
    "FirmwareStatus",
    "OperationalStatus",
    "SupportLevel",
    "DEVICE_OPERATIONAL_STATUS_VALUES",
    "HardwareEvidenceReference",
    "HardwareCapability",
    "HardwareIssue",
    "HardwareRecommendation",
    "HardwareDriverState",
    "HardwareFirmwareState",
    "HardwarePrivacyFlags",
    "HardwareDevice",
    "PeripheralCapability",
    "PlatformIdentity",
    "HardwareInventory",
    "build_hardware_contracts_diagnostics",
]
