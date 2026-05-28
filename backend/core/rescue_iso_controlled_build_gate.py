from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

CONTROLLED_GATE_MESSAGE = "Use controlled gate before running lb build."
CONTROLLED_GATE_ERROR_CODE = "blocked_controlled_build_gate_required"
CONTROLLED_GATE_NEXT_ACTION = "use_controlled_rescue_build_gate"
CONTROLLED_GATE_CATEGORY = "safety_gate"
CONTROLLED_ROOT_POLICY_ERROR_CODE = "blocked_requires_operator_sudo_policy"
CONTROLLED_ROOT_POLICY_NEXT_ACTION = "manual_operator_terminal_required"
CONTROLLED_ROOT_POLICY_CATEGORY = "operator_policy"
ISOHYBRID_ERROR_CODE = "RESCUE-BUILD-ISOHYBRID-001"
ISOHYBRID_NEXT_ACTION = "prepare_binary_package_list_and_retry"
ISOHYBRID_CATEGORY = "binary_stage_toolchain"
CHROOT_CLEANUP_ERROR_CODE = "RESCUE-BUILD-CHROOT-CLEANUP-001"
CHROOT_CLEANUP_NEXT_ACTION = "unmount_build_tree_and_clean_chroot"
CHROOT_CLEANUP_CATEGORY = "live_build_cleanup"

WORKING_DIRECTORY_REL = "build/rescue/live-build/setuphelfer-rescue-live"
PATH_PREFIX_REL = "build/rescue/tool-compat/bin"
LOGGING_WRAPPER_REL = "scripts/rescue-live/run-controlled-iso-build-with-logging.sh"

RUN_LATEST_REL = "docs/evidence/runtime-results/rescue/rescue_iso_amd64_build_run_latest.json"
RESULT_LATEST_REL = "docs/evidence/runtime-results/rescue/rescue_iso_amd64_build_result_latest.json"
DECISION_LATEST_REL = "docs/evidence/runtime-results/rescue/rescue_iso_amd64_build_decision_latest.json"
COMBINED_LOG_LATEST_REL = (
    "docs/evidence/runtime-results/rescue/build-logs/rescue_iso_amd64_build_combined_latest.log"
)
CONTROLLED_RUN_LATEST_REL = "docs/evidence/runtime-results/rescue/rescue_iso_controlled_amd64_build_run_latest.json"
CONTROLLED_RESULT_LATEST_REL = "docs/evidence/runtime-results/rescue/rescue_iso_controlled_amd64_build_result_latest.json"
CONTROLLED_DECISION_LATEST_REL = "docs/evidence/runtime-results/rescue/rescue_iso_controlled_amd64_build_decision_latest.json"
CONTROLLED_COMBINED_LOG_LATEST_REL = (
    "docs/evidence/runtime-results/rescue/build-logs/rescue_iso_controlled_amd64_build_combined_latest.log"
)


