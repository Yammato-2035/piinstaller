"""
Hardware baseline diagnostic contracts — early, safe risk-check vocabulary.

PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 2.

Canonical shapes for the new early hardware baseline layer (memory, CPU, GPU,
HDD, SATA-SSD, NVMe) and the startup baseline gate. This module defines
*shapes only* — no shell execution, no sysfs reads, no timing. Diagnostic
modules (``memory_baseline_diagnostics.py`` etc.) build these dataclasses.

Terminology rule (spec preamble): a short baseline test must never claim
hardware is guaranteed fault-free, that RAM/CPU/GPU is fully verified, or that
a long-running test has passed. Only the status vocabulary below is allowed.
This module intentionally does **not** define a "healthy"/"ok"/"passed"
status — see ``BaselineStatus``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

HARDWARE_BASELINE_CONTRACTS_VERSION = 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BaselineSubsystem(str, Enum):
    MEMORY = "memory"
    CPU = "cpu"
    GPU = "gpu"
    HDD = "hdd"
    SATA_SSD = "sata_ssd"
    NVME = "nvme"


class BaselineStatus(str, Enum):
    """Allowed baseline result vocabulary (spec preamble). No "healthy"/"passed"."""

    NO_IMMEDIATE_ISSUE_DETECTED = "no_immediate_issue_detected"
    IMMEDIATE_ISSUE_DETECTED = "immediate_issue_detected"
    DEGRADED = "degraded"
    REVIEW_REQUIRED = "review_required"
    EXTENDED_TEST_RECOMMENDED = "extended_test_recommended"
    EXTENDED_TEST_REQUIRED = "extended_test_required"
    TEST_UNAVAILABLE = "test_unavailable"
    NOT_TESTED = "not_tested"


class BaselineSeverity(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    GRAY = "gray"


#: Maps a BaselineStatus to its default traffic-light severity. Individual
#: modules may still choose a stricter severity for a specific finding.
DEFAULT_SEVERITY_BY_STATUS: dict[str, str] = {
    BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value: BaselineSeverity.GREEN.value,
    BaselineStatus.EXTENDED_TEST_RECOMMENDED.value: BaselineSeverity.YELLOW.value,
    BaselineStatus.DEGRADED.value: BaselineSeverity.YELLOW.value,
    BaselineStatus.REVIEW_REQUIRED.value: BaselineSeverity.YELLOW.value,
    BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value: BaselineSeverity.RED.value,
    BaselineStatus.EXTENDED_TEST_REQUIRED.value: BaselineSeverity.RED.value,
    BaselineStatus.TEST_UNAVAILABLE.value: BaselineSeverity.GRAY.value,
    BaselineStatus.NOT_TESTED.value: BaselineSeverity.GRAY.value,
}

#: Forbidden claim strings (spec preamble) — used by tests/validators, never
#: emitted by any baseline module. Kept here as the single source of truth.
FORBIDDEN_BASELINE_CLAIMS: frozenset[str] = frozenset(
    {
        "hardware guaranteed fault-free",
        "hardware_guaranteed_fault_free",
        "ram fully tested",
        "ram_fully_tested",
        "ram_fully_verified",
        "disk without defect",
        "disk_without_defect",
        "gpu fully stable",
        "gpu_fully_stable",
        "gpu_fully_verified",
        "cpu fully stable",
        "cpu_fully_stable",
        "cpu_fully_verified",
        "long-term test passed",
        "long_term_test_passed",
        "extended_test_passed",
        "all_storage_healthy",
        "hardware_faults_excluded",
        "memory_fully_verified",
    }
)


@dataclass(frozen=True)
class HardwareMetric:
    """One measured or observed value, never itself a pass/fail claim."""

    name: str
    value: Any
    unit: str | None = None
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "value": self.value, "unit": self.unit, "source": self.source}


@dataclass(frozen=True)
class HardwareFinding:
    """A structured, code-based baseline finding (never free-text guessing)."""

    code: str
    severity: str = BaselineSeverity.GRAY.value
    message: str | None = None
    evidence: tuple[str, ...] = field(default_factory=tuple)
    # Optional 006B fields — severity stays the traffic light; action_blocking
    # separates restore/install impact from informational / expected_by_profile.
    confidence: float | None = None
    action_blocking: bool | None = None
    category: str | None = None  # informational|expected_by_profile|degraded|warning|critical

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "evidence": list(self.evidence),
        }
        if self.confidence is not None:
            out["confidence"] = self.confidence
        if self.action_blocking is not None:
            out["action_blocking"] = self.action_blocking
        if self.category is not None:
            out["category"] = self.category
        return out


@dataclass(frozen=True)
class ExtendedTestRecommendation:
    """Preview-only pointer to a longer test — never started by this phase."""

    recommended: bool = False
    required: bool = False
    test_type: str | None = None  # "memtest86plus"|"cpu_stress"|"gpu_render_stress"|"smart_self_test_short"|...
    estimated_duration: str | None = None
    operator_confirmation_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommended": self.recommended,
            "required": self.required,
            "test_type": self.test_type,
            "estimated_duration": self.estimated_duration,
            "operator_confirmation_required": self.operator_confirmation_required,
        }


@dataclass(frozen=True)
class HardwareSubsystemResult:
    """Baseline result for one subsystem (memory|cpu|gpu|hdd|sata_ssd|nvme)."""

    subsystem: str
    status: str = BaselineStatus.NOT_TESTED.value
    severity: str = BaselineSeverity.GRAY.value
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int = 0
    checks_run: tuple[str, ...] = field(default_factory=tuple)
    checks_skipped: tuple[str, ...] = field(default_factory=tuple)
    metrics: tuple[HardwareMetric, ...] = field(default_factory=tuple)
    findings: tuple[HardwareFinding, ...] = field(default_factory=tuple)
    recommendations: tuple[str, ...] = field(default_factory=tuple)
    extended_test: ExtendedTestRecommendation = field(default_factory=ExtendedTestRecommendation)
    evidence: tuple[str, ...] = field(default_factory=tuple)
    device_id: str | None = None  # for per-device storage results (hdd/sata_ssd/nvme)

    def to_dict(self) -> dict[str, Any]:
        out = {
            "subsystem": self.subsystem,
            "status": self.status,
            "severity": self.severity,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "checks_run": list(self.checks_run),
            "checks_skipped": list(self.checks_skipped),
            "metrics": {m.name: m.to_dict() for m in self.metrics},
            "findings": [f.to_dict() for f in self.findings],
            "recommendations": list(self.recommendations),
            "extended_test": self.extended_test.to_dict(),
            "evidence": list(self.evidence),
        }
        if self.device_id is not None:
            out["device_id"] = self.device_id
        return out


@dataclass(frozen=True)
class HardwareBaselineGate:
    """Aggregated safety decision derived from all subsystem baseline results."""

    status: str = "incomplete"  # passed|review_required|blocked|incomplete
    memory_status: str = BaselineStatus.NOT_TESTED.value
    cpu_status: str = BaselineStatus.NOT_TESTED.value
    gpu_status: str = BaselineStatus.NOT_TESTED.value
    storage_status: str = BaselineStatus.NOT_TESTED.value
    backup_allowed: bool = True
    restore_allowed: bool = False
    os_installation_allowed: bool = False
    gui_mode_allowed: bool = True
    reasons: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    required_next_actions: tuple[str, ...] = field(default_factory=tuple)
    # Severity vs action impact (006B) — operations may stay allowed under yellow review.
    action_impact: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "memory_status": self.memory_status,
            "cpu_status": self.cpu_status,
            "gpu_status": self.gpu_status,
            "storage_status": self.storage_status,
            "backup_allowed": self.backup_allowed,
            "restore_allowed": self.restore_allowed,
            "os_installation_allowed": self.os_installation_allowed,
            "gui_mode_allowed": self.gui_mode_allowed,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "required_next_actions": list(self.required_next_actions),
            "action_impact": dict(self.action_impact),
        }


@dataclass(frozen=True)
class HardwareBaselineResult:
    """Top-level result of one startup baseline run (all subsystems + gate)."""

    run_id: str
    collected_at: str
    mode: str = "quick"  # "quick" | "extended_preview"
    subsystems: tuple[HardwareSubsystemResult, ...] = field(default_factory=tuple)
    gate: HardwareBaselineGate = field(default_factory=HardwareBaselineGate)
    total_duration_ms: int = 0
    schema_version: str = "hardware-baseline-result.v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "collected_at": self.collected_at,
            "mode": self.mode,
            "subsystems": [s.to_dict() for s in self.subsystems],
            "gate": self.gate.to_dict(),
            "total_duration_ms": self.total_duration_ms,
        }


def contains_forbidden_baseline_claim(text: str) -> bool:
    """Case-insensitive, space/dash/underscore-insensitive substring check
    against ``FORBIDDEN_BASELINE_CLAIMS``."""
    low = text.lower().replace("-", "_").replace(" ", "_")
    return any(claim.replace("-", "_").replace(" ", "_") in low for claim in FORBIDDEN_BASELINE_CLAIMS)


def build_hardware_baseline_contracts_diagnostics() -> dict[str, Any]:
    """Lightweight, read-only self-description (no hardware access)."""
    return {
        "contracts_version": HARDWARE_BASELINE_CONTRACTS_VERSION,
        "module": "core.hardware_baseline_contracts",
        "models": [
            "HardwareBaselineResult",
            "HardwareSubsystemResult",
            "HardwareMetric",
            "HardwareFinding",
            "HardwareBaselineGate",
            "ExtendedTestRecommendation",
        ],
        "enums": ["BaselineSubsystem", "BaselineStatus", "BaselineSeverity"],
        "allowed_status_values": [s.value for s in BaselineStatus],
        "read_only": True,
        "writes_allowed": False,
        "shell_execution": False,
    }


__all__ = [
    "HARDWARE_BASELINE_CONTRACTS_VERSION",
    "BaselineSubsystem",
    "BaselineStatus",
    "BaselineSeverity",
    "DEFAULT_SEVERITY_BY_STATUS",
    "FORBIDDEN_BASELINE_CLAIMS",
    "HardwareMetric",
    "HardwareFinding",
    "ExtendedTestRecommendation",
    "HardwareSubsystemResult",
    "HardwareBaselineGate",
    "HardwareBaselineResult",
    "contains_forbidden_baseline_claim",
    "build_hardware_baseline_contracts_diagnostics",
    "_utc_now",
]
