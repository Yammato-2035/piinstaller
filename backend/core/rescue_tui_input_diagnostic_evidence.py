"""Atomic evidence writer for TUI input diagnostic runs."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "00-run-meta.json",
    "01-machine-identity-redacted.json",
    "02-kernel-cmdline.txt",
    "03-input-device-inventory.json",
    "04-internal-keyboard-test.json",
    "05-external-keyboard-test.json",
    "06-tui-menu-input-test.json",
    "07-whiptail-process.json",
    "08-whiptail-cpu-samples.jsonl",
    "09-whiptail-fds.json",
    "10-tty1-state.json",
    "11-tty1-owners.json",
    "12-input-events-redacted.jsonl",
    "13-kernel-input-log-redacted.txt",
    "14-systemd-console-status.txt",
    "15-screen-comparison.json",
    "16-operator-observations.json",
    "17-hypothesis-decision.json",
    "18-final-result.json",
    "19-final-report.md",
    "20-file-manifest.json",
    "SHA256SUMS",
)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    with open(partial, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(partial, path)


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_sha256sums(run_dir: Path, files: list[str]) -> Path:
    lines: list[str] = []
    for name in files:
        p = run_dir / name
        if not p.is_file() or name == "SHA256SUMS":
            continue
        lines.append(f"{sha256_file(p)}  {name}")
    out = run_dir / "SHA256SUMS"
    atomic_write_text(out, "\n".join(lines) + ("\n" if lines else ""))
    return out


def build_manifest(run_dir: Path) -> dict[str, Any]:
    entries = []
    for p in sorted(run_dir.iterdir()):
        if not p.is_file() or p.name.endswith(".partial"):
            continue
        entries.append({"name": p.name, "size": p.stat().st_size, "sha256": sha256_file(p)})
    return {"schema_version": 1, "files": entries}


def finalize_run_dir(run_dir: Path, *, status: str, final_result: dict[str, Any]) -> dict[str, Any]:
    """Write final result last; refresh manifest + SHA256SUMS."""
    # Ensure placeholders exist for required JSON/txt so import validation is stable.
    for name in REQUIRED_FILES:
        if name in {"SHA256SUMS", "20-file-manifest.json", "18-final-result.json"}:
            continue
        p = run_dir / name
        if not p.exists():
            if name.endswith(".json") or name.endswith(".jsonl"):
                atomic_write_json(p, {} if name.endswith(".json") else [])
            elif name.endswith(".md"):
                atomic_write_text(p, f"# placeholder\nstatus={status}\n")
            else:
                atomic_write_text(p, "")

    atomic_write_json(run_dir / "18-final-result.json", final_result)
    manifest = build_manifest(run_dir)
    atomic_write_json(run_dir / "20-file-manifest.json", manifest)
    write_sha256sums(
        run_dir,
        [e["name"] for e in manifest["files"] if e["name"] != "SHA256SUMS"],
    )
    # refresh manifest with SHA256SUMS included
    manifest = build_manifest(run_dir)
    atomic_write_json(run_dir / "20-file-manifest.json", manifest)
    write_sha256sums(run_dir, [e["name"] for e in manifest["files"] if e["name"] != "SHA256SUMS"])
    return {"status": status, "run_dir": str(run_dir), "manifest_files": len(manifest["files"])}


def assert_path_under_allowed_roots(path: Path, allowed_roots: list[Path]) -> None:
    resolved = path.resolve()
    for root in allowed_roots:
        try:
            resolved.relative_to(root.resolve())
            return
        except ValueError:
            continue
    raise ValueError(f"EVIDENCE_PATH_NOT_ALLOWED:{resolved}")