def _safe_read_text(path: Path) -> str | None:
    try:
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    raw = _safe_read_text(path)
    if raw is None:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _parse_iso(raw: Any) -> datetime | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def analyze_auto_build_gate(
    *,
    auto_build_text: str,
    logging_wrapper_text: str,
    runbook_text: str,
) -> dict[str, Any]:
    gate_message_found = CONTROLLED_GATE_MESSAGE in auto_build_text
    wrapper_uses_operator_flag = "--operator-confirm-build" in logging_wrapper_text
    wrapper_uses_noauto = "lb build noauto" in logging_wrapper_text
    wrapper_sets_path_prefix = "tool-compat/bin" in logging_wrapper_text or "tool-compat/bin" in runbook_text
    runbook_mentions_noauto = "lb build noauto" in runbook_text or "sudo lb build noauto" in runbook_text

    conclusion = "unexpected_failure"
    if gate_message_found and (wrapper_uses_noauto or runbook_mentions_noauto):
        conclusion = "controlled_gate_required"
    elif gate_message_found:
        conclusion = "unclear_gate_contract"

    expected_gate_mechanism = (
        "auto/build ist absichtlich nur ein Stop-Script mit Exit 20. "
        "Der echte Build darf nur ueber den kontrollierten Setuphelfer-Buildpfad laufen, "
        "der auto/build nicht rekursiv ausloest und stattdessen ./auto/config plus lb build noauto nutzt."
    )
    expected_env_vars = [f'PATH="<repo>/{PATH_PREFIX_REL}:$PATH"']
    expected_files = [
        f"{WORKING_DIRECTORY_REL}/auto/build",
        f"{WORKING_DIRECTORY_REL}/auto/config",
        f"{WORKING_DIRECTORY_REL}/auto/clean",
        f"{WORKING_DIRECTORY_REL}/evidence/build-tree-manifest.json",
        "docs/evidence/runtime-results/rescue/live_build_dpkg_preflight_latest.json",
    ]
    expected_command = (
        f'cd "{WORKING_DIRECTORY_REL}" && export PATH="<repo>/{PATH_PREFIX_REL}:$PATH" '
        f'&& ./auto/config && sudo env PATH="<repo>/{PATH_PREFIX_REL}:$PATH" lb build noauto'
    )
    return {
        "gate_message_found": gate_message_found,
        "expected_gate_mechanism": expected_gate_mechanism,
        "expected_env_vars": expected_env_vars,
        "expected_files": expected_files,
        "expected_working_directory": WORKING_DIRECTORY_REL,
        "expected_command": expected_command,
        "wrapper_command": f"{LOGGING_WRAPPER_REL} --operator-confirm-build",
        "wrapper_uses_operator_flag": wrapper_uses_operator_flag,
        "wrapper_uses_noauto": wrapper_uses_noauto,
        "wrapper_sets_path_prefix": wrapper_sets_path_prefix,
        "conclusion": conclusion,
        "no_build_executed": True,
    }


def build_controlled_build_contract(gate_analysis: dict[str, Any]) -> dict[str, Any]:
    ready = (
        bool(gate_analysis.get("gate_message_found"))
        and bool(gate_analysis.get("wrapper_uses_noauto"))
        and bool(gate_analysis.get("wrapper_sets_path_prefix"))
    )
    contract_status = "ready" if ready else "review_required"
    return {
        "contract_status": contract_status,
        "required_inputs": [
            "Runtime-Gate Exit 0",
            "DPKG-Preflight ok/pre_chroot_ok",
            "materialisierter Live-Build-Tree vorhanden",
            "projektlokaler rsvg-Wrapper im PATH",
            "explizite Operator-Freigabe",
        ],
        "required_env": list(gate_analysis.get("expected_env_vars") or []),
        "required_marker_files": list(gate_analysis.get("expected_files") or []),
        "required_evidence_files": [
            "docs/evidence/runtime-results/rescue/rescue_iso_host_toolchain_preflight_latest.json",
            "docs/evidence/runtime-results/rescue/rsvg_project_local_wrapper_validation_latest.json",
            "docs/evidence/runtime-results/rescue/rescue_live_build_config_preflight_latest.json",
            "docs/evidence/runtime-results/rescue/live_build_dpkg_preflight_latest.json",
        ],
        "allowed_working_directory": str(gate_analysis.get("expected_working_directory") or WORKING_DIRECTORY_REL),
        "allowed_command": str(gate_analysis.get("expected_command") or ""),
        "forbidden_invocations": [
            "lb build",
            'PATH="<repo>/build/rescue/tool-compat/bin:$PATH" lb build',
            "sudo lb build",
            "scripts/rescue/build-rescue-iso-controlled.sh",
        ],
        "operator_confirmation_required": True,
        "usb_write_allowed": False,
        "supported_target_architecture": "amd64",
        "unsupported_targets": ["i386", "arm64", "armhf"],
        "no_build_executed": True,
    }


