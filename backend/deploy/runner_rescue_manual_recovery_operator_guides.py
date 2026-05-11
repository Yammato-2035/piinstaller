from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, resolve_handoff_path, write_json_handoff

_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_manual_recovery_operator_guides.json"
_MAX_BYTES = 768 * 1024


def _emit(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_manual_recovery_operator_guides_status": status,
        "rescue_manual_recovery_operator_guides_file_path": _OUT_REL,
        "rescue_manual_recovery_operator_guides": body,
        "rescue_manual_recovery_operator_guides_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_manual_recovery_operator_guides(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_MRG")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_MRG_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_MRG")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    guides: list[dict[str, Any]] = [
        {
            "topic": "efi_check",
            "title": "EFI prüfen (nur Lesen)",
            "steps": [
                "Storage-Discovery und EFI-Boot-Analyse ausführen",
                "Handoff `rescue_efi_boot_analysis.json` prüfen",
                "Keine `grub-install` / `efibootmgr`-Writes ohne separates Gate",
            ],
        },
        {
            "topic": "backup_check",
            "title": "Backup prüfen",
            "steps": [
                "Backup-Discovery/Verify nur mit `build/rescue/…`-Lab oder freigegebenem Mount",
                "Manifest und SHA256-Einträge manuell gegen Prüfsummen loggen",
            ],
        },
        {
            "topic": "restore_preview",
            "title": "Restore-Preview interpretieren",
            "steps": [
                "`rescue_restore_preview_result.json` lesen: betroffene Pfade nur als Vorschau",
                "Keine Ausführung: `writes_executed` muss false bleiben",
            ],
        },
        {
            "topic": "target_validation",
            "title": "Recovery-Ziel validieren",
            "steps": [
                "Plan mit `proposed_recovery_target` setzen",
                "Execute nur mit explizitem Flag; Systempfade bleiben blockiert",
            ],
        },
        {
            "topic": "evidence_export",
            "title": "Evidence exportieren",
            "steps": [
                "Explizites Export-Ziel (Allowlist) wählen",
                "Kein Export auf aktive Systempartitionen",
            ],
        },
        {
            "topic": "remote_help",
            "title": "Remote Help vorbereiten",
            "steps": [
                "Plan/Result lesen; SSH nicht automatisch starten",
                "Zugangsdaten manuell rotieren",
            ],
        },
    ]

    body: dict[str, Any] = {
        "rescue_manual_recovery_operator_guides_schema_version": 1,
        "strict_mode": "rescue_manual_guides_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "guides": guides,
        "no_auto_repair": True,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit("ok", body, wrote=True, warnings=[], errors=[])
