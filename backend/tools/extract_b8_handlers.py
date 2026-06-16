#!/usr/bin/env python3
"""One-shot extractor for Backup B.8 handlers (create/verify/delete/restore)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "backend/app.py"
BE = ROOT / "backend/core/backup_execute_handlers.py"
RT = ROOT / "backend/core/backup_readonly_runtime.py"

RANGES = [
    ("create_backup", 9631, 10776),
    ("verify_backup", 10777, 11371),
    ("delete_backup", 11372, 11521),
    ("restore_backup", 11634, 12122),
]

RENAME = {
    "create_backup": "create_backup",
    "verify_backup": "verify_backup",
    "delete_backup": "delete_backup",
    "restore_backup": "restore_backup",
}

SUBS = [
    (r"\bJSONResponse\b", "rt.json_response"),
    (r"\bwith_backup_contract\b", "rt.with_backup_contract"),
    (r"\brun_command_async\b", "rt.run_command_async"),
    (r"\brun_command\b", "rt.run_command"),
    (r"\bsudo_store\b", "rt.sudo_store()"),
    (r"\blogger\b", "rt.logger()"),
    (r"\bBACKUP_JOB_CANCEL\b", "rt.get_backup_job_cancel()"),
    (r"\bBACKUP_JOBS\b", "rt.get_backup_jobs()"),
    (r"\bROOT_RESTORE_BLOCKED_PREFIXES\b", "rt.root_restore_blocked_prefixes()"),
    (r"\bROOT_RESTORE_ALLOWED_PREFIXES\b", "rt.root_restore_allowed_prefixes()"),
    (r"\bRESTORE_PREVIEW_BASE\b", "rt.restore_preview_base()"),
    (r"\b_validate_restore_target_dir\b", "rt.validate_restore_target_dir"),
    (r"\b_validate_backup_dir\b", "rt.validate_backup_dir"),
    (r"\b_systemctl_run_argv\b", "rt.systemctl_run_argv"),
    (r"\b_sudo_n_true_failed_due_to_nnp\b", "rt.sudo_n_true_failed_due_to_nnp"),
    (r"\b_start_backup_via_helper\b", "rt.start_backup_via_helper"),
    (r"\b_read_backup_settings\b", "rt.read_backup_settings"),
    (r"\b_private_tmp_isolation_active\b", "rt.private_tmp_isolation_active"),
    (r"\b_plan_data_backup_sources\b", "rt.plan_data_backup_sources"),
    (r"\b_normalize_path\b", "rt.normalize_path"),
    (r"\b_normalize_backup_create_crypto_payload\b", "rt.normalize_backup_create_crypto_payload"),
    (r"\b_now_iso\b", "rt.now_iso"),
    (r"\b_new_job_id\b", "rt.new_job_id"),
    (r"\b_merge_backup_realtest_state\b", "rt.merge_backup_realtest_state"),
    (r"\b_is_under_allowed_root\b", "rt.is_under_allowed_root"),
    (r"\b_has_active_long_running_job\b", "rt.has_active_long_running_job"),
    (r"\b_get_backup_module\b", "rt.get_backup_module"),
    (r"\b_do_backup_logic\b", "rt.do_backup_logic"),
    (r"\b_detect_active_package_operations\b", "rt.detect_active_package_operations"),
    (r"\b_curl_put_with_progress\b", "rt.curl_put_with_progress"),
    (r"\b_cleanup_old_preview_dirs\b", "rt.cleanup_old_preview_dirs"),
    (r"\b_backup_start_mode\b", "rt.backup_start_mode"),
    (r"\b_backup_runner_status_file\b", "rt.backup_runner_status_file"),
    (r"\b_backup_runner_status_dir\b", "rt.backup_runner_status_dir"),
    (r"\b_backup_runner_mode\b", "rt.backup_runner_mode"),
    (r"\b_backup_runner_job_file\b", "rt.backup_runner_job_file"),
    (r"\b_backup_path_looks_encrypted\b", "rt.backup_path_looks_encrypted"),
    (r"\b_backup_create_needs_sudo_precheck\b", "rt.backup_create_needs_sudo_precheck"),
    (r"\b_analyze_tar_members\b", "rt.analyze_tar_members"),
]


def transform(block: str, fn: str) -> str:
    block = re.sub(
        r'@app\.post\("/api/backup/[^"]+"\)\nasync def \w+',
        f"async def {fn}",
        block,
        count=1,
    )
    for pat, rep in SUBS:
        block = re.sub(pat, rep, block)
    return block.rstrip() + "\n"


def main() -> None:
    lines = APP.read_text(encoding="utf-8").splitlines(keepends=True)
    blocks: list[tuple[str, str]] = []
    for name, start, end in reversed(RANGES):
        chunk = "".join(lines[start - 1 : end])
        lines[start - 1 : end] = []
        blocks.append((name, chunk))
    blocks.reverse()

    handlers = "\n\n".join(transform(b, RENAME[n]) for n, b in blocks)
    be_text = BE.read_text(encoding="utf-8")
    if "async def create_backup" not in be_text:
        BE.write_text(be_text.rstrip() + "\n\n\n" + handlers, encoding="utf-8")

    APP.write_text("".join(lines), encoding="utf-8")
    print("B.8 extracted", [n for n, _ in blocks])
    print("app lines", "".join(lines).count("\n") + 1)


if __name__ == "__main__":
    main()