def build_controlled_operator_build_plan(contract: dict[str, Any]) -> dict[str, Any]:
    contract_status = str(contract.get("contract_status") or "review_required")
    plan_status = "ready_for_operator" if contract_status == "ready" else "review_required"
    path_prefix = f"<repo>/{PATH_PREFIX_REL}"
    return {
        "plan_status": plan_status,
        "reason": (
            "Der direkte lb-build-Aufruf bleibt verboten; der naechste echte Build darf nur ueber den "
            "kontrollierten Operator-Pfad mit noauto und projektlokalem PATH-Praefix laufen."
            if plan_status == "ready_for_operator"
            else "Der Gate-Vertrag ist noch nicht konsistent genug dokumentiert."
        ),
        "required_gate_inputs": list(contract.get("required_inputs") or []),
        "required_env_vars": list(contract.get("required_env") or []),
        "required_marker_files": list(contract.get("required_marker_files") or []),
        "exact_operator_steps": [
            f'cd "{WORKING_DIRECTORY_REL}"',
            f'export PATH="{path_prefix}:$PATH"',
            "./auto/config",
            f'sudo env PATH="{path_prefix}:$PATH" lb build noauto',
        ],
        "exact_command_preview": (
            f'cd "{WORKING_DIRECTORY_REL}" && export PATH="{path_prefix}:$PATH" '
            f'&& ./auto/config && sudo env PATH="{path_prefix}:$PATH" lb build noauto'
        ),
        "working_directory": WORKING_DIRECTORY_REL,
        "path_prefix": PATH_PREFIX_REL,
        "logs": [
            "build/rescue/logs/controlled-iso-build/latest.log",
            "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json",
        ],
        "stop_conditions": [
            "Runtime-Gate nicht gruen",
            "DPKG-Preflight nicht ok/pre_chroot_ok",
            "rsvg-Wrapper nicht im PATH",
            "USB-Write bleibt blockiert",
        ],
        "expected_outputs": [
            "live-image-amd64.hybrid.iso im Live-Build-Arbeitsverzeichnis",
            "aktualisierte controlled_iso_build_latest_summary.json",
        ],
        "target_architecture": "amd64",
        "no_build_executed": True,
        "usb_write_allowed": False,
        "real_usb_write_allowed": False,
    }


