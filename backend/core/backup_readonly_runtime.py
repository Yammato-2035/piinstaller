"""
Backup readonly runtime — lazy app adapters for extracted GET handlers (Phase B.2).
"""

from __future__ import annotations

from typing import Any, Callable


def _app():
    import app as app_module

    return app_module


def get_backup_jobs() -> dict[str, dict[str, Any]]:
    return _app().BACKUP_JOBS


def sync_stale_runner_job(job_id: str) -> None:
    _app()._sync_stale_runner_job_from_systemd(job_id)


def job_snapshot(job: dict[str, Any]) -> dict[str, Any]:
    return _app()._job_snapshot(job)


def read_backup_runner_status(job_id: str) -> dict[str, Any] | None:
    return _app()._read_backup_runner_status(job_id)


def sync_ram_job_from_runner(job_id: str) -> None:
    _app()._sync_ram_job_from_runner(job_id)


def runner_status_to_job(status: dict[str, Any]) -> dict[str, Any]:
    return _app()._runner_status_to_job(status)


def read_backup_settings() -> dict[str, Any]:
    return _app()._read_backup_settings()


def systemd_timer_name(rule_id: str) -> str:
    return _app()._systemd_timer_name(rule_id)


def run_command(cmd: str, **kwargs: Any) -> dict[str, Any]:
    return _app().run_command(cmd, **kwargs)


def with_backup_contract(payload: dict[str, Any], code: str, severity: str, details: dict | None = None):
    from modules.backup import with_backup_contract as _wbc

    return _wbc(payload, code, severity, details)


def check_installed(name: str) -> bool:
    return _app().check_installed(name)


def lsblk_tree() -> dict[str, Any]:
    return _app()._lsblk_tree()


def findmnt_mounts() -> list[dict[str, Any]]:
    return _app()._findmnt_mounts()


def find_lsblk_by_mountpoint(mountpoint: str):
    return _app()._find_lsblk_by_mountpoint(mountpoint)


def find_lsblk_by_name(name: str):
    return _app()._find_lsblk_by_name(name)


def find_disk_by_name(name: str):
    return _app()._find_disk_by_name(name)


def disk_is_system(disk: dict[str, Any]) -> bool:
    return _app()._disk_is_system(disk)


def mountpoints_for_disk(disk_dev: str) -> list[str]:
    return _app()._mountpoints_for_disk(disk_dev)


def sanitize_label(label: str, max_len: int = 16) -> str:
    return _app()._sanitize_label(label, max_len=max_len)


def validate_backup_list_dir(backup_dir: str):
    return _app()._validate_backup_list_dir(backup_dir)


def load_backup_index():
    return _app()._load_backup_index()


def backup_profiles_list_payload() -> dict[str, Any]:
    return _app()._backup_profiles_list_payload()


def get_backup_module():
    return _app()._get_backup_module()


def backup_job_id_re():
    return _app()._BACKUP_JOB_ID_RE


def read_backup_evidence_manifest_disk(job_id: str):
    return _app()._read_backup_evidence_manifest_disk(job_id)


def normalize_evidence_api_payload(manifest, path):
    return _app()._normalize_evidence_api_payload(manifest, path)


def logger():
    return _app().logger


def json_response(**kwargs):
    from fastapi.responses import JSONResponse

    return JSONResponse(**kwargs)


def validate_backup_dir(path_str: str) -> str:
    return _app()._validate_backup_dir(path_str)


def sudo_password() -> str:
    return _app().sudo_store.get_password() or ""


def backup_target_err_to_api() -> dict[str, str]:
    return _app()._BACKUP_TARGET_ERR_TO_API


def systemctl_run_argv(argv: list[str], *, timeout: int) -> dict[str, Any]:
    return _app()._systemctl_run_argv(argv, timeout=timeout)


def get_backup_job_cancel() -> dict[str, Any]:
    return _app().BACKUP_JOB_CANCEL


def run_backup_evidence_collect(job_id: str):
    return _app()._run_backup_evidence_collect(job_id)


def default_backup_settings() -> dict[str, Any]:
    return _app()._default_backup_settings()


def ensure_schedule_migration(settings: dict[str, Any]) -> dict[str, Any]:
    return _app()._ensure_schedule_migration(settings)


def write_backup_settings(settings: dict[str, Any], *, sudo_password: str) -> None:
    _app()._write_backup_settings(settings, sudo_password=sudo_password)


