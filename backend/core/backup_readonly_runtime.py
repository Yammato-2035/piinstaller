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
