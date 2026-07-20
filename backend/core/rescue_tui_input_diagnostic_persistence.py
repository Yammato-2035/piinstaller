"""Runtime-first TUI diagnostic evidence with late SETUP_LOGS persistence."""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from core.rescue_tui_input_diagnostic_evidence import (
    REQUIRED_FILES,
    assert_path_under_allowed_roots,
    finalize_run_dir,
    sha256_file,
)

RUNTIME_EVIDENCE_BASE = Path("/run/setuphelfer/tui-input-diagnostics")
DEFAULT_MOUNT_WAIT_TIMEOUT_S = 60.0
DEFAULT_MOUNT_WAIT_INTERVAL_S = 2.0

FORBIDDEN_NAME_CHARS = frozenset('<>:"\\|?*')


@dataclass(frozen=True)
class EvidenceRootResolution:
    runtime_root: Path
    persistent_root: Path | None
    persistent_available: bool
    source: str
    mount_target: str | None
    filesystem_type: str | None
    warnings: tuple[str, ...] = ()


@dataclass
class EvidenceFinalizeResult:
    status: str
    run_id: str
    runtime_path: str
    persistent_path: str | None = None
    persistent_copy_started: bool = False
    persistent_copy_completed: bool = False
    manifest_valid: bool = False
    sha256_valid: bool = False
    atomic_publish_completed: bool = False
    runtime_cleanup_allowed: bool = False
    shutdown_allowed: bool = False
    warnings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class ShutdownDecision:
    shutdown_allowed: bool
    reason: str
    operator_message_de: str
    persistence_status: str


ResolverFn = Callable[[bool], dict[str, Any] | None]


def runtime_evidence_base(*, override: Path | None = None) -> Path:
    if override is not None:
        return override
    env = os.environ.get("SETUPHELFER_TUI_INPUT_DIAG_ROOT", "").strip()
    if env:
        return Path(env)
    return RUNTIME_EVIDENCE_BASE


def resolve_runtime_evidence_root(*, override: Path | None = None) -> Path:
    """Always available working root (tmpfs /run or test override)."""
    root = runtime_evidence_base(override=override)
    root.mkdir(parents=True, exist_ok=True)
    assert_path_under_allowed_roots(
        root,
        [Path("/run/setuphelfer"), Path("/tmp"), Path("/media"), Path("/run/media"), root],
    )
    return root


def _default_resolve_setup_logs(allow_mount: bool) -> dict[str, Any] | None:
    try:
        from core.rescue_setup_logs_resolver import resolve_setup_logs

        return resolve_setup_logs(allow_mount=allow_mount)
    except Exception:
        return None


def _is_allowed_setup_logs_mount(mount: Path) -> bool:
    """Accept only known removable/media/run mounts (plus /tmp for unit tests)."""
    try:
        resolved = mount.resolve()
    except OSError:
        return False
    text = str(resolved)
    if text in {"/", "/home", "/opt", "/var", "/boot", "/root", "/usr", "/etc"}:
        return False
    # Reject static operator home media paths even if present in docs/import hints.
    if "/media/volker/" in text:
        return False
    allowed_prefixes = (
        "/run/setuphelfer/",
        "/run/setuphelfer-rescue/",
        "/media/",
        "/run/media/",
        "/tmp/",
    )
    return any(text.startswith(prefix) for prefix in allowed_prefixes)