def apply_backup_schedule(settings: dict[str, Any], *, sudo_password: str) -> None:
    _app()._apply_backup_schedule(settings, sudo_password=sudo_password)


async def run_command_async(cmd, sudo: bool = False, sudo_password: str | None = None, timeout: int = 10) -> dict[str, Any]:
    return await _app().run_command_async(cmd, sudo=sudo, sudo_password=sudo_password, timeout=timeout)


def sudo_store():
    return _app().sudo_store


def clone_disk_info(sudo_password: str | None = None) -> dict[str, Any]:
    return _app()._clone_disk_info(sudo_password=sudo_password)


def invalidate_clone_disk_info_cache() -> None:
    _app()._clone_disk_info_cache_ts = 0


def has_active_long_running_job() -> bool:
    return _app()._has_active_long_running_job()


def new_job_id() -> str:
    return _app()._new_job_id()


def now_iso() -> str:
    return _app()._now_iso()


def do_clone_logic(
    target_device: str,
    sudo_password: str,
    job: dict[str, Any],
    cancel_event=None,
) -> dict[str, Any]:
    return _app()._do_clone_logic(target_device, sudo_password, job, cancel_event=cancel_event)


def normalize_path(path_str: str) -> Path:
    return _app()._normalize_path(path_str)


def is_under_allowed_root(p: Path) -> bool:
    return _app()._is_under_allowed_root(p)


def detect_active_package_operations() -> list[dict[str, Any]]:
    return _app()._detect_active_package_operations()


def private_tmp_isolation_active() -> bool:
    return _app()._private_tmp_isolation_active()


def backup_create_needs_sudo_precheck(*args, **kwargs) -> bool:
    return _app()._backup_create_needs_sudo_precheck(*args, **kwargs)


def sudo_n_true_failed_due_to_nnp(sudo_test: dict) -> bool:
    return _app()._sudo_n_true_failed_due_to_nnp(sudo_test)


def normalize_backup_create_crypto_payload(data: dict) -> dict:
    return _app()._normalize_backup_create_crypto_payload(data)


def merge_backup_realtest_state(**kwargs) -> None:
    _app()._merge_backup_realtest_state(**kwargs)


def do_backup_logic(*args, **kwargs):
    return _app()._do_backup_logic(*args, **kwargs)


def backup_runner_mode() -> str:
    return _app()._backup_runner_mode()


def backup_start_mode() -> str:
    return _app()._backup_start_mode()


def start_backup_via_helper(job_id: str):
    return _app()._start_backup_via_helper(job_id)


def backup_runner_status_dir() -> Path:
    return _app()._backup_runner_status_dir()


def backup_runner_status_file(job_id: str) -> Path:
    return _app()._backup_runner_status_file(job_id)


def backup_runner_job_file(job_id: str) -> Path:
    return _app()._backup_runner_job_file(job_id)


def systemctl_run_argv(argv: list[str], *, timeout: int) -> dict[str, Any]:
    return _app()._systemctl_run_argv(argv, timeout=timeout)


def backup_path_looks_encrypted(path: str) -> bool:
    return _app()._backup_path_looks_encrypted(path)


def curl_put_with_progress(*args, **kwargs):
    return _app()._curl_put_with_progress(*args, **kwargs)


def plan_data_backup_sources():
    return _app()._plan_data_backup_sources()


def data_required_source_candidates() -> list:
    return _app()._data_required_source_candidates()


def data_optional_source_candidates() -> list:
    return _app()._data_optional_source_candidates()


def validate_restore_target_dir(path_str: str) -> str:
    return _app()._validate_restore_target_dir(path_str)


def analyze_tar_members(backup_file: str) -> dict:
    return _app()._analyze_tar_members(backup_file)


def cleanup_old_preview_dirs(keep_dir: Path, max_age_seconds: int | None = None) -> None:
    if max_age_seconds is None:
        _app()._cleanup_old_preview_dirs(keep_dir)
    else:
        _app()._cleanup_old_preview_dirs(keep_dir, max_age_seconds=max_age_seconds)


def restore_preview_base() -> Path:
    return _app().RESTORE_PREVIEW_BASE


def root_restore_allowed_prefixes() -> list[str]:
    return _app().ROOT_RESTORE_ALLOWED_PREFIXES


def root_restore_blocked_prefixes() -> list[str]:
    return _app().ROOT_RESTORE_BLOCKED_PREFIXES
