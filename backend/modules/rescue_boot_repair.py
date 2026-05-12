"""
Phase 3E / 3.N7: Boot-Reparatur auf dem Ziel-Root — modulare Schritte, kein pauschales „fix all“.

Alle destruktiven Schritte respektieren ``dry_run``: nur protokollieren, keine Aufrufe.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable, Literal

from modules.inspect_boot import analyze_boot_status
from modules.restore_engine import install_bootloader

Runner = Callable[..., subprocess.CompletedProcess[str]] | None

BootContext = Literal[
    "x86_uefi",
    "x86_bios_legacy",
    "raspberry_pi_firmware_boot",
    "unknown",
]


def _run(
    argv: list[str],
    *,
    runner: Runner = None,
    timeout: int = 600,
) -> subprocess.CompletedProcess[str]:
    run = runner or subprocess.run
    return run(argv, capture_output=True, text=True, timeout=timeout, check=False)


def detect_boot_context(target_root: str | Path) -> BootContext:
    """Heuristik nur auf dem extrahierten Zielbaum (nicht Host-/)."""
    tr = Path(target_root)
    if (tr / "boot" / "firmware" / "config.txt").is_file():
        return "raspberry_pi_firmware_boot"
    if (tr / "boot" / "efi" / "EFI").is_dir():
        return "x86_uefi"
    if (tr / "boot" / "grub").exists():
        return "x86_bios_legacy"
    return "unknown"


def validate_boot_configuration(target_root: str | Path, *, runner: Runner = None) -> dict[str, Any]:
    """Read-only Boot-Konfiguration unter ``target_root``."""
    st = analyze_boot_status(target_root, runner=runner)
    codes: list[str] = []
    for c in st.get("codes") or []:
        codes.append(c)
    fw = Path(target_root) / "boot" / "firmware" / "config.txt"
    cmd = Path(target_root) / "boot" / "firmware" / "cmdline.txt"
    if fw.is_file():
        codes.append("rescue.boot_repair.firmware_config_present")
    if cmd.is_file():
        codes.append("rescue.boot_repair.firmware_cmdline_present")
    return {"boot_status": st, "codes": codes}


def validate_boot_artifacts(target_root: str | Path, *, runner: Runner = None) -> dict[str, Any]:
    """Alias mit klarer Semantik (3.N7): Artefakte lesend prüfen."""
    return validate_boot_configuration(target_root, runner=runner)


def choose_boot_repair_strategy(boot_context: BootContext) -> tuple[list[str], list[str]]:
    """
    Liefert geplante Teil-Schritte und ggf. Blocker-Codes.

    ``unknown`` → keine automatische Reparatur (kein blindes GRUB/chroot).
    """
    if boot_context == "unknown":
        return [], ["rescue.boot.context_unknown", "rescue.boot.repair_not_supported"]
    if boot_context == "raspberry_pi_firmware_boot":
        return ["initramfs_optional"], []
    return ["bootloader", "initramfs"], []


def prepare_chroot_environment(chroot: str | Path, *, dry_run: bool = True, runner: Runner = None) -> dict[str, Any]:
    """
    Bind-Mounts für klassisches chroot (nur auf Ziel-Root).

    Ohne Root-Rechte schlägt dies typischerweise fehl — dann ``code`` gesetzt.
    """
    root = Path(chroot)
    out: dict[str, Any] = {"codes": [], "dry_run": dry_run}
    binds = [("/dev", root / "dev"), ("/proc", root / "proc"), ("/sys", root / "sys")]
    if dry_run:
        out["codes"].append("rescue.boot_repair.chroot_bind_skipped_dry_run")
        return out
    for src, dst in binds:
        dst.mkdir(parents=True, exist_ok=True)
        r = _run(["mount", "--bind", src, str(dst)], runner=runner, timeout=60)
        if r.returncode != 0:
            out["codes"].append("rescue.boot_repair.chroot_bind_failed")
            out["bind_failed"] = str(dst)
            return out
    out["codes"].append("rescue.boot_repair.chroot_bind_ok")
    return out


def reinstall_bootloader(
    target_block_device: str | Path,
    boot_directory: str | Path | None,
    *,
    dry_run: bool = True,
    runner: Runner = None,
) -> dict[str, Any]:
    """Wrapper um ``install_bootloader`` (GRUB auf Zielplatte)."""
    ok, key, err = install_bootloader(target_block_device, boot_directory=boot_directory, dry_run=dry_run, runner=runner)
    return {"ok": ok, "message_key": key, "detail_type": type(err).__name__ if err else None}


def regenerate_initramfs(chroot: str | Path, *, dry_run: bool = True, runner: Runner = None) -> dict[str, Any]:
    """``update-initramfs`` im chroot (falls ``chroot``-Binary vorhanden)."""
    if dry_run:
        return {"ok": True, "code": "rescue.boot_repair.initramfs_skipped_dry_run"}
    which = _run(["which", "chroot"], runner=runner, timeout=10)
    if which.returncode != 0:
        return {"ok": False, "code": "rescue.boot_repair.chroot_binary_missing"}
    r = _run(["chroot", str(chroot), "update-initramfs", "-c", "-k", "all"], runner=runner, timeout=3600)
    if r.returncode != 0:
        return {"ok": False, "code": "rescue.boot_repair.initramfs_failed"}
    return {"ok": True, "code": "rescue.boot_repair.initramfs_ok"}


def execute_boot_repair_if_allowed(
    target_root: Path,
    target_block_device: str | Path | None,
    boot_context: BootContext,
    *,
    dry_run: bool,
    runner: Runner = None,
) -> dict[str, Any]:
    """Führt nur erlaubte Schritte für den erkannten Kontext aus."""
    steps, blockers = choose_boot_repair_strategy(boot_context)
    out: dict[str, Any] = {"boot_context": boot_context, "steps": steps, "blockers": blockers, "bootloader": {}, "initramfs": {}}
    if blockers:
        return out
    ch = prepare_chroot_environment(target_root, dry_run=dry_run, runner=runner)
    out["chroot"] = ch
    if "bootloader" in steps and target_block_device:
        boot_dir = target_root / "boot"
        out["bootloader"] = reinstall_bootloader(
            target_block_device,
            boot_dir if boot_dir.is_dir() else None,
            dry_run=dry_run,
            runner=runner,
        )
    if "initramfs" in steps or "initramfs_optional" in steps:
        out["initramfs"] = regenerate_initramfs(target_root, dry_run=dry_run, runner=runner)
    return out


def validate_boot_repair_result(repair_out: dict[str, Any]) -> list[str]:
    """Leitet Findings aus Ausführungsergebnis ab (kein verschleierter Erfolg)."""
    codes: list[str] = []
    bl = repair_out.get("bootloader") or {}
    if bl and bl.get("ok") is False:
        codes.append("rescue.boot.repair_failed")
    init = repair_out.get("initramfs") or {}
    if init.get("ok") is False:
        codes.append("rescue.boot.repair_failed")
    if repair_out.get("blockers"):
        codes.extend(str(x) for x in repair_out["blockers"])
    val = repair_out.get("validated") or {}
    for c in (val.get("codes") or []):
        if c in ("rescue.boot.kernel_missing", "rescue.boot.initrd_missing", "rescue.boot.boot_dir_missing"):
            codes.append("rescue.boot.validation_uncertain")
    return sorted(set(codes))


def run_boot_repair_pipeline(
    target_root: str | Path,
    target_block_device: str | Path | None,
    *,
    perform_boot_repair: bool,
    dry_run: bool = False,
    runner: Runner = None,
) -> dict[str, Any]:
    """
    Orchestrierung 3.N7: detect → validate → choose → execute → validate result.
    """
    root = Path(target_root)
    stages: list[dict[str, Any]] = []
    ctx = detect_boot_context(root)
    stages.append({"name": "detect_boot_context", "context": ctx})
    val = validate_boot_artifacts(root, runner=runner)
    stages.append({"name": "validate_boot_artifacts", "codes": val.get("codes")})
    if not perform_boot_repair:
        return {
            "stages": stages,
            "validated": val,
            "performed": False,
            "codes": ["rescue.boot_repair.skipped_by_request"],
            "boot_context": ctx,
        }
    strat, blk = choose_boot_repair_strategy(ctx)
    stages.append({"name": "choose_boot_repair_strategy", "strategies": strat, "blockers": blk})
    if blk:
        return {
            "stages": stages,
            "validated": val,
            "performed": False,
            "codes": list(blk),
            "boot_context": ctx,
        }
    exec_out = execute_boot_repair_if_allowed(
        root,
        target_block_device,
        ctx,
        dry_run=dry_run,
        runner=runner,
    )
    exec_out["validated"] = val
    stages.append({"name": "execute_boot_repair_if_allowed", "summary_keys": list(exec_out.keys())})
    r_codes = validate_boot_repair_result({**exec_out, "validated": val})
    stages.append({"name": "validate_boot_repair_result", "codes": r_codes})
    all_codes = list(val.get("codes") or [])
    all_codes.extend(r_codes)
    return {
        "stages": stages,
        "validated": val,
        "execution": exec_out,
        "performed": True,
        "codes": sorted(set(all_codes)),
        "boot_context": ctx,
    }


__all__ = [
    "BootContext",
    "choose_boot_repair_strategy",
    "detect_boot_context",
    "execute_boot_repair_if_allowed",
    "prepare_chroot_environment",
    "regenerate_initramfs",
    "reinstall_bootloader",
    "run_boot_repair_pipeline",
    "validate_boot_artifacts",
    "validate_boot_configuration",
    "validate_boot_repair_result",
]
