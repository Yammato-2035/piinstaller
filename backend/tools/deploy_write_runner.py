#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPLAY_SEEN: set[tuple[str, str]] = set()
_REPLAY_GUARD_ENV = "DEPLOY_RUNNER_REPLAY_GUARD"


def _clear_replay_guard_state_for_tests() -> None:
    """Nur für Unit-Tests: Prozess-internen Replay-Cache leeren."""
    _REPLAY_SEEN.clear()


def _replay_check_after_valid(job: dict[str, object]) -> str | None:
    """Nach erfolgreicher Schema-/Hash-Validierung: optional Replay innerhalb desselben Prozesses blocken."""
    if os.environ.get(_REPLAY_GUARD_ENV, "").strip() != "1":
        return None
    jid = str(job.get("job_id") or "")
    jh = str(job.get("job_hash") or "")
    key = (jid, jh)
    if key in _REPLAY_SEEN:
        return "DEPLOY_RUNNER_JOB_REPLAY_DUPLICATE"
    _REPLAY_SEEN.add(key)
    return None


def _blocked_payload(
    job_id: object,
    target: object,
    image_path: object,
    errors: list[str],
    *,
    warnings: list[str] | None = None,
    runner_state: str | None = None,
    lock_id: str | None = None,
    audit_entries_written: int = 0,
) -> dict[str, object]:
    return {
        "code": "DEPLOY_RUNNER_DRY_RUN_BLOCKED",
        "runner_state": runner_state,
        "job_id": job_id,
        "lock_id": lock_id,
        "audit_entries_written": audit_entries_written,
        "warnings": list(warnings or []),
        "errors": errors,
        "would_write": False,
        "target_device": target,
        "image_path": image_path,
    }


def _ok_payload(
    *,
    job_id: object,
    target: object,
    image_path: object,
    lock_id: str,
    audit_entries_written: int,
    warnings: list[str],
) -> dict[str, object]:
    return {
        "code": "DEPLOY_RUNNER_DRY_RUN_OK",
        "runner_state": "completed",
        "job_id": job_id,
        "lock_id": lock_id,
        "audit_entries_written": audit_entries_written,
        "warnings": warnings,
        "errors": [],
        "would_write": True,
        "target_device": target,
        "image_path": image_path,
    }