def classify_rescue_iso_build_attempt(
    *,
    run_data: dict[str, Any] | None = None,
    result_data: dict[str, Any] | None = None,
    combined_log_text: str | None = None,
) -> dict[str, Any]:
    run_body = run_data or {}
    result_body = result_data or {}
    combined_log = combined_log_text or ""

    attempted = bool(run_body or result_body or combined_log.strip())
    iso_created = bool(result_body.get("iso_created"))
    usb_write_performed = bool(result_body.get("usb_write_performed"))
    exit_code = result_body.get("exit_code")
    if not isinstance(exit_code, int):
        exit_code = run_body.get("exit_code") if isinstance(run_body.get("exit_code"), int) else None

    raw_errors = [str(item) for item in (result_body.get("errors") or []) if str(item)]
    raw_status = str(result_body.get("result_status") or "").lower()
    gate_message_found = CONTROLLED_GATE_MESSAGE in combined_log
    sudo_policy_message_found = any(
        token in combined_log.lower()
        for token in (
            "sudo: ein terminal ist erforderlich",
            "sudo: ein passwort ist notwendig",
            "sudo: a terminal is required",
            "sudo: a password is required",
        )
    )
    result_error_code = str(result_body.get("error_code") or (raw_errors[0] if raw_errors else "")).strip()

    if gate_message_found and not iso_created:
        return {
            "attempted": attempted,
            "result_status": "blocked",
            "error_code": CONTROLLED_GATE_ERROR_CODE,
            "category": CONTROLLED_GATE_CATEGORY,
            "next_action": CONTROLLED_GATE_NEXT_ACTION,
            "summary": (
                "Direkter lb build wurde bewusst vom kontrollierten auto/build-Gate blockiert; "
                "zulaessig ist nur der kontrollierte Rescue-Buildpfad mit ./auto/config und lb build noauto."
            ),
            "gate_message_found": True,
            "direct_lb_build_blocked": True,
            "iso_created": False,
            "usb_write_performed": usb_write_performed,
            "exit_code": exit_code,
            "command": run_body.get("command"),
            "started_at": run_body.get("started_at"),
            "finished_at": result_body.get("finished_at") or run_body.get("finished_at"),
        }

    chroot_cleanup_failure = (
        "chroot/proc" in combined_log
        and (
            "Vorgang nicht zulässig" in combined_log
            or "Operation not permitted" in combined_log
        )
    ) or (
        "chroot: failed to run command" in combined_log
        and "/usr/bin/env" in combined_log
    )
    if (chroot_cleanup_failure or result_error_code == CHROOT_CLEANUP_ERROR_CODE) and not iso_created:
        return {
            "attempted": attempted,
            "result_status": "failed",
            "error_code": CHROOT_CLEANUP_ERROR_CODE,
            "category": CHROOT_CLEANUP_CATEGORY,
            "next_action": CHROOT_CLEANUP_NEXT_ACTION,
            "summary": (
                "live-build konnte den Chroot nicht sauber bereinigen (proc/Operation not permitted) "
                "oder der Chroot ist beschädigt (/usr/bin/env fehlt). Zuerst Mounts unter BUILD_TREE lösen, "
                "dann Tree bereinigen — nicht als isohybrid-Fehler behandeln."
            ),
            "gate_message_found": False,
            "direct_lb_build_blocked": False,
            "iso_created": False,
            "usb_write_performed": usb_write_performed,
            "exit_code": exit_code,
            "command": run_body.get("command"),
            "started_at": run_body.get("started_at"),
            "finished_at": result_body.get("finished_at") or run_body.get("finished_at"),
        }

    isohybrid_missing = "isohybrid: not found" in combined_log
    if (isohybrid_missing or result_error_code == ISOHYBRID_ERROR_CODE) and not iso_created:
        return {
            "attempted": attempted,
            "result_status": "failed",
            "error_code": ISOHYBRID_ERROR_CODE,
            "category": ISOHYBRID_CATEGORY,
            "next_action": ISOHYBRID_NEXT_ACTION,
            "summary": (
                "Die ISO wurde bis genisoimage erzeugt, aber der isohybrid-Schritt im Binary-Chroot "
                "fehlte (syslinux-utils in setuphelfer.list.binary erforderlich)."
            ),
            "gate_message_found": False,
            "direct_lb_build_blocked": False,
            "iso_created": False,
            "usb_write_performed": usb_write_performed,
            "exit_code": exit_code,
            "command": run_body.get("command"),
            "started_at": run_body.get("started_at"),
            "finished_at": result_body.get("finished_at") or run_body.get("finished_at"),
        }

    if (sudo_policy_message_found or result_error_code == CONTROLLED_ROOT_POLICY_ERROR_CODE) and not iso_created:
        return {
            "attempted": attempted,
            "result_status": "blocked",
            "error_code": CONTROLLED_ROOT_POLICY_ERROR_CODE,
            "category": CONTROLLED_ROOT_POLICY_CATEGORY,
            "next_action": CONTROLLED_ROOT_POLICY_NEXT_ACTION,
            "summary": (
                "Kontrollierte Root-Ausführung fehlt; starte den Wrapper aus einem echten Operator-Terminal "
                "mit sudo-Rechten oder richte eine eng begrenzte dokumentierte Operator-Policy ein."
            ),
            "gate_message_found": False,
            "direct_lb_build_blocked": False,
            "iso_created": False,
            "usb_write_performed": usb_write_performed,
            "exit_code": exit_code,
            "command": run_body.get("command"),
            "started_at": run_body.get("started_at"),
            "finished_at": result_body.get("finished_at") or run_body.get("finished_at"),
        }

    if not attempted:
        return {
            "attempted": False,
            "result_status": "not_started",
            "error_code": None,
            "category": None,
            "next_action": None,
            "summary": None,
            "gate_message_found": False,
            "direct_lb_build_blocked": False,
            "iso_created": False,
            "usb_write_performed": False,
            "exit_code": None,
            "command": None,
            "started_at": None,
            "finished_at": None,
        }

    if iso_created and exit_code == 0:
        result_status = "success"
    elif raw_status == "blocked":
        result_status = "blocked"
    elif raw_status == "failed" or (isinstance(exit_code, int) and exit_code != 0):
        result_status = "failed"
    else:
        result_status = "review_required"

    return {
        "attempted": attempted,
        "result_status": result_status,
        "error_code": result_error_code or None,
        "category": (
            CONTROLLED_ROOT_POLICY_CATEGORY
            if result_error_code == CONTROLLED_ROOT_POLICY_ERROR_CODE
            else ("execution_failure" if result_status == "failed" else None)
        ),
        "next_action": None,
        "summary": str((result_body.get("warnings") or [""])[0] or "").strip() or None,
        "gate_message_found": gate_message_found,
        "direct_lb_build_blocked": False,
        "iso_created": iso_created,
        "usb_write_performed": usb_write_performed,
        "exit_code": exit_code,
        "command": run_body.get("command"),
        "started_at": run_body.get("started_at"),
        "finished_at": result_body.get("finished_at") or run_body.get("finished_at"),
    }


