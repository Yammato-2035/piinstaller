"""
Deploy runner risk gate — policy decisions before any future execution.

Phase C.4: allowed_to_execute is always false. No runner imports, no execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from deploy.runner_registry import (
    RunnerCategory,
    RunnerExecutionPolicy,
    RunnerRegistryEntry,
    RunnerRiskLevel,
    build_runner_registry_from_files,
    find_runner_by_id,
)
from deploy.runner_result_contract import (
    build_empty_result_for_registry_entry,
    validate_registry_result_contract,
)

RISK_GATE_VERSION = 1

_C4_EXECUTE_ALLOWED = False


class RunnerRiskDecision(str, Enum):
    ALLOWED_PLAN_ONLY = "allowed_plan_only"
    REVIEW_REQUIRED = "review_required"
    BLOCKED_OPERATOR_REQUIRED = "blocked_operator_required"
    BLOCKED_POLICY = "blocked_policy"
    BLOCKED_NEVER_AUTO = "blocked_never_auto"
    BLOCKED_UNKNOWN_RUNNER = "blocked_unknown_runner"
    BLOCKED_INVALID_CONTRACT = "blocked_invalid_contract"


@dataclass
class RunnerOperatorConfirmation:
    confirmed: bool = False
    operator_id: str = ""
    confirmation_token: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunnerRiskGateInput:
    runner_id: str
    operator_confirmation: RunnerOperatorConfirmation | None = None
    runtime_gate_ok: bool | None = None
    install_profile: str = ""
    lab_profile_required: bool | None = None
    hardware_present: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.operator_confirmation is not None:
            d["operator_confirmation"] = self.operator_confirmation.to_dict()
        return d


@dataclass
class RunnerRiskGateDecision:
    runner_id: str
    decision: RunnerRiskDecision
    allowed_to_execute: bool
    allowed_to_plan: bool
    requires_operator: bool
    requires_runtime_gate: bool
    requires_lab_profile: bool
    requires_hardware_presence: bool
    risk_level: str
    execution_policy: str
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    next_required_actions: list[str] = field(default_factory=list)
    risk_gate_version: int = RISK_GATE_VERSION

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["decision"] = self.decision.value
        return d


def _operator_confirmed(
    entry: RunnerRegistryEntry,
    operator_confirmation: RunnerOperatorConfirmation | None,
) -> bool:
    if operator_confirmation is not None and operator_confirmation.confirmed:
        return True
    return False


def _needs_hardware(entry: RunnerRegistryEntry) -> bool:
    return entry.uses_device_write or entry.risk_level in {
        RunnerRiskLevel.DEVICE_WRITE,
        RunnerRiskLevel.DESTRUCTIVE,
    }


def _needs_lab_profile(entry: RunnerRegistryEntry) -> bool:
    return entry.execution_policy == RunnerExecutionPolicy.LAB_ONLY or entry.risk_level in {
        RunnerRiskLevel.EVIDENCE_WRITE,
    }


def evaluate_registry_entry_risk(
    entry: RunnerRegistryEntry,
    operator_confirmation: RunnerOperatorConfirmation | None = None,
    runtime_context: dict[str, Any] | None = None,
) -> RunnerRiskGateDecision:
    """Evaluate risk gate for a registry entry (no execution)."""
    ctx = runtime_context or {}
    op_ok = _operator_confirmed(entry, operator_confirmation)
    runtime_gate_ok = ctx.get("runtime_gate_ok")
    install_profile = str(ctx.get("install_profile", "") or "")
    lab_required = ctx.get("lab_profile_required")
    hardware_present = ctx.get("hardware_present")

    empty = build_empty_result_for_registry_entry(entry)
    validation = validate_registry_result_contract(entry, empty)
    if not validation.valid:
        return RunnerRiskGateDecision(
            runner_id=entry.runner_id,
            decision=RunnerRiskDecision.BLOCKED_INVALID_CONTRACT,
            allowed_to_execute=False,
            allowed_to_plan=False,
            requires_operator=entry.requires_operator,
            requires_runtime_gate=True,
            requires_lab_profile=_needs_lab_profile(entry),
            requires_hardware_presence=_needs_hardware(entry),
            risk_level=entry.risk_level.value,
            execution_policy=entry.execution_policy.value,
            errors=list(validation.errors),
            reasons=["registry_result_contract_invalid"],
            next_required_actions=["fix_registry_contract_validation"],
        )

    reasons: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    next_actions: list[str] = []

    if entry.execution_policy == RunnerExecutionPolicy.DISABLED:
        return RunnerRiskGateDecision(
            runner_id=entry.runner_id,
            decision=RunnerRiskDecision.BLOCKED_POLICY,
            allowed_to_execute=False,
            allowed_to_plan=False,
            requires_operator=entry.requires_operator,
            requires_runtime_gate=False,
            requires_lab_profile=False,
            requires_hardware_presence=False,
            risk_level=entry.risk_level.value,
            execution_policy=entry.execution_policy.value,
            reasons=["execution_policy_disabled"],
            next_required_actions=["enable_policy_or_skip_runner"],
        )

    decision = RunnerRiskDecision.REVIEW_REQUIRED
    allowed_to_plan = False

    risk = entry.risk_level
    policy = entry.execution_policy

    if risk == RunnerRiskLevel.DESTRUCTIVE:
        if policy == RunnerExecutionPolicy.NEVER_AUTO:
            decision = RunnerRiskDecision.BLOCKED_NEVER_AUTO
            allowed_to_plan = op_ok
            reasons.append("destructive_never_auto")
            next_actions.append("manual_lab_procedure_only")
            if op_ok:
                warnings.append("operator_confirmed_but_c4_execute_still_forbidden")
        elif op_ok:
            decision = RunnerRiskDecision.REVIEW_REQUIRED
            allowed_to_plan = True
            reasons.append("destructive_operator_confirmed_review_only_c4")
            warnings.append("not_executable_in_c4")
            next_actions.append("await_c5_migration_and_runtime_gate")
        else:
            decision = RunnerRiskDecision.BLOCKED_OPERATOR_REQUIRED
            reasons.append("destructive_requires_operator")
            next_actions.append("obtain_operator_confirmation")
    elif risk in {
        RunnerRiskLevel.DEVICE_WRITE,
        RunnerRiskLevel.SYSTEM_CHANGE,
        RunnerRiskLevel.LOCAL_RUNTIME_CHANGE,
    } or entry.uses_sudo or entry.uses_device_write:
        if not op_ok:
            decision = RunnerRiskDecision.BLOCKED_OPERATOR_REQUIRED
            reasons.append("elevated_risk_requires_operator")
            next_actions.append("obtain_operator_confirmation")
        else:
            decision = RunnerRiskDecision.REVIEW_REQUIRED
            allowed_to_plan = True
            reasons.append("operator_confirmed_elevated_risk_plan_review")
            warnings.append("not_executable_in_c4")
    elif risk == RunnerRiskLevel.READ_ONLY:
        decision = RunnerRiskDecision.ALLOWED_PLAN_ONLY
        allowed_to_plan = True
        reasons.append("read_only_runner")
    elif risk == RunnerRiskLevel.EVIDENCE_WRITE:
        decision = RunnerRiskDecision.ALLOWED_PLAN_ONLY
        allowed_to_plan = True
        reasons.append("evidence_write_plan_only")
    elif risk == RunnerRiskLevel.TEMPLATE_WRITE:
        decision = RunnerRiskDecision.REVIEW_REQUIRED
        allowed_to_plan = True
        reasons.append("template_write_review")
    else:
        decision = RunnerRiskDecision.REVIEW_REQUIRED
        allowed_to_plan = True
        reasons.append("conservative_unknown_risk_tier")

    if entry.category == RunnerCategory.UNKNOWN:
        warnings.append("unknown_category_conservative")
        if decision == RunnerRiskDecision.ALLOWED_PLAN_ONLY:
            decision = RunnerRiskDecision.REVIEW_REQUIRED

    requires_lab = _needs_lab_profile(entry)
    if requires_lab:
        if lab_required is False or (lab_required is None and install_profile and install_profile != "lab"):
            if decision == RunnerRiskDecision.ALLOWED_PLAN_ONLY:
                decision = RunnerRiskDecision.REVIEW_REQUIRED
            warnings.append("lab_profile_recommended")
            next_actions.append("use_lab_profile")
        if lab_required is True and install_profile != "lab":
            decision = RunnerRiskDecision.BLOCKED_POLICY
            allowed_to_plan = False
            reasons.append("lab_profile_required")
            next_actions.append("switch_to_lab_profile")

    requires_hw = _needs_hardware(entry)
    if requires_hw and hardware_present is False:
        decision = RunnerRiskDecision.BLOCKED_OPERATOR_REQUIRED
        allowed_to_plan = False
        reasons.append("hardware_presence_required")
        next_actions.append("attach_target_hardware")

    requires_runtime = risk in {
        RunnerRiskLevel.DESTRUCTIVE,
        RunnerRiskLevel.DEVICE_WRITE,
        RunnerRiskLevel.SYSTEM_CHANGE,
        RunnerRiskLevel.LOCAL_RUNTIME_CHANGE,
    }
    if requires_runtime and runtime_gate_ok is False:
        if decision not in {
            RunnerRiskDecision.BLOCKED_NEVER_AUTO,
            RunnerRiskDecision.BLOCKED_POLICY,
        }:
            decision = RunnerRiskDecision.BLOCKED_OPERATOR_REQUIRED
            allowed_to_plan = False
            reasons.append("runtime_gate_not_ok")
            next_actions.append("pass_runtime_deploy_gate")

    return RunnerRiskGateDecision(
        runner_id=entry.runner_id,
        decision=decision,
        allowed_to_execute=_C4_EXECUTE_ALLOWED,
        allowed_to_plan=allowed_to_plan,
        requires_operator=entry.requires_operator or entry.uses_sudo or entry.uses_device_write,
        requires_runtime_gate=requires_runtime,
        requires_lab_profile=requires_lab,
        requires_hardware_presence=requires_hw,
        risk_level=risk.value,
        execution_policy=policy.value,
        reasons=reasons,
        warnings=warnings,
        errors=errors,
        next_required_actions=next_actions,
    )


def evaluate_runner_risk_gate(
    runner_id: str,
    operator_confirmation: RunnerOperatorConfirmation | None = None,
    runtime_context: dict[str, Any] | None = None,
    *,
    entries: list[RunnerRegistryEntry] | None = None,
) -> RunnerRiskGateDecision:
    """Evaluate risk gate by runner_id."""
    pool = entries if entries is not None else build_runner_registry_from_files()
    entry = find_runner_by_id(runner_id, pool)
    if entry is None:
        return RunnerRiskGateDecision(
            runner_id=runner_id,
            decision=RunnerRiskDecision.BLOCKED_UNKNOWN_RUNNER,
            allowed_to_execute=False,
            allowed_to_plan=False,
            requires_operator=False,
            requires_runtime_gate=False,
            requires_lab_profile=False,
            requires_hardware_presence=False,
            risk_level="unknown",
            execution_policy="unknown",
            errors=[f"unknown_runner_id:{runner_id}"],
            reasons=["runner_not_in_registry"],
            next_required_actions=["verify_runner_id"],
        )
    return evaluate_registry_entry_risk(entry, operator_confirmation, runtime_context)


def build_risk_gate_summary(entries: list[RunnerRegistryEntry] | None = None) -> dict[str, Any]:
    """Aggregate risk gate decisions for all registry entries."""
    pool = entries if entries is not None else build_runner_registry_from_files()
    by_decision: dict[str, int] = {}
    plan_allowed = 0
    operator_required = 0
    never_auto = 0
    for entry in pool:
        d = evaluate_registry_entry_risk(entry)
        by_decision[d.decision.value] = by_decision.get(d.decision.value, 0) + 1
        if d.allowed_to_plan:
            plan_allowed += 1
        if d.decision == RunnerRiskDecision.BLOCKED_OPERATOR_REQUIRED:
            operator_required += 1
        if d.decision == RunnerRiskDecision.BLOCKED_NEVER_AUTO:
            never_auto += 1
    return {
        "risk_gate_version": RISK_GATE_VERSION,
        "total": len(pool),
        "allowed_to_execute_in_c4": _C4_EXECUTE_ALLOWED,
        "by_decision": by_decision,
        "plan_allowed_count": plan_allowed,
        "operator_required_count": operator_required,
        "never_auto_count": never_auto,
    }


def list_blocked_runners(entries: list[RunnerRegistryEntry] | None = None) -> list[dict[str, Any]]:
    pool = entries if entries is not None else build_runner_registry_from_files()
    blocked: list[dict[str, Any]] = []
    block_decisions = {
        RunnerRiskDecision.BLOCKED_OPERATOR_REQUIRED,
        RunnerRiskDecision.BLOCKED_POLICY,
        RunnerRiskDecision.BLOCKED_NEVER_AUTO,
        RunnerRiskDecision.BLOCKED_INVALID_CONTRACT,
    }
    for entry in pool:
        d = evaluate_registry_entry_risk(entry)
        if d.decision in block_decisions or not d.allowed_to_plan:
            blocked.append({"runner_id": entry.runner_id, "decision": d.decision.value, "reasons": d.reasons})
    return blocked


def list_operator_required_runners(entries: list[RunnerRegistryEntry] | None = None) -> list[str]:
    pool = entries if entries is not None else build_runner_registry_from_files()
    out: list[str] = []
    for entry in pool:
        d = evaluate_registry_entry_risk(entry)
        if d.decision == RunnerRiskDecision.BLOCKED_OPERATOR_REQUIRED or d.requires_operator:
            out.append(entry.runner_id)
    return sorted(set(out))