def dry_run_with_loaded_job(
    job: dict[str, object],
    *,
    job_file_path: str | None = None,
) -> tuple[int, dict[str, object]]:
    """
    Dry-run inkl. Lifecycle, Locking, TOCTOU-Rechecks (read-only), Audit.
    Kein Device-Zugriff, kein Shell/Kindprozess, kein Netzwerk.
    """
    backend_root = Path(__file__).resolve().parent.parent
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    from deploy import runner_lifecycle as rl
    from deploy.real_write_runner_contract import validate_real_write_job

    audit_n = 0

    def _audit(state: str, event: str, code: str, jid: str, dev: str) -> None:
        nonlocal audit_n
        rl.append_runner_audit(
            runner_state=state,
            job_id=jid,
            target_device=dev,
            event=event,
            code=code,
        )
        audit_n += 1

    if not isinstance(job, dict):
        return 1, _blocked_payload(None, None, None, ["job_not_object"], runner_state=rl.STATE_FAILED)

    jid = str(job.get("job_id") or "")
    tdev = str(job.get("target_device") or "")
    imgp = str(job.get("image_path") or "")

    lc, bcode = rl.build_runner_lifecycle(job_id=jid, job_path=job_file_path)
    if bcode == rl.DEPLOY_RUNNER_STATE_INVALID:
        return 1, _blocked_payload(jid, tdev, imgp, ["lifecycle_invalid"], runner_state=rl.STATE_FAILED)

    _audit(rl.STATE_CREATED, "lifecycle_build", bcode, jid, tdev)

    v = validate_real_write_job(job)
    valid = v.get("code") == "DEPLOY_RUNNER_JOB_VALID"
    exp_code = str(v.get("code") or "")

    if not valid:
        if exp_code == "DEPLOY_RUNNER_JOB_EXPIRED":
            lc, _ = rl.transition_runner_state(lc, rl.STATE_EXPIRED)
            st = str(lc.get("state") or rl.STATE_EXPIRED)
            _audit(st, "validate", exp_code, jid, tdev)
            return 1, _blocked_payload(
                jid,
                tdev,
                imgp,
                [exp_code] + list(v.get("errors") or []),
                warnings=list(v.get("warnings") or []),
                runner_state=st,
                audit_entries_written=audit_n,
            )
        lc, tc = rl.transition_runner_state(lc, rl.STATE_FAILED)
        st = str(lc.get("state") or rl.STATE_FAILED)
        _audit(st, "validate", exp_code, jid, tdev)
        return 1, _blocked_payload(
            jid,
            tdev,
            imgp,
            [exp_code] + list(v.get("errors") or []),
            warnings=list(v.get("warnings") or []),
            runner_state=st,
            audit_entries_written=audit_n,
        )

    lc, tc = rl.transition_runner_state(lc, rl.STATE_VALIDATED)
    if tc != rl.DEPLOY_RUNNER_LIFECYCLE_TRANSITION_OK:
        return 1, _blocked_payload(
            jid, tdev, imgp, [rl.DEPLOY_RUNNER_STATE_TRANSITION_BLOCKED], runner_state=str(lc.get("state"))
        )
    _audit(rl.STATE_VALIDATED, "validate", "DEPLOY_RUNNER_JOB_VALID", jid, tdev)

    replay_err = _replay_check_after_valid(job)
    if replay_err:
        lc, _ = rl.transition_runner_state(lc, rl.STATE_FAILED)
        _audit(rl.STATE_FAILED, "replay", replay_err, jid, tdev)
        return 1, _blocked_payload(
            jid,
            tdev,
            imgp,
            [replay_err],
            runner_state=rl.STATE_FAILED,
            audit_entries_written=audit_n,
        )

    lock_id = rl.new_lock_id()
    lock_ok, lock_err = rl.acquire_runner_lock(job_id=jid, lock_id=lock_id, state=rl.STATE_LOCKED)
    if not lock_ok:
        lc, _ = rl.transition_runner_state(lc, rl.STATE_FAILED)
        st = str(lc.get("state") or rl.STATE_FAILED)
        _audit(st, "lock_acquire", str(lock_err or "busy"), jid, tdev)
        return 1, _blocked_payload(
            jid,
            tdev,
            imgp,
            [str(lock_err or "DEPLOY_RUNNER_LOCK_BUSY")],
            runner_state=st,
            audit_entries_written=audit_n,
        )

    try:
        lc, tc = rl.transition_runner_state(lc, rl.STATE_LOCKED)
        if tc != rl.DEPLOY_RUNNER_LIFECYCLE_TRANSITION_OK:
            lc, _ = rl.transition_runner_state(lc, rl.STATE_FAILED)
            return 1, _blocked_payload(
                jid,
                tdev,
                imgp,
                [rl.DEPLOY_RUNNER_STATE_TRANSITION_BLOCKED],
                runner_state=rl.STATE_FAILED,
                lock_id=lock_id,
                audit_entries_written=audit_n,
            )
        _audit(rl.STATE_LOCKED, "lock_acquire", "ok", jid, tdev)

        baseline = rl.extract_runner_baseline_from_job(job)

        def _toctou(ck: str) -> tuple[bool, list[str]]:
            cur = rl.extract_runner_baseline_from_job(job)
            return rl.recheck_runner_consistency(checkpoint=ck, baseline=baseline, current=cur)

        ok_r, err_r = _toctou("pre_ready")
        if not ok_r:
            lc, _ = rl.transition_runner_state(lc, rl.STATE_ABORTED)
            st = str(lc.get("state") or rl.STATE_ABORTED)
            _audit(st, "toctou_pre_ready", err_r[0] if err_r else "drift", jid, tdev)
            return 1, _blocked_payload(
                jid,
                tdev,
                imgp,
                err_r,
                runner_state=st,
                lock_id=lock_id,
                audit_entries_written=audit_n,
            )

        lc, tc = rl.transition_runner_state(lc, rl.STATE_READY)
        if tc != rl.DEPLOY_RUNNER_LIFECYCLE_TRANSITION_OK:
            lc, _ = rl.transition_runner_state(lc, rl.STATE_ABORTED)
            return 1, _blocked_payload(
                jid,
                tdev,
                imgp,
                [rl.DEPLOY_RUNNER_STATE_TRANSITION_BLOCKED],
                runner_state=rl.STATE_ABORTED,
                lock_id=lock_id,
                audit_entries_written=audit_n,
            )
        _audit(rl.STATE_READY, "transition", "ready", jid, tdev)

        ok_w, err_w = _toctou("pre_writing")
        if not ok_w:
            lc, _ = rl.transition_runner_state(lc, rl.STATE_ABORTED)
            st = str(lc.get("state") or rl.STATE_ABORTED)
            _audit(st, "toctou_pre_writing", err_w[0] if err_w else "drift", jid, tdev)
            return 1, _blocked_payload(
                jid,
                tdev,
                imgp,
                err_w,
                runner_state=st,
                lock_id=lock_id,
                audit_entries_written=audit_n,
            )

        ok_v, err_v = _toctou("pre_verifying")
        if not ok_v:
            lc, _ = rl.transition_runner_state(lc, rl.STATE_ABORTED)
            st = str(lc.get("state") or rl.STATE_ABORTED)
            _audit(st, "toctou_pre_verifying", err_v[0] if err_v else "drift", jid, tdev)
            return 1, _blocked_payload(
                jid,
                tdev,
                imgp,
                err_v,
                runner_state=st,
                lock_id=lock_id,
                audit_entries_written=audit_n,
            )

        lc, tc = rl.transition_runner_state(lc, rl.STATE_COMPLETED)
        if tc != rl.DEPLOY_RUNNER_LIFECYCLE_TRANSITION_OK:
            lc, _ = rl.transition_runner_state(lc, rl.STATE_FAILED)
            return 1, _blocked_payload(
                jid,
                tdev,
                imgp,
                [rl.DEPLOY_RUNNER_STATE_TRANSITION_BLOCKED],
                runner_state=rl.STATE_FAILED,
                lock_id=lock_id,
                audit_entries_written=audit_n,
            )
        _audit(rl.STATE_COMPLETED, "completed", "DEPLOY_RUNNER_DRY_RUN_OK", jid, tdev)

        return 0, _ok_payload(
            job_id=jid,
            target=tdev,
            image_path=imgp,
            lock_id=lock_id,
            audit_entries_written=audit_n,
            warnings=list(v.get("warnings") or []),
        )
    finally:
        rl.release_runner_lock(jid)