def _attempt_specs() -> list[dict[str, str]]:
    return [
        {
            "kind": "controlled_wrapper",
            "run": CONTROLLED_RUN_LATEST_REL,
            "result": CONTROLLED_RESULT_LATEST_REL,
            "decision": CONTROLLED_DECISION_LATEST_REL,
            "log": CONTROLLED_COMBINED_LOG_LATEST_REL,
        },
        {
            "kind": "direct_lb_build",
            "run": RUN_LATEST_REL,
            "result": RESULT_LATEST_REL,
            "decision": DECISION_LATEST_REL,
            "log": COMBINED_LOG_LATEST_REL,
        },
    ]


def read_latest_rescue_iso_build_attempt(repo_root: Path) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for spec in _attempt_specs():
        run_path = repo_root / spec["run"]
        result_path = repo_root / spec["result"]
        decision_path = repo_root / spec["decision"]
        log_path = repo_root / spec["log"]

        run_data = _safe_read_json(run_path) or {}
        result_data = _safe_read_json(result_path) or {}
        decision_data = _safe_read_json(decision_path) or {}
        combined_log_text = _safe_read_text(log_path) or ""
        classified = classify_rescue_iso_build_attempt(
            run_data=run_data,
            result_data=result_data,
            combined_log_text=combined_log_text,
        )
        if not classified.get("attempted"):
            continue
        finished_at = _parse_iso(classified.get("finished_at")) or _parse_iso(classified.get("started_at"))
        if finished_at is None:
            for path in (result_path, run_path, log_path):
                try:
                    finished_at = datetime.fromtimestamp(path.stat().st_mtime)
                    break
                except OSError:
                    continue
        classified.update(
            {
                "kind": spec["kind"],
                "run_path": spec["run"] if run_path.exists() else None,
                "result_path": spec["result"] if result_path.exists() else None,
                "decision_path": spec["decision"] if decision_path.exists() else None,
                "combined_log_path": spec["log"] if log_path.exists() else None,
                "decision_status": decision_data.get("decision_status"),
                "decision_next_prompt": decision_data.get("next_recommended_prompt"),
                "_finished_sort_key": finished_at.timestamp() if finished_at else -1.0,
            }
        )
        candidates.append(classified)

    if not candidates:
        return classify_rescue_iso_build_attempt()

    best = max(candidates, key=lambda item: float(item.get("_finished_sort_key") or -1.0))
    best.pop("_finished_sort_key", None)
    return best
