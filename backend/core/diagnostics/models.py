from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Severity = Literal["info", "low", "medium", "high", "critical"]
ConfidenceLevel = Literal["low", "medium", "high"]
UserLevel = Literal["beginner", "advanced", "expert", "all"]
DiagnosisDomain = Literal[
    "backup_restore",
    "boot",
    "systemd_services",
    "permissions",
    "storage_filesystem",
    "network",
    "ssh_remote_access",
    "updates_packages",
    "security_hardening",
    "docker_container_runtime",
    "hardware_raspberry_pi",
    "logs_runtime",
    "app_setuphelfer_runtime",
]
EvidenceSourceType = Literal[
    "manual_test",
    "api_test",
    "unit_test",
    "vm_test",
    "hardware_test",
    "user_report",
]
EvidencePlatform = Literal["raspberry_pi", "linux_pc", "linux_laptop", "vm", "rescue_media"]
EvidenceOutcome = Literal["success", "partial", "failed", "inconclusive"]
BootMode = Literal["sd", "usb", "nvme", "mixed", "unknown"]
EvidenceDiagnosisStatus = Literal["suspected", "confirmed", "refuted"]


class DiagnosticCheck(BaseModel):
    id: str
    description: str
    expects: str


class DiagnosticAction(BaseModel):
    id: str
    priority: int = Field(default=100, ge=1, le=999)
    text_de: str
    text_en: str


class DiagnosticCase(BaseModel):
    id: str
    domain: DiagnosisDomain
    title_de: str
    title_en: str
    summary_de: str
    summary_en: str
    severity: Severity
    confidence: ConfidenceLevel
    user_level_visibility: UserLevel = "all"
    symptoms: list[str] = Field(default_factory=list)
    detection_sources: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    checks: list[DiagnosticCheck] = Field(default_factory=list)
    root_causes: list[str] = Field(default_factory=list)
    recommended_actions: list[DiagnosticAction] = Field(default_factory=list)
    safe_auto_actions: list[str] = Field(default_factory=list)
    escalation_hint: str = ""
    related_docs: list[str] = Field(default_factory=list)
    related_faq: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    requires_confirmation: bool = False
    destructive_risk: bool = False
    status_mapping: dict[str, str] | None = None
    seen_in_platforms: list[EvidencePlatform] = Field(default_factory=list)
    common_storage_contexts: list[str] = Field(default_factory=list)
    common_boot_contexts: list[str] = Field(default_factory=list)
    typical_false_assumptions: list[str] = Field(default_factory=list)
    evidence_counts: dict[str, int] = Field(
        default_factory=lambda: {"suspected": 0, "confirmed": 0, "refuted": 0}
    )


class StorageDevice(BaseModel):
    name: str
    type: Literal["sd", "usb", "nvme", "sata", "loop"]
    size_gb: float = Field(ge=0)
    filesystem: str = ""
    mountpoint: str = ""
    removable: bool = False
    encrypted: bool = False
    health_info: dict[str, Any] | None = None


class SystemProfile(BaseModel):
    id: str
    hostname: str | None = None
    platform_class: EvidencePlatform
    manufacturer: str | None = None
    model: str | None = None
    cpu_model: str = ""
    cpu_arch: str = ""
    core_count: int = Field(default=0, ge=0)
    ram_total_mb: int = Field(default=0, ge=0)
    os_name: str = ""
    os_version: str = ""
    kernel_version: str = ""
    boot_mode: BootMode = "unknown"
    filesystem_root: str = ""
    filesystem_backup_target: str = ""
    storage_devices: list[StorageDevice] = Field(default_factory=list)
    network_summary: dict[str, Any] | None = None


class EvidenceDiagnosisLink(BaseModel):
    diagnosis_id: str
    status: EvidenceDiagnosisStatus = "suspected"


class EvidenceRecord(BaseModel):
    id: str
    timestamp: str
    source_type: EvidenceSourceType
    domain: DiagnosisDomain
    platform: EvidencePlatform
    scenario: str
    test_goal: str
    outcome: EvidenceOutcome
    severity: Severity
    confidence: ConfidenceLevel
    system_profile_id: str = ""
    storage_profile: str = ""
    encryption_profile: str = ""
    boot_profile: str = ""
    observed_symptoms: list[str] = Field(default_factory=list)
    raw_signals: dict[str, Any] = Field(default_factory=dict)
    matched_diagnosis_ids: list[str] = Field(default_factory=list)
    diagnosis_links: list[EvidenceDiagnosisLink] = Field(default_factory=list)
    suspected_root_causes: list[str] = Field(default_factory=list)
    confirmed_root_cause: str = ""
    corrective_actions: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    docs_updated: bool = False
    faq_updated: bool = False
    catalog_updated: bool = False
    tests_added: bool = False


class EvidenceSummary(BaseModel):
    diagnosis_id: str
    suspected: int = 0
    confirmed: int = 0
    refuted: int = 0
    seen_in_platforms: list[EvidencePlatform] = Field(default_factory=list)
    common_storage_contexts: list[str] = Field(default_factory=list)
    common_boot_contexts: list[str] = Field(default_factory=list)


class DiagnosticsAnalyzeRequest(BaseModel):
    question: str = ""
    context: dict[str, Any] = Field(default_factory=dict)
    signals: dict[str, Any] = Field(default_factory=dict)


class DiagnosticsEvidence(BaseModel):
    source: str
    key: str
    value: Any
    note: str = ""


class DiagnosticsAnalyzeResponse(BaseModel):
    primary_diagnosis: dict[str, Any] | None = None
    secondary_diagnoses: list[dict[str, Any]] = Field(default_factory=list)
    severity: Severity = "info"
    confidence: ConfidenceLevel = "low"
    messages: dict[str, str] = Field(default_factory=dict)
    user_message_beginner: str = ""
    technical_summary: str = ""
    actions_now: list[str] = Field(default_factory=list)
    actions_later: list[str] = Field(default_factory=list)
    recommended_actions: list[dict[str, Any]] = Field(default_factory=list)
    safe_auto_actions: list[str] = Field(default_factory=list)
    evidence: list[DiagnosticsEvidence] = Field(default_factory=list)
    requires_confirmation: bool = False


class EvidenceSampleResponse(BaseModel):
    sample: EvidenceRecord
    total_records: int = 0
