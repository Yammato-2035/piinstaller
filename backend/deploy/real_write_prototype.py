from __future__ import annotations

import hashlib
import os
import secrets
import stat
import threading
import time
from typing import Any, Callable

from deploy.final_confirmation import check_final_confirmation_dryrun, get_final_confirmation_bindings
from deploy.hardware_gate import build_hardware_gate_report, validate_test_device
from deploy.image_inspect import inspect_deploy_image
from deploy.real_write_guard import _validate_harness_proof, build_real_write_snapshot
from deploy.write_execute import _image_valid

_PROTOTYPE_WRITE_LOCK = threading.Lock()
_CHUNK_BYTES = 1024 * 1024
_MAX_IMAGE_BYTES = 512 * 1024 * 1024
_REAL_WRITE_ENV_FLAG = "SETUPHELFER_ENABLE_REAL_WRITE"
_TESTMODE_ENV_FLAG = "SETUPHELFER_REAL_WRITE_TESTMODE"

# Overridable in tests only (no production use).
_is_block_device: Callable[[str], bool] | None = None


def _stat_is_block_device(path: str) -> bool:
    try:
        st = os.stat(path, follow_symlinks=False)
    except OSError:
        return False
    return stat.S_ISBLK(st.st_mode)


def _device_is_block(path: str) -> bool:
    if _is_block_device is not None:
        return bool(_is_block_device(path))
    return _stat_is_block_device(path)


def _testmode_enabled() -> bool:
    return str(os.environ.get(_TESTMODE_ENV_FLAG) or "").strip() == "1"