def _persistent_root_from_resolution(
    resolved: dict[str, Any] | None,
    *,
    runtime_override: Path | None = None,
) -> EvidenceRootResolution:
    runtime = resolve_runtime_evidence_root(override=runtime_override)
    if not resolved or not resolved.get("resolved"):
        return EvidenceRootResolution(
            runtime_root=runtime,
            persistent_root=None,
            persistent_available=False,
            source="unresolved",
            mount_target=None,
            filesystem_type=None,
            warnings=("persistent_root_unavailable",),
        )
    mount = (
        resolved.get("actual_mountpoint")
        or resolved.get("setup_logs_root")
        or resolved.get("path")
        or ""
    )
    if not mount:
        return EvidenceRootResolution(
            runtime_root=runtime,
            persistent_root=None,
            persistent_available=False,
            source=str(resolved.get("resolution_status") or "empty_mount"),
            mount_target=None,
            filesystem_type=str(resolved.get("filesystem_type") or "") or None,
            warnings=("persistent_mount_empty",),
        )
    mount_path = Path(str(mount))
    try:
        resolved_mount = mount_path.resolve()
    except OSError:
        resolved_mount = mount_path
    if resolved_mount.is_symlink() or mount_path.is_symlink():
        return EvidenceRootResolution(
            runtime_root=runtime,
            persistent_root=None,
            persistent_available=False,
            source="rejected_symlink_mount",
            mount_target=str(resolved_mount),
            filesystem_type=str(resolved.get("filesystem_type") or "") or None,
            warnings=("symlink_mount_rejected",),
        )
    if not _is_allowed_setup_logs_mount(resolved_mount):
        return EvidenceRootResolution(
            runtime_root=runtime,
            persistent_root=None,
            persistent_available=False,
            source="rejected_mount",
            mount_target=str(resolved_mount),
            filesystem_type=str(resolved.get("filesystem_type") or "") or None,
            warnings=("persistent_mount_rejected",),
        )
    # Traversal / label sanity: basename should look like SETUP_LOGS* or be canonical mount.
    label = str(resolved.get("label") or resolved_mount.name).upper()
    if label and label not in {"SETUP_LOGS", "SETUPHELFER_LOGS"} and not label.startswith("SETUP_LOGS"):
        # Still allow canonical resolver mounts under /run/setuphelfer-rescue/media/SETUP_LOGS
        if "SETUP_LOGS" not in str(resolved_mount).upper() and "SETUPHELFER_LOGS" not in str(resolved_mount).upper():
            return EvidenceRootResolution(
                runtime_root=runtime,
                persistent_root=None,
                persistent_available=False,
                source="rejected_label",
                mount_target=str(resolved_mount),
                filesystem_type=str(resolved.get("filesystem_type") or "") or None,
                warnings=("wrong_label_rejected",),
            )
    persistent = resolved_mount / "tui-input-diagnostics"
    return EvidenceRootResolution(
        runtime_root=runtime,
        persistent_root=persistent,
        persistent_available=True,
        source=str(resolved.get("resolution_status") or "mounted_valid"),
        mount_target=str(resolved_mount),
        filesystem_type=str(resolved.get("filesystem_type") or "") or None,
    )


def resolve_tui_diagnostic_evidence_roots(
    *,
    allow_safe_mount: bool = False,
    resolver: ResolverFn | None = None,
    runtime_override: Path | None = None,
) -> EvidenceRootResolution:
    """Runtime root always; persistent root only when SETUP_LOGS is available."""
    runtime = resolve_runtime_evidence_root(override=runtime_override)
    persistent = resolve_persistent_evidence_root(
        allow_safe_mount=allow_safe_mount,
        resolver=resolver,
        runtime_override=runtime_override,
    )
    return EvidenceRootResolution(
        runtime_root=runtime,
        persistent_root=persistent.persistent_root,
        persistent_available=persistent.persistent_available,
        source=persistent.source,
        mount_target=persistent.mount_target,
        filesystem_type=persistent.filesystem_type,
        warnings=persistent.warnings,
    )


def resolve_persistent_evidence_root(
    *,
    allow_safe_mount: bool = False,
    resolver: ResolverFn | None = None,
    runtime_override: Path | None = None,
) -> EvidenceRootResolution:
    fn = resolver or _default_resolve_setup_logs
    resolved = fn(bool(allow_safe_mount))
    return _persistent_root_from_resolution(resolved, runtime_override=runtime_override)