def dry_run_job_path(job_arg: str) -> tuple[int, dict[str, object]]:
    """
    Liest Jobdatei nach Pfad-Containment, parst JSON, validiert Dry-run.
    """
    backend_root = Path(__file__).resolve().parent.parent
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    from deploy.real_write_runner_contract import validate_runner_job_file_location

    allowed_path, loc_err = validate_runner_job_file_location(job_arg)
    if loc_err or allowed_path is None:
        return 1, _blocked_payload(None, None, None, [loc_err or "job_path_blocked"])

    try:
        raw = allowed_path.read_text(encoding="utf-8")
        job = json.loads(raw)
    except OSError as e:
        return 1, _blocked_payload(None, None, None, [f"job_read_failed:{e}"])
    except json.JSONDecodeError as e:
        return 1, _blocked_payload(None, None, None, [f"job_json_invalid:{e}"])

    return dry_run_with_loaded_job(job if isinstance(job, dict) else {}, job_file_path=str(allowed_path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Setuphelfer deploy write runner (dry-run phase).")
    parser.add_argument("--job", required=True, help="Path to job JSON file.")
    parser.add_argument("--dry-run", action="store_true", help="Validate job only; no device access.")
    args = parser.parse_args()

    if not args.dry_run:
        sys.stderr.write("Only --dry-run is supported in this phase.\n")
        return 2

    code, payload = dry_run_job_path(args.job)
    _emit(payload)
    return code


def _emit(payload: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(payload, sort_keys=True, ensure_ascii=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