def _fail_after_chunks_n() -> int | None:
    if not _testmode_enabled():
        return None
    raw = str(os.environ.get("FAIL_AFTER_CHUNKS") or "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        return None
    return n if n >= 0 else None


def _env_truthy(name: str) -> bool:
    return _testmode_enabled() and str(os.environ.get(name) or "").strip() == "1"


def _fail_verify_device_path() -> str | None:
    """Nur Testmode: alternativer Pfad für Geräte-Reads im Verify (Mismatch-Injection)."""
    if not _testmode_enabled():
        return None
    if str(os.environ.get("FAIL_VERIFY_MISMATCH") or "").strip() != "1":
        return None
    p = str(os.environ.get("SETUPHELFER_FAIL_VERIFY_DEVICE_PATH") or "").strip()
    return p or None


def _inject_fail_before_open() -> bool:
    return _env_truthy("FAIL_BEFORE_OPEN")


def _inject_fail_after_open() -> bool:
    return _env_truthy("FAIL_AFTER_OPEN")


def _inject_fail_during_fsync() -> bool:
    return _env_truthy("FAIL_DURING_FSYNC")


def _inject_device_changed() -> bool:
    return _env_truthy("FAIL_DEVICE_CHANGED")


def _realpath_safe(path: str) -> str:
    try:
        return os.path.realpath(path)
    except OSError:
        return path


def _collect_drift_state(target_device: str, inspect_result: dict[str, Any], safety_summary: dict[str, Any]) -> dict[str, Any]:
    v = validate_test_device(target_device, inspect_result, safety_summary)
    snap = build_real_write_snapshot(target_device, inspect_result, safety_summary)
    ro = bool((snap.get("device_summary") or {}).get("readonly"))
    return {
        "target_device": target_device,
        "realpath": _realpath_safe(target_device),
        "fingerprint": str(snap.get("fingerprint") or ""),
        "transport": str(v.get("transport") or "").lower(),
        "removable": v.get("removable"),
        "mounted": bool(v.get("mounted")),
        "size_bytes": v.get("size_bytes"),
        "readonly": ro,
    }


def _drift_error_code(baseline: dict[str, Any], current: dict[str, Any]) -> str | None:
    if baseline["target_device"] != current["target_device"]:
        return "DEPLOY_REAL_WRITE_DEVICE_CHANGED"
    if baseline["realpath"] != current["realpath"]:
        return "DEPLOY_REAL_WRITE_DEVICE_CHANGED"
    if baseline["transport"] != current["transport"]:
        return "DEPLOY_REAL_WRITE_DEVICE_CHANGED"
    if baseline["removable"] != current["removable"]:
        return "DEPLOY_REAL_WRITE_DEVICE_CHANGED"
    if baseline["mounted"] != current["mounted"]:
        return "DEPLOY_REAL_WRITE_TARGET_REMOUNTED"
    if baseline["readonly"] != current["readonly"]:
        return "DEPLOY_REAL_WRITE_READONLY_CHANGED"
    if baseline["size_bytes"] != current["size_bytes"]:
        return "DEPLOY_REAL_WRITE_SIZE_CHANGED"
    if baseline["fingerprint"] != current["fingerprint"]:
        return "DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED"
    return None


def _empty_verify_result() -> dict[str, Any]:
    return {
        "verify_status": "failed",
        "bytes_verified": 0,
        "expected_sha256": None,
        "actual_sha256": None,
        "mismatch_offset": None,
        "sha256_hex": None,
    }


def _base_out(
    *,
    code: str,
    prototype_write_id: str,
    target_device: str | None,
    image_path: str | None,
    bytes_written: int = 0,
    duration_ms: int = 0,
    verify: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    vfy = verify if verify is not None else _empty_verify_result()
    if "sha256_hex" not in vfy and vfy.get("expected_sha256"):
        vfy = dict(vfy)
        vfy["sha256_hex"] = vfy.get("expected_sha256")
    return {
        "code": code,
        "prototype_write_id": prototype_write_id,
        "target_device": target_device,
        "image_path": image_path,
        "bytes_written": bytes_written,
        "chunk_size": _CHUNK_BYTES,
        "duration_ms": duration_ms,
        "verify": vfy,
        "verify_result": vfy,
        "warnings": list(warnings or []),
        "errors": list(errors or []),
    }


def _env_flag_enabled() -> bool:
    return str(os.environ.get(_REAL_WRITE_ENV_FLAG) or "").strip() == "1"


def _inspect_image_ok(image_path: str, expected_checksum: str) -> tuple[dict[str, Any] | None, str | None]:
    if not str(expected_checksum or "").strip():
        return None, "DEPLOY_REAL_WRITE_BLOCKED"
    insp = inspect_deploy_image(
        {
            "image_path": image_path,
            "expected_checksum": expected_checksum,
            "expected_architecture": "unknown",
            "expected_type": "unknown",
        }
    )
    if not _image_valid(insp):
        return None, "DEPLOY_REAL_WRITE_BLOCKED"
    size = int((insp.get("image") or {}).get("size_bytes") or 0)
    if size > _MAX_IMAGE_BYTES:
        return None, "DEPLOY_REAL_WRITE_IMAGE_TOO_LARGE"
    return insp, None


def _gate_hardware(
    *,
    target_device: str,
    inspect_result: dict[str, Any],
    safety_summary: dict[str, Any],
    write_harness_result: dict[str, Any],
    real_write_guard_result: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    rep = build_hardware_gate_report(
        {
            "target_device": target_device,
            "inspect_result": inspect_result,
            "safety_summary": safety_summary,
            "write_harness_result": write_harness_result,
            "final_confirmation_result": {"code": "DEPLOY_FINAL_CONFIRMATION_READY"},
            "real_write_guard_result": real_write_guard_result,
        }
    )
    if str(rep.get("readiness_level") or "") != "test_ready":
        return None, "DEPLOY_REAL_WRITE_BLOCKED"
    return rep, None


def _fingerprint_match(guard_snapshot: dict[str, Any], target_device: str, inspect_result: dict[str, Any], safety_summary: dict[str, Any]) -> bool:
    fp = str(guard_snapshot.get("fingerprint") or "")
    if not fp:
        return False
    fresh = build_real_write_snapshot(target_device, inspect_result, safety_summary)
    return str(fresh.get("fingerprint") or "") == fp


def _target_device_checks(v: dict[str, Any]) -> str | None:
    if not bool(v.get("eligible")):
        r = v.get("reasons") if isinstance(v.get("reasons"), list) else []
        if r:
            return str(r[0])
        return "DEPLOY_REAL_WRITE_BLOCKED"
    transport = str(v.get("transport") or "").lower()
    if transport not in {"usb", "sdcard"}:
        return "DEPLOY_REAL_WRITE_BLOCKED"
    if bool(v.get("removable")) is not True:
        return "DEPLOY_REAL_WRITE_BLOCKED"
    if bool(v.get("mounted")):
        return "DEPLOY_REAL_WRITE_BLOCKED"
    return None


def verify_written_range(
    image_path: str,
    device_path: str,
    nbytes: int,
    *,
    verify_device_path: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Vergleicht exakt die ersten nbytes Bytes von image_path mit device_path (oder verify_device_path).
    Keine Retries, keine Reparatur. Liefert expected_sha256/actual_sha256 über den gelesenen Bereich.
    """
    out_base: dict[str, Any] = {
        "verify_status": "failed",
        "bytes_verified": 0,
        "expected_sha256": None,
        "actual_sha256": None,
        "mismatch_offset": None,
        "sha256_hex": None,
    }
    if nbytes <= 0:
        out_base["verify_status"] = "failed"
        return "failed", out_base
    dev_path = verify_device_path if verify_device_path else device_path
    h_src = hashlib.sha256()
    h_dst = hashlib.sha256()
    offset_acc = 0
    try:
        with open(image_path, "rb", buffering=0) as src, open(dev_path, "rb", buffering=0) as dst:
            remain = nbytes
            while remain > 0:
                take = min(_CHUNK_BYTES, remain)
                bs = src.read(take)
                if len(bs) != take:
                    out_base["bytes_verified"] = offset_acc
                    out_base["verify_status"] = "failed"
                    return "failed", out_base
                bd = dst.read(take)
                if len(bd) != take:
                    h_src.update(bs)
                    h_dst.update(bd)
                    out_base["bytes_verified"] = offset_acc + len(bd)
                    out_base["expected_sha256"] = h_src.hexdigest()
                    out_base["actual_sha256"] = h_dst.hexdigest()
                    out_base["sha256_hex"] = out_base["expected_sha256"]
                    out_base["verify_status"] = "failed"
                    return "failed", out_base
                if bs != bd:
                    mismatch_at = None
                    for i, (bx, by) in enumerate(zip(bs, bd)):
                        if bx != by:
                            mismatch_at = offset_acc + i
                            break
                    h_src.update(bs)
                    h_dst.update(bd)
                    out_base["bytes_verified"] = offset_acc + take
                    out_base["expected_sha256"] = h_src.hexdigest()
                    out_base["actual_sha256"] = h_dst.hexdigest()
                    out_base["mismatch_offset"] = mismatch_at
                    out_base["sha256_hex"] = out_base["expected_sha256"]
                    out_base["verify_status"] = "mismatch"
                    return "mismatch", out_base
                h_src.update(bs)
                h_dst.update(bd)
                offset_acc += take
                remain -= take
    except OSError:
        out_base["bytes_verified"] = offset_acc
        out_base["verify_status"] = "failed"
        return "failed", out_base
    exp_h = h_src.hexdigest()
    act_h = h_dst.hexdigest()
    out_base["expected_sha256"] = exp_h
    out_base["actual_sha256"] = act_h
    out_base["bytes_verified"] = nbytes
    out_base["sha256_hex"] = exp_h
    if exp_h != act_h:
        out_base["verify_status"] = "mismatch"
        return "mismatch", out_base
    out_base["verify_status"] = "verified"
    return "verified", out_base


def _run_drift_gate(
    baseline: dict[str, Any],
    target_device: str,
    inspect_result: dict[str, Any],
    safety_summary: dict[str, Any],
    guard_fp: str,
) -> str | None:
    if _inject_device_changed():
        return "DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED"
    cur = _collect_drift_state(target_device, inspect_result, safety_summary)
    drift = _drift_error_code(baseline, cur)
    if drift:
        return drift
    if str(cur.get("fingerprint") or "") != str(guard_fp or ""):
        return "DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED"
    return None


def execute_deploy_real_write_prototype(request: dict[str, Any]) -> dict[str, Any]:
    prototype_write_id = secrets.token_hex(16)
    t0 = time.monotonic()
    target_device = str(request.get("target_device") or "").strip()
    image_path = str(request.get("image_path") or "").strip()
    expected_checksum = str(request.get("expected_checksum") or "").strip()
    inspect_result = request.get("inspect_result") if isinstance(request.get("inspect_result"), dict) else {}
    safety_summary = request.get("safety_summary") if isinstance(request.get("safety_summary"), dict) else {}
    write_harness_result = request.get("write_harness_result") if isinstance(request.get("write_harness_result"), dict) else {}
    real_write_guard_result = request.get("real_write_guard_result") if isinstance(request.get("real_write_guard_result"), dict) else {}
    guard_snapshot = request.get("guard_snapshot") if isinstance(request.get("guard_snapshot"), dict) else {}
    final_confirmation_id = str(request.get("final_confirmation_id") or "").strip()
    confirmation_token = str(request.get("confirmation_token") or "").strip()
    target_snapshot = request.get("target_snapshot") if isinstance(request.get("target_snapshot"), dict) else {}
    guard_fp = str(guard_snapshot.get("fingerprint") or "")

    def _done(code: str, **kwargs: Any) -> dict[str, Any]:
        dur = int((time.monotonic() - t0) * 1000)
        return _base_out(
            code=code,
            prototype_write_id=prototype_write_id,
            target_device=kwargs.get("target_device", target_device or None),
            image_path=kwargs.get("image_path", image_path or None),
            bytes_written=int(kwargs.get("bytes_written") or 0),
            duration_ms=dur,
            verify=kwargs.get("verify"),
            warnings=kwargs.get("warnings"),
            errors=kwargs.get("errors"),
        )

    if not _env_flag_enabled():
        return _done("DEPLOY_REAL_WRITE_FEATURE_DISABLED", errors=["DEPLOY_REAL_WRITE_FEATURE_DISABLED"])

    if not target_device or not image_path:
        return _done("DEPLOY_REAL_WRITE_BLOCKED", errors=["DEPLOY_REAL_WRITE_BLOCKED"])

    if str(real_write_guard_result.get("code") or "") != "DEPLOY_REAL_WRITE_READY":
        return _done("DEPLOY_REAL_WRITE_BLOCKED", errors=["DEPLOY_REAL_WRITE_BLOCKED"])

    if not _validate_harness_proof(write_harness_result):
        return _done("DEPLOY_REAL_WRITE_BLOCKED", errors=["DEPLOY_REAL_WRITE_BLOCKED_NO_HARNESS_PROOF"])

    fc_out = check_final_confirmation_dryrun(
        {
            "final_confirmation_id": final_confirmation_id,
            "confirmation_token": confirmation_token,
            "target_snapshot": target_snapshot,
        }
    )
    if str(fc_out.get("code") or "") != "DEPLOY_FINAL_CONFIRMATION_READY":
        return _done("DEPLOY_REAL_WRITE_BLOCKED", errors=[str(fc_out.get("code") or "DEPLOY_REAL_WRITE_BLOCKED")])

    bind = get_final_confirmation_bindings(final_confirmation_id)
    if not bind:
        return _done("DEPLOY_REAL_WRITE_BLOCKED", errors=["DEPLOY_FINAL_CONFIRMATION_NOT_FOUND"])
    if str(bind.get("image_path") or "") != image_path:
        return _done("DEPLOY_REAL_WRITE_BLOCKED", errors=["DEPLOY_FINAL_CONFIRMATION_TARGET_MISMATCH"])
    if str(bind.get("target_device") or "") != target_device:
        return _done("DEPLOY_REAL_WRITE_BLOCKED", errors=["DEPLOY_FINAL_CONFIRMATION_TARGET_MISMATCH"])

    _, hg_err = _gate_hardware(
        target_device=target_device,
        inspect_result=inspect_result,
        safety_summary=safety_summary,
        write_harness_result=write_harness_result,
        real_write_guard_result=real_write_guard_result,
    )
    if hg_err:
        return _done(hg_err, errors=[hg_err])

    if str(guard_snapshot.get("target_device") or "") != target_device:
        return _done("DEPLOY_REAL_WRITE_BLOCKED", errors=["DEPLOY_REAL_WRITE_BLOCKED"])

    if not _fingerprint_match(guard_snapshot, target_device, inspect_result, safety_summary):
        return _done("DEPLOY_REAL_WRITE_BLOCKED", errors=["DEPLOY_REAL_WRITE_BLOCKED_FINGERPRINT_MISMATCH"])

    insp, ierr = _inspect_image_ok(image_path, expected_checksum)
    if ierr:
        return _done(ierr, errors=[ierr])
    assert insp is not None
    nbytes = int((insp.get("image") or {}).get("size_bytes") or 0)
    if nbytes > _MAX_IMAGE_BYTES:
        return _done("DEPLOY_REAL_WRITE_IMAGE_TOO_LARGE", errors=["DEPLOY_REAL_WRITE_IMAGE_TOO_LARGE"])

    v = validate_test_device(target_device, inspect_result, safety_summary)
    t_err = _target_device_checks(v)
    if t_err:
        return _done("DEPLOY_REAL_WRITE_BLOCKED", errors=[t_err])

    if not _device_is_block(target_device):
        return _done("DEPLOY_REAL_WRITE_BLOCKED", errors=["DEPLOY_REAL_WRITE_BLOCKED"])

    warnings = list(insp.get("warnings") or [])

    if not _PROTOTYPE_WRITE_LOCK.acquire(blocking=False):
        return _done("DEPLOY_REAL_WRITE_ABORTED", errors=["DEPLOY_REAL_WRITE_ABORTED"])

    try:
        v_pre = validate_test_device(target_device, inspect_result, safety_summary)
        pre_err = _target_device_checks(v_pre)
        if pre_err:
            return _done("DEPLOY_REAL_WRITE_BLOCKED", warnings=warnings, errors=[pre_err])
        if str(guard_snapshot.get("target_device") or "") != target_device:
            return _done("DEPLOY_REAL_WRITE_DEVICE_CHANGED", errors=["DEPLOY_REAL_WRITE_DEVICE_CHANGED"])
        if not _fingerprint_match(guard_snapshot, target_device, inspect_result, safety_summary):
            return _done("DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED", errors=["DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED"])
        if not _env_flag_enabled():
            return _done("DEPLOY_REAL_WRITE_FEATURE_DISABLED", errors=["DEPLOY_REAL_WRITE_FEATURE_DISABLED"])
        if not _validate_harness_proof(write_harness_result):
            return _done("DEPLOY_REAL_WRITE_BLOCKED", errors=["DEPLOY_REAL_WRITE_BLOCKED_NO_HARNESS_PROOF"])
        fc2 = check_final_confirmation_dryrun(
            {
                "final_confirmation_id": final_confirmation_id,
                "confirmation_token": confirmation_token,
                "target_snapshot": target_snapshot,
            }
        )
        if str(fc2.get("code") or "") != "DEPLOY_FINAL_CONFIRMATION_READY":
            return _done("DEPLOY_REAL_WRITE_BLOCKED", errors=[str(fc2.get("code") or "DEPLOY_REAL_WRITE_BLOCKED")])
        insp2, ierr2 = _inspect_image_ok(image_path, expected_checksum)
        if ierr2 or not insp2:
            return _done(ierr2 or "DEPLOY_REAL_WRITE_BLOCKED", errors=[ierr2 or "DEPLOY_REAL_WRITE_BLOCKED"])
        if int((insp2.get("image") or {}).get("size_bytes") or 0) != nbytes:
            return _done("DEPLOY_REAL_WRITE_SIZE_CHANGED", errors=["DEPLOY_REAL_WRITE_SIZE_CHANGED"])

        baseline = _collect_drift_state(target_device, inspect_result, safety_summary)
        if str(baseline.get("fingerprint") or "") != guard_fp:
            return _done("DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED", errors=["DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED"])

        drift_err = _run_drift_gate(baseline, target_device, inspect_result, safety_summary, guard_fp)
        if drift_err:
            return _done(drift_err, errors=[drift_err])

        if _inject_fail_before_open():
            return _done("DEPLOY_REAL_WRITE_ABORTED", warnings=warnings, errors=["FAIL_BEFORE_OPEN"], verify=_empty_verify_result())

        bytes_written = 0
        verify_dev_override = _fail_verify_device_path()
        fail_chunks_limit = _fail_after_chunks_n()
        chunks_written = 0

        src = None
        dst = None
        try:
            src = open(image_path, "rb", buffering=0)
            dst = open(target_device, "rb+", buffering=0)
            if _inject_fail_after_open():
                return _done(
                    "DEPLOY_REAL_WRITE_ABORTED",
                    warnings=warnings,
                    errors=["FAIL_AFTER_OPEN"],
                    verify=_empty_verify_result(),
                )

            drift_err2 = _run_drift_gate(baseline, target_device, inspect_result, safety_summary, guard_fp)
            if drift_err2:
                return _done(drift_err2, errors=[drift_err2])

            dst.seek(0)
            remain = nbytes
            while remain > 0:
                drift_err_loop = _run_drift_gate(baseline, target_device, inspect_result, safety_summary, guard_fp)
                if drift_err_loop:
                    return _done(
                        drift_err_loop,
                        bytes_written=bytes_written,
                        warnings=warnings,
                        errors=[drift_err_loop],
                        verify=_empty_verify_result(),
                    )
                take = min(_CHUNK_BYTES, remain)
                buf = src.read(take)
                if len(buf) != take:
                    return _done(
                        "DEPLOY_REAL_WRITE_ABORTED",
                        warnings=warnings,
                        errors=["DEPLOY_REAL_WRITE_ABORTED"],
                        bytes_written=bytes_written,
                        verify=_empty_verify_result(),
                    )
                dst.write(buf)
                bytes_written += len(buf)
                chunks_written += 1
                remain -= take
                if fail_chunks_limit is not None and chunks_written >= fail_chunks_limit:
                    break

            dst.flush()
            if _inject_fail_during_fsync():
                raise OSError(5, "FAIL_DURING_FSYNC")
            os.fsync(dst.fileno())
        except OSError:
            return _done(
                "DEPLOY_REAL_WRITE_ABORTED",
                target_device=target_device,
                image_path=image_path,
                bytes_written=bytes_written,
                warnings=warnings,
                errors=["DEPLOY_REAL_WRITE_ABORTED"],
                verify=_empty_verify_result(),
            )
        finally:
            if src is not None:
                try:
                    src.close()
                except OSError:
                    pass
            if dst is not None:
                try:
                    dst.close()
                except OSError:
                    pass

        drift_err3 = _run_drift_gate(baseline, target_device, inspect_result, safety_summary, guard_fp)
        if drift_err3:
            return _done(
                drift_err3,
                bytes_written=bytes_written,
                warnings=warnings,
                errors=[drift_err3],
                verify=_empty_verify_result(),
            )

        st_verify, verify_payload = verify_written_range(
            image_path,
            target_device,
            nbytes,
            verify_device_path=verify_dev_override,
        )
        if st_verify == "verified":
            verify_payload["verify_status"] = "verified"
            return _done(
                "DEPLOY_REAL_WRITE_COMPLETED",
                bytes_written=bytes_written,
                warnings=warnings,
                verify=verify_payload,
            )
        if st_verify == "mismatch":
            return _done(
                "DEPLOY_REAL_WRITE_VERIFY_FAILED",
                bytes_written=bytes_written,
                warnings=warnings,
                errors=["DEPLOY_REAL_WRITE_VERIFY_FAILED"],
                verify=verify_payload,
            )
        return _done(
            "DEPLOY_REAL_WRITE_VERIFY_FAILED",
            bytes_written=bytes_written,
            warnings=warnings,
            errors=["DEPLOY_REAL_WRITE_VERIFY_FAILED"],
            verify=verify_payload,
        )
    finally:
        _PROTOTYPE_WRITE_LOCK.release()