def wait_for_persistent_evidence_root(
    *,
    timeout_s: float = DEFAULT_MOUNT_WAIT_TIMEOUT_S,
    interval_s: float = DEFAULT_MOUNT_WAIT_INTERVAL_S,
    allow_safe_mount: bool = True,
    resolver: ResolverFn | None = None,
    runtime_override: Path | None = None,
    monotonic: Callable[[], float] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> EvidenceRootResolution:
    """Poll until SETUP_LOGS is available or timeout (no busy-loop)."""
    clock = monotonic or time.monotonic
    nap = sleep or time.sleep
    deadline = clock() + max(0.0, float(timeout_s))
    last = resolve_persistent_evidence_root(
        allow_safe_mount=allow_safe_mount,
        resolver=resolver,
        runtime_override=runtime_override,
    )
    if last.persistent_available:
        return last
    while clock() < deadline:
        remaining = deadline - clock()
        nap(min(max(0.05, float(interval_s)), max(0.05, remaining)))
        last = resolve_persistent_evidence_root(
            allow_safe_mount=allow_safe_mount,
            resolver=resolver,
            runtime_override=runtime_override,
        )
        if last.persistent_available:
            return last
    warnings = tuple(last.warnings) + ("persistent_root_timeout",)
    return EvidenceRootResolution(
        runtime_root=last.runtime_root,
        persistent_root=None,
        persistent_available=False,
        source="timeout",
        mount_target=last.mount_target,
        filesystem_type=last.filesystem_type,
        warnings=warnings,
    )


def _validate_relative_name(name: str) -> None:
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError(f"INVALID_EVIDENCE_NAME:{name}")
    if any(ch in FORBIDDEN_NAME_CHARS for ch in name):
        raise ValueError(f"INVALID_EVIDENCE_NAME_CHARS:{name}")
    if ":" in name:
        raise ValueError(f"INVALID_EVIDENCE_NAME_COLON:{name}")


def _inventory_runtime_files(runtime_run_dir: Path) -> list[Path]:
    files: list[Path] = []
    for p in sorted(runtime_run_dir.iterdir()):
        if p.is_symlink():
            raise ValueError(f"SYMLINK_FORBIDDEN:{p.name}")
        if not p.is_file():
            continue
        if p.name.endswith(".partial"):
            continue
        _validate_relative_name(p.name)
        files.append(p)
    return files


def _dir_fsync(path: Path) -> None:
    try:
        fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _verify_copied_tree(src_files: list[Path], dest_dir: Path) -> tuple[bool, bool, list[str]]:
    """Return (manifest_ok_placeholder, sha_ok, errors)."""
    errors: list[str] = []
    for src in src_files:
        dst = dest_dir / src.name
        if not dst.is_file():
            errors.append(f"missing:{src.name}")
            continue
        if dst.is_symlink():
            errors.append(f"symlink:{src.name}")
            continue
        if dst.stat().st_size != src.stat().st_size:
            errors.append(f"size_mismatch:{src.name}")
            continue
        if sha256_file(dst) != sha256_file(src):
            errors.append(f"hash_mismatch:{src.name}")
    sha_ok = not errors
    return sha_ok, sha_ok, errors


def persist_runtime_evidence(
    runtime_run_dir: Path,
    persistent_base_dir: Path,
    run_id: str,
) -> EvidenceFinalizeResult:
    """Atomically publish a runtime run dir onto SETUP_LOGS via .<id>.partial."""
    result = EvidenceFinalizeResult(
        status="copying",
        run_id=run_id,
        runtime_path=str(runtime_run_dir),
    )
    if not runtime_run_dir.is_dir():
        result.status = "blocked"
        result.errors.append({"code": "runtime_missing", "detail": str(runtime_run_dir)})
        return result

    final_dir = persistent_base_dir / run_id
    partial_dir = persistent_base_dir / f".{run_id}.partial"

    if final_dir.exists():
        # Idempotent: already published.
        try:
            sha_ok = (final_dir / "SHA256SUMS").is_file() and (final_dir / "20-file-manifest.json").is_file()
        except OSError:
            sha_ok = False
        result.status = "persisted" if sha_ok else "review_required"
        result.persistent_path = str(final_dir)
        result.persistent_copy_started = True
        result.persistent_copy_completed = True
        result.manifest_valid = sha_ok
        result.sha256_valid = sha_ok
        result.atomic_publish_completed = True
        result.runtime_cleanup_allowed = sha_ok
        result.shutdown_allowed = sha_ok
        result.warnings.append({"code": "already_persisted", "detail": str(final_dir)})
        return result

    try:
        files = _inventory_runtime_files(runtime_run_dir)
    except ValueError as exc:
        result.status = "blocked"
        result.errors.append({"code": "runtime_inventory_failed", "detail": str(exc)})
        return result

    result.persistent_copy_started = True
    try:
        persistent_base_dir.mkdir(parents=True, exist_ok=True)
        if partial_dir.exists():
            shutil.rmtree(partial_dir)
        partial_dir.mkdir(parents=True, exist_ok=False)
        for src in files:
            dst = partial_dir / src.name
            shutil.copyfile(src, dst, follow_symlinks=False)
            with open(dst, "rb") as fh:
                os.fsync(fh.fileno())
        _dir_fsync(partial_dir)

        _sha_ok, _manifest_ok, errors = _verify_copied_tree(files, partial_dir)
        if errors:
            result.status = "blocked"
            result.errors.extend({"code": "verify_failed", "detail": e} for e in errors)
            return result

        # Refresh manifest/SHA on the partial tree for stick-native integrity.
        fin = finalize_run_dir(
            partial_dir,
            status="review_required",
            final_result=json.loads((partial_dir / "18-final-result.json").read_text(encoding="utf-8"))
            if (partial_dir / "18-final-result.json").is_file()
            else {"status": "review_required", "run_id": run_id},
        )
        result.manifest_valid = bool(fin.get("manifest_files"))
        # Re-verify after finalize refresh
        files2 = _inventory_runtime_files(partial_dir)
        # Compare against themselves (integrity) + required names
        missing_required = [n for n in REQUIRED_FILES if not (partial_dir / n).is_file()]
        if missing_required:
            result.status = "blocked"
            result.errors.append({"code": "required_missing", "detail": ",".join(missing_required)})
            return result
        # SHA256SUMS self-check
        sums = partial_dir / "SHA256SUMS"
        for line in sums.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            digest, name = line.split(None, 1)
            name = name.strip()
            actual = sha256_file(partial_dir / name)
            if actual != digest:
                result.status = "blocked"
                result.errors.append({"code": "sha256sums_mismatch", "detail": name})
                result.sha256_valid = False
                return result
        result.sha256_valid = True

        os.replace(partial_dir, final_dir)
        _dir_fsync(persistent_base_dir)
        result.atomic_publish_completed = True
        result.persistent_copy_completed = True
        result.persistent_path = str(final_dir)
        result.runtime_cleanup_allowed = True
        result.shutdown_allowed = True
        result.status = "persisted"
        return result
    except OSError as exc:
        result.status = "blocked"
        result.errors.append({"code": "persist_os_error", "detail": str(exc)})
        result.shutdown_allowed = False
        result.runtime_cleanup_allowed = False
        return result


def build_diagnostic_shutdown_decision(finalize_result: EvidenceFinalizeResult) -> ShutdownDecision:
    if (
        finalize_result.persistent_copy_completed
        and finalize_result.manifest_valid
        and finalize_result.sha256_valid
        and finalize_result.atomic_publish_completed
        and finalize_result.persistent_path
    ):
        return ShutdownDecision(
            shutdown_allowed=True,
            reason="persisted",
            persistence_status="abgeschlossen",
            operator_message_de=(
                "Evidence dauerhaft gespeichert:\n"
                f"{finalize_result.persistent_path}\n\n"
                "Manifest: gültig\nSHA256: gültig\nHerunterfahren: freigegeben"
            ),
        )
    if finalize_result.status == "waiting_for_persistent_root":
        return ShutdownDecision(
            shutdown_allowed=False,
            reason="waiting_for_persistent_root",
            persistence_status="wartet",
            operator_message_de=(
                "Diagnose abgeschlossen, aber die Ergebnisse sind noch nicht dauerhaft gespeichert.\n\n"
                "Der Rechner darf noch nicht heruntergefahren werden.\n\n"
                "Setuphelfer versucht weiterhin für begrenzte Zeit, SETUP_LOGS zu finden."
            ),
        )
    return ShutdownDecision(
        shutdown_allowed=False,
        reason=finalize_result.status or "runtime_only",
        persistence_status="fehlgeschlagen",
        operator_message_de=(
            "Die Diagnoseergebnisse konnten nicht auf SETUP_LOGS gespeichert werden.\n\n"
            "Status: review_required\n\n"
            "Nicht neu starten oder ausschalten, wenn die Laufdaten noch manuell gesichert werden sollen.\n"
            f"Runtime-Pfad: {finalize_result.runtime_path}"
        ),
    )


def complete_diagnostic_persistence(
    *,
    runtime_run_dir: Path,
    run_id: str,
    timeout_s: float = DEFAULT_MOUNT_WAIT_TIMEOUT_S,
    interval_s: float = DEFAULT_MOUNT_WAIT_INTERVAL_S,
    allow_safe_mount: bool = True,
    resolver: ResolverFn | None = None,
    runtime_override: Path | None = None,
    monotonic: Callable[[], float] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> EvidenceFinalizeResult:
    """Wait for SETUP_LOGS (bounded) and publish runtime evidence atomically."""
    # Ensure runtime finalize artifacts exist before copy.
    if not (runtime_run_dir / "18-final-result.json").is_file():
        finalize_run_dir(
            runtime_run_dir,
            status="review_required",
            final_result={"status": "review_required", "run_id": run_id, "persistence": "runtime_only"},
        )

    roots = wait_for_persistent_evidence_root(
        timeout_s=timeout_s,
        interval_s=interval_s,
        allow_safe_mount=allow_safe_mount,
        resolver=resolver,
        runtime_override=runtime_override,
        monotonic=monotonic,
        sleep=sleep,
    )
    if not roots.persistent_available or roots.persistent_root is None:
        out = EvidenceFinalizeResult(
            status="runtime_only",
            run_id=run_id,
            runtime_path=str(runtime_run_dir),
            persistent_path=None,
            shutdown_allowed=False,
            runtime_cleanup_allowed=False,
        )
        out.warnings.append({"code": "persistent_root_timeout", "detail": ",".join(roots.warnings)})
        # Annotate runtime final result
        try:
            final_path = runtime_run_dir / "18-final-result.json"
            data = json.loads(final_path.read_text(encoding="utf-8")) if final_path.is_file() else {}
            data["persistence_status"] = "runtime_only"
            data["shutdown_allowed"] = False
            finalize_run_dir(runtime_run_dir, status=str(data.get("status") or "review_required"), final_result=data)
        except (OSError, json.JSONDecodeError):
            pass
        return out

    published = persist_runtime_evidence(runtime_run_dir, roots.persistent_root, run_id)
    # Mirror persistence status into runtime final-result for operator/UI.
    try:
        final_path = runtime_run_dir / "18-final-result.json"
        data = json.loads(final_path.read_text(encoding="utf-8")) if final_path.is_file() else {}
        data["persistence_status"] = published.status
        data["persistent_path"] = published.persistent_path
        data["shutdown_allowed"] = published.shutdown_allowed
        finalize_run_dir(runtime_run_dir, status=str(data.get("status") or "review_required"), final_result=data)
    except (OSError, json.JSONDecodeError):
        pass
    return published


def maybe_cleanup_runtime(runtime_run_dir: Path, finalize_result: EvidenceFinalizeResult) -> bool:
    if not finalize_result.runtime_cleanup_allowed:
        return False
    try:
        shutil.rmtree(runtime_run_dir)
        return True
    except OSError:
        return False


def is_importable_run_dir(path: Path) -> bool:
    """Import must ignore .partial staging dirs."""
    name = path.name
    if name.startswith(".") and name.endswith(".partial"):
        return False
    if ".partial" in name:
        return False
    return path.is_dir()
