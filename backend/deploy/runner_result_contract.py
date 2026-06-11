"""
Deploy runner result contract — schema, validation, legacy normalization.

Phase C.2: No runner imports, no execution, no runtime writes.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from deploy.runner_registry import (
    RunnerCategory,
    RunnerExecutionPolicy,
    RunnerRegistryEntry,
    RunnerRiskLevel,
)

CONTRACT_VERSION = 1

_FORBIDDEN_EVIDENCE_PATHS = (
    re.compile(r"(^|/)\.env($|/)"),
    re.compile(r"/etc/shadow"),
    re.compile(r"(^|/)id_rsa($|/)"),
    re.compile(r"(^|/)credentials\.json$"),
)
_SECRET_METADATA_KEYS = frozenset(
    {"password", "secret", "api_key", "token", "private_key", "credential"}
)
_ABSOLUTE_PATH = re.compile(r"^/[a-zA-Z0-9_./-]+$")
_LEGACY_STATUS_MAP: dict[str, str] = {
    "ok": "ok",
    "ready": "ok",
    "success": "ok",
    "created": "ok",
    "review_required": "review_required",
    "partial": "review_required",
    "implemented": "review_required",
    "tested": "review_required",
    "pending": "review_required",
    "blocked": "blocked",
    "failed": "failed",
    "error": "failed",
    "skipped": "skipped",
    "not_started": "skipped",
    "planned_only": "not_applicable",
}
_CONTRACT_STATUSES = frozenset(
    {"ok", "review_required", "blocked", "failed", "skipped", "not_applicable"}
)
_CATEGORY_TO_KIND: dict[RunnerCategory, str] = {
    RunnerCategory.RUNTIME: "readiness_gate",
    RunnerCategory.DEPLOY: "runtime_operation",
    RunnerCategory.RESCUE: "runtime_operation",
    RunnerCategory.RESCUE_BUILD: "execution_plan",
    RunnerCategory.RESCUE_USB: "device_operation",
    RunnerCategory.BACKUP_RELATED: "execution_plan",
    RunnerCategory.RESTORE_RELATED: "execution_plan",
    RunnerCategory.NOTIFICATION: "runtime_operation",
    RunnerCategory.EVIDENCE: "evidence_generation",
    RunnerCategory.PACKAGING: "template_generation",
    RunnerCategory.DASHBOARD: "static_analysis",
    RunnerCategory.DIAGNOSTICS: "static_analysis",
    RunnerCategory.UNKNOWN: "unknown",
}


class RunnerResultStatus(str, Enum):
    OK = "ok"
    REVIEW_REQUIRED = "review_required"
    BLOCKED = "blocked"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"


class RunnerResultSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RunnerResultKind(str, Enum):
    STATIC_ANALYSIS = "static_analysis"
    TEMPLATE_GENERATION = "template_generation"
    EVIDENCE_GENERATION = "evidence_generation"
    READINESS_GATE = "readiness_gate"
    MANUAL_PRECHECK = "manual_precheck"
    EXECUTION_PLAN = "execution_plan"
    RUNTIME_OPERATION = "runtime_operation"
    DEVICE_OPERATION = "device_operation"
    UNKNOWN = "unknown"


@dataclass
class RunnerMessage:
    code: str
    message: str
    severity: RunnerResultSeverity = RunnerResultSeverity.INFO

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass
class RunnerEvidenceRef:
    path: str
    read_only: bool = False
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"path": self.path, "read_only": self.read_only}
        if self.label:
            d["label"] = self.label
        return d


@dataclass
class RunnerResult:
    runner_id: str
    status: RunnerResultStatus
    kind: RunnerResultKind
    created_at: str
    summary: str
    warnings: list[RunnerMessage] = field(default_factory=list)
    errors: list[RunnerMessage] = field(default_factory=list)
    evidence_paths: list[RunnerEvidenceRef] = field(default_factory=list)
    risk_level: str = RunnerRiskLevel.READ_ONLY.value
    execution_policy: str = RunnerExecutionPolicy.NEVER_AUTO.value
    requires_operator: bool = False
    no_execution_performed: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    contract_version: int = CONTRACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        d["kind"] = self.kind.value
        d["warnings"] = [w.to_dict() if isinstance(w, RunnerMessage) else w for w in self.warnings]
        d["errors"] = [e.to_dict() if isinstance(e, RunnerMessage) else e for e in self.errors]
        d["evidence_paths"] = [
            ep.to_dict() if isinstance(ep, RunnerEvidenceRef) else ep for ep in self.evidence_paths
        ]
        return d


@dataclass
class RunnerResultValidation:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _coerce_message(item: Any, default_severity: RunnerResultSeverity) -> RunnerMessage | None:
    if isinstance(item, RunnerMessage):
        return item
    if isinstance(item, dict):
        sev_raw = str(item.get("severity", default_severity.value))
        try:
            sev = RunnerResultSeverity(sev_raw)
        except ValueError:
            sev = default_severity
        code = str(item.get("code", "LEGACY_MESSAGE"))
        message = str(item.get("message", item.get("detail", code)))
        return RunnerMessage(code=code, message=message, severity=sev)
    if isinstance(item, str):
        return RunnerMessage(code="LEGACY_STRING", message=item, severity=default_severity)
    return None


def _coerce_evidence_ref(item: Any) -> RunnerEvidenceRef | None:
    if isinstance(item, RunnerEvidenceRef):
        return item
    if isinstance(item, str):
        return RunnerEvidenceRef(path=item)
    if isinstance(item, dict) and "path" in item:
        return RunnerEvidenceRef(
            path=str(item["path"]),
            read_only=bool(item.get("read_only", False)),
            label=str(item.get("label", "")),
        )
    return None


def build_runner_result(
    *,
    runner_id: str,
    status: RunnerResultStatus | str,
    kind: RunnerResultKind | str,
    summary: str,
    created_at: str | None = None,
    warnings: list[Any] | None = None,
    errors: list[Any] | None = None,
    evidence_paths: list[Any] | None = None,
    risk_level: str | RunnerRiskLevel = RunnerRiskLevel.READ_ONLY,
    execution_policy: str | RunnerExecutionPolicy = RunnerExecutionPolicy.NEVER_AUTO,
    requires_operator: bool = False,
    no_execution_performed: bool = True,
    metadata: dict[str, Any] | None = None,
) -> RunnerResult:
    """Build a contract-compliant RunnerResult."""
    st = RunnerResultStatus(status) if isinstance(status, str) else status
    kd = RunnerResultKind(kind) if isinstance(kind, str) else kind
    rl = risk_level.value if isinstance(risk_level, RunnerRiskLevel) else str(risk_level)
    ep = execution_policy.value if isinstance(execution_policy, RunnerExecutionPolicy) else str(execution_policy)

    warn_msgs = [
        m
        for m in (_coerce_message(w, RunnerResultSeverity.WARNING) for w in (warnings or []))
        if m is not None
    ]
    err_msgs = [
        m
        for m in (_coerce_message(e, RunnerResultSeverity.ERROR) for e in (errors or []))
        if m is not None
    ]
    ev_refs = [
        r
        for r in (_coerce_evidence_ref(p) for p in (evidence_paths or []))
        if r is not None
    ]

    return RunnerResult(
        runner_id=runner_id,
        status=st,
        kind=kd,
        created_at=created_at or _utc_now_iso(),
        summary=summary,
        warnings=warn_msgs,
        errors=err_msgs,
        evidence_paths=ev_refs,
        risk_level=rl,
        execution_policy=ep,
        requires_operator=requires_operator,
        no_execution_performed=no_execution_performed,
        metadata=dict(metadata or {}),
    )


def _validate_messages(items: Any, label: str, out: RunnerResultValidation) -> None:
    if not isinstance(items, list):
        out.errors.append(f"{label}_must_be_list")
        return
    for i, item in enumerate(items):
        if isinstance(item, dict):
            if "code" not in item and "message" not in item:
                out.errors.append(f"{label}[{i}]_missing_code_or_message")
            sev = str(item.get("severity", "info"))
            if sev not in {s.value for s in RunnerResultSeverity}:
                out.errors.append(f"{label}[{i}]_invalid_severity:{sev}")
        elif isinstance(item, str):
            continue
        else:
            out.errors.append(f"{label}[{i}]_invalid_type")


def _validate_evidence_path(path: str, read_only: bool, out: RunnerResultValidation, prefix: str) -> None:
    for rx in _FORBIDDEN_EVIDENCE_PATHS:
        if rx.search(path):
            out.errors.append(f"{prefix}_forbidden_path:{path}")
            return
    if path.startswith("/") and not read_only:
        out.errors.append(f"{prefix}_absolute_path_not_read_only:{path}")
    if path.startswith(".."):
        out.errors.append(f"{prefix}_path_traversal:{path}")


def _validate_metadata(meta: Any, out: RunnerResultValidation) -> None:
    if not isinstance(meta, dict):
        out.errors.append("metadata_must_be_dict")
        return
    for key, value in meta.items():
        if str(key).lower() in _SECRET_METADATA_KEYS:
            out.errors.append(f"metadata_secret_key:{key}")
        if isinstance(value, str) and any(
            s in value.lower() for s in ("password=", "api_key=", "secret=", "token=")
        ):
            out.errors.append(f"metadata_secret_like_value:{key}")


def validate_runner_result(result: dict[str, Any]) -> RunnerResultValidation:
    """Validate a runner result dict against the contract."""
    out = RunnerResultValidation(valid=True)

    required = (
        "runner_id",
        "status",
        "kind",
        "created_at",
        "summary",
        "warnings",
        "errors",
        "evidence_paths",
        "risk_level",
        "execution_policy",
        "requires_operator",
        "no_execution_performed",
        "metadata",
    )
    for key in required:
        if key not in result:
            out.errors.append(f"missing_field:{key}")

    status_raw = str(result.get("status", ""))
    if status_raw not in _CONTRACT_STATUSES:
        out.errors.append(f"invalid_status:{status_raw}")
    elif status_raw == "unknown":
        out.errors.append("status_unknown_not_allowed")

    kind_raw = str(result.get("kind", ""))
    if kind_raw not in {k.value for k in RunnerResultKind}:
        out.errors.append(f"invalid_kind:{kind_raw}")

    _validate_messages(result.get("warnings", []), "warnings", out)
    _validate_messages(result.get("errors", []), "errors", out)

    evidence = result.get("evidence_paths", [])
    if not isinstance(evidence, list):
        out.errors.append("evidence_paths_must_be_list")
    else:
        for i, item in enumerate(evidence):
            if isinstance(item, str):
                _validate_evidence_path(item, False, out, f"evidence_paths[{i}]")
            elif isinstance(item, dict):
                path = str(item.get("path", ""))
                if not path:
                    out.errors.append(f"evidence_paths[{i}]_missing_path")
                else:
                    _validate_evidence_path(path, bool(item.get("read_only", False)), out, f"evidence_paths[{i}]")
            else:
                out.errors.append(f"evidence_paths[{i}]_invalid_type")

    _validate_metadata(result.get("metadata", {}), out)

    if "no_execution_performed" not in result:
        pass
    elif not isinstance(result.get("no_execution_performed"), bool):
        out.errors.append("no_execution_performed_must_be_bool")

    if status_raw in {"blocked", "failed"}:
        errs = result.get("errors", [])
        if not isinstance(errs, list) or len(errs) == 0:
            out.errors.append(f"{status_raw}_requires_errors")

    if status_raw == "review_required":
        warns = result.get("warnings", [])
        errs = result.get("errors", [])
        if (not isinstance(warns, list) or len(warns) == 0) and (
            not isinstance(errs, list) or len(errs) == 0
        ):
            out.errors.append("review_required_requires_warnings_or_errors")

    risk = str(result.get("risk_level", ""))
    policy = str(result.get("execution_policy", ""))
    if risk in {RunnerRiskLevel.DEVICE_WRITE.value, RunnerRiskLevel.DESTRUCTIVE.value}:
        requires_op = bool(result.get("requires_operator", False))
        allowed_policies = {
            RunnerExecutionPolicy.NEVER_AUTO.value,
            RunnerExecutionPolicy.OPERATOR_CONFIRMED.value,
            RunnerExecutionPolicy.MANUAL_ONLY.value,
        }
        if not requires_op and policy not in allowed_policies:
            out.errors.append("device_write_requires_operator_or_restricted_policy")
        if risk == RunnerRiskLevel.DESTRUCTIVE.value and policy != RunnerExecutionPolicy.NEVER_AUTO.value:
            out.errors.append("destructive_requires_never_auto_policy")

    out.valid = len(out.errors) == 0
    return out


def _infer_kind_from_registry(entry: RunnerRegistryEntry | None) -> RunnerResultKind:
    if entry is None:
        return RunnerResultKind.UNKNOWN
    kind_str = _CATEGORY_TO_KIND.get(entry.category, "unknown")
    return RunnerResultKind(kind_str)


def normalize_legacy_runner_result(
    runner_id: str,
    raw: dict[str, Any],
    registry_entry: RunnerRegistryEntry | None = None,
) -> RunnerResult:
    """Map legacy runner dict shapes to RunnerResult (no runner execution)."""
    legacy_status = str(raw.get("status", raw.get("result_status", "review_required"))).lower()
    norm_warnings: list[RunnerMessage] = []
    if legacy_status not in _LEGACY_STATUS_MAP:
        norm_warnings.append(
            RunnerMessage(
                code="LEGACY_STATUS_UNKNOWN",
                message=f"Unmapped legacy status '{legacy_status}' → review_required",
                severity=RunnerResultSeverity.WARNING,
            )
        )
        contract_status = RunnerResultStatus.REVIEW_REQUIRED
    else:
        contract_status = RunnerResultStatus(_LEGACY_STATUS_MAP[legacy_status])

    legacy_warns = raw.get("warnings", [])
    if isinstance(legacy_warns, list):
        for w in legacy_warns:
            msg = _coerce_message(w, RunnerResultSeverity.WARNING)
            if msg:
                norm_warnings.append(msg)

    legacy_errors = raw.get("errors", [])
    norm_errors: list[RunnerMessage] = []
    if isinstance(legacy_errors, list):
        for e in legacy_errors:
            msg = _coerce_message(e, RunnerResultSeverity.ERROR)
            if msg:
                norm_errors.append(msg)
    if contract_status in {RunnerResultStatus.BLOCKED, RunnerResultStatus.FAILED} and not norm_errors:
        detail = str(raw.get("detail", raw.get("message", "legacy failure without errors")))
        norm_errors.append(
            RunnerMessage(code="LEGACY_FAILURE", message=detail, severity=RunnerResultSeverity.ERROR)
        )
    if contract_status == RunnerResultStatus.REVIEW_REQUIRED and not norm_warnings and not norm_errors:
        norm_warnings.append(
            RunnerMessage(
                code="LEGACY_REVIEW",
                message=str(raw.get("detail", "review required (legacy)")),
                severity=RunnerResultSeverity.WARNING,
            )
        )

    evidence_raw = raw.get("evidence_paths", raw.get("evidence_files", raw.get("evidence", [])))
    evidence_paths: list[RunnerEvidenceRef] = []
    if isinstance(evidence_raw, str):
        evidence_paths.append(RunnerEvidenceRef(path=evidence_raw))
    elif isinstance(evidence_raw, list):
        for item in evidence_raw:
            ref = _coerce_evidence_ref(item)
            if ref:
                evidence_paths.append(ref)

    kind = _infer_kind_from_registry(registry_entry)
    risk = registry_entry.risk_level.value if registry_entry else RunnerRiskLevel.READ_ONLY.value
    policy = registry_entry.execution_policy.value if registry_entry else RunnerExecutionPolicy.NEVER_AUTO.value
    requires_op = registry_entry.requires_operator if registry_entry else False

    return build_runner_result(
        runner_id=runner_id,
        status=contract_status,
        kind=kind,
        summary=str(raw.get("summary", raw.get("detail", f"Normalized legacy result for {runner_id}"))),
        created_at=str(raw.get("created_at", _utc_now_iso())),
        warnings=norm_warnings,
        errors=norm_errors,
        evidence_paths=evidence_paths,
        risk_level=risk,
        execution_policy=policy,
        requires_operator=requires_op,
        no_execution_performed=bool(raw.get("no_execution_performed", True)),
        metadata=dict(raw.get("metadata", {})),
    )


def summarize_runner_results(results: list[RunnerResult]) -> dict[str, Any]:
    """Aggregate status counts and validation summary."""
    by_status: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    invalid = 0
    for r in results:
        by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
        by_kind[r.kind.value] = by_kind.get(r.kind.value, 0) + 1
        if not validate_runner_result(r.to_dict()).valid:
            invalid += 1
    return {
        "contract_version": CONTRACT_VERSION,
        "total": len(results),
        "by_status": by_status,
        "by_kind": by_kind,
        "invalid_count": invalid,
        "valid_count": len(results) - invalid,
    }


def build_empty_result_for_registry_entry(entry: RunnerRegistryEntry) -> RunnerResult:
    """Plan-only empty result template for a registry entry (no execution)."""
    kind = _infer_kind_from_registry(entry)
    return build_runner_result(
        runner_id=entry.runner_id,
        status=RunnerResultStatus.SKIPPED,
        kind=kind,
        summary=f"Plan-only template for {entry.runner_id}; no execution performed (C.2).",
        warnings=[
            RunnerMessage(
                code="NO_EXECUTION",
                message="Empty registry template — runner not invoked.",
                severity=RunnerResultSeverity.INFO,
            )
        ],
        risk_level=entry.risk_level,
        execution_policy=entry.execution_policy,
        requires_operator=entry.requires_operator,
        no_execution_performed=True,
        metadata={"registry_category": entry.category.value, "registry_path": entry.path},
    )


def validate_registry_result_contract(
    entry: RunnerRegistryEntry,
    result: dict[str, Any] | RunnerResult,
) -> RunnerResultValidation:
    """Validate result against contract and registry entry expectations."""
    payload = result.to_dict() if isinstance(result, RunnerResult) else result
    validation = validate_runner_result(payload)

    if payload.get("runner_id") != entry.runner_id:
        validation.errors.append("runner_id_mismatch")
    if payload.get("risk_level") != entry.risk_level.value:
        validation.warnings.append("risk_level_differs_from_registry")
    if payload.get("execution_policy") != entry.execution_policy.value:
        validation.warnings.append("execution_policy_differs_from_registry")

    validation.valid = len(validation.errors) == 0
    return validation


# --- Static scan helpers for boundary guard (warn-only) ---

_STATUS_LITERAL = re.compile(
    r"""['"]status['"]\s*:\s*['"]([^'"]+)['"]""",
    re.IGNORECASE,
)
_FAILED_LIKE_WITHOUT_ERRORS = re.compile(
    r"""['"]status['"]\s*:\s*['"](?:failed|blocked|error)['"]""",
    re.IGNORECASE,
)


def scan_runner_file_result_warnings(path: str | Path, text: str | None = None) -> list[str]:
    """Static warnings for legacy result patterns in a runner file."""
    p = Path(path)
    raw = text if text is not None else p.read_text(encoding="utf-8", errors="replace")
    rel = p.name
    warns: list[str] = []

    for m in _STATUS_LITERAL.finditer(raw):
        token = m.group(1).lower()
        if token not in _CONTRACT_STATUSES:
            warns.append(f"runner_result_unknown_status_token:{rel}:{token}")

    if _FAILED_LIKE_WITHOUT_ERRORS.search(raw):
        window_has_errors = "errors" in raw or '"error"' in raw.lower()
        if not window_has_errors:
            warns.append(f"runner_result_no_errors_for_failed_like:{rel}")

    if "evidence" in p.name.lower() or "evidence" in raw[:800].lower():
        if "evidence_path" not in raw and "evidence_paths" not in raw and "evidence_files" not in raw:
            warns.append(f"runner_result_no_evidence_reference:{rel}")

    return warns
