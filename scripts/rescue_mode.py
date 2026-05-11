#!/usr/bin/env python3
"""
CLI für Rescue Read-only-Analyse und Restore-Dry-Run (keine UI).

- Standard: Read-only-Analyse → /tmp/setuphelfer-rescue-report.*
- Mit --restore-dryrun-backup: Restore-Simulation → /tmp/setuphelfer-rescue-dryrun.*
- Mit --restore-live: echter Restore (Token + Bestätigung erforderlich) → Log unter /tmp/setuphelfer-rescue-restore.log
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    backend = Path(__file__).resolve().parent.parent / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))

    try:
        from models.diagnosis import RescueRestoreRequest, RestoreDryRunRequest
        from modules.rescue_readonly_analyze import REPORT_JSON, run_rescue_readonly_analysis
        from modules.rescue_restore_dryrun import DRYRUN_REPORT_JSON, run_restore_dryrun_pipeline
        from modules.rescue_restore_execute import RESTORE_LOG_PATH, run_rescue_restore
    except ModuleNotFoundError as exc:
        print(
            "Rescue-CLI benötigt die Backend-Python-Umgebung (z. B. venv mit pydantic/fastapi).",
            file=sys.stderr,
        )
        print(f"Importfehler: {exc}", file=sys.stderr)
        return 2

    p = argparse.ArgumentParser(description="Setuphelfer Rescue (Analyse / Restore-Dry-Run)")
    p.add_argument(
        "--root",
        default="/",
        help="Nur Analyse: Wurzelpfad für Boot-/fstab-Prüfungen (Standard: /)",
    )
    p.add_argument(
        "--json-stdout",
        action="store_true",
        help="Vollständige JSON-Antwort auf stdout",
    )
    p.add_argument(
        "--restore-dryrun-backup",
        metavar="PATH",
        default=None,
        help="Absoluter Pfad zu .tar.gz (unter erlaubten Wurzeln) für Restore-Dry-Run",
    )
    p.add_argument(
        "--target-device",
        default=None,
        help="Optionales Whole-Disk-Blockgerät für Kapazitäts-/Layout-Vergleich",
    )
    p.add_argument(
        "--mode",
        choices=("analyze_only", "dryrun"),
        default="dryrun",
        help="Restore-Dry-Run-Modus",
    )
    p.add_argument(
        "--encryption-key-available",
        action="store_true",
        help="Nur Flag: Nutzer gibt an, einen Entschlüsselungsschlüssel zu haben (kein Secret)",
    )
    p.add_argument(
        "--restore-live",
        action="store_true",
        help="Echten Restore ausführen (benötigt Token und Zielverzeichnis)",
    )
    p.add_argument(
        "--restore-target-dir",
        metavar="PATH",
        default=None,
        help="Zielverzeichnis unter erlaubtem Live-Restore-Präfix (leer)",
    )
    p.add_argument(
        "--dry-run-token",
        default=None,
        help="Token aus erfolgreichem Dry-Run (dry_run_token)",
    )
    p.add_argument(
        "--session-id",
        default=None,
        help="session_id aus Dry-Run-JSON (Session-Bindung, Pflicht für --restore-live)",
    )
    p.add_argument(
        "--phrase",
        default=None,
        help="Bestätigung: basename(target_device) oder RESTORE_NO_BLOCK_DEVICE",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="Explizite Bestätigung (confirmation=true)",
    )
    p.add_argument(
        "--risk-ack",
        action="store_true",
        help="Risiko explizit akzeptiert (für YELLOW)",
    )
    p.add_argument(
        "--perform-boot-repair",
        action="store_true",
        help="Bootloader/initramfs-Schritte auf dem Ziel (benötigt target-device)",
    )
    args = p.parse_args()

    if args.restore_live:
        if not (
            args.restore_dryrun_backup
            and args.restore_target_dir
            and args.dry_run_token
            and args.phrase
            and args.yes
            and args.session_id
        ):
            print(
                "Für --restore-live benötigt: --restore-dryrun-backup, --restore-target-dir, "
                "--dry-run-token, --session-id, --phrase, --yes",
                file=sys.stderr,
            )
            return 2
        rreq = RescueRestoreRequest(
            session_id=args.session_id,
            backup_id=args.restore_dryrun_backup,
            restore_target_directory=args.restore_target_dir,
            target_device=args.target_device,
            dry_run_token=args.dry_run_token,
            confirmation=True,
            risk_acknowledged=bool(args.risk_ack),
            target_confirmation_text=args.phrase,
            perform_boot_repair=bool(args.perform_boot_repair),
        )
        rres = run_rescue_restore(rreq)
        payload = json.loads(rres.model_dump_json())
        if args.json_stdout:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"status={rres.status} result={rres.result} bootable={rres.bootable}")
            for w in rres.warnings:
                print(f"  warn: {w}")
            for c in rres.codes:
                print(f"  code: {c}")
            print(f"Log: {RESTORE_LOG_PATH}")
        return 0 if rres.status == "ok" else 1

    if args.restore_dryrun_backup:
        req = RestoreDryRunRequest(
            backup_file=args.restore_dryrun_backup,
            target_device=args.target_device,
            mode=args.mode,
            encryption_key_available=bool(args.encryption_key_available),
        )
        result = run_restore_dryrun_pipeline(req)
        payload = json.loads(result.model_dump_json())
        if args.json_stdout:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(
                f"status={result.status} session_id={result.session_id} "
                f"restore_risk_level={result.restore_risk_level} "
                f"restore_decision={result.restore_decision} findings={len(result.findings)}"
            )
            for f in result.findings:
                print(f"  [{f.risk_level}] {f.code}")
            print(f"Bericht: {DRYRUN_REPORT_JSON}")
        return 0 if result.status == "ok" else 1

    result = run_rescue_readonly_analysis(root=args.root, write_reports=True)
    payload = json.loads(result.model_dump_json())

    if args.json_stdout:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"status={result.status} risk_level={result.risk_level} findings={len(result.findings)}")
        for f in result.findings:
            print(f"  [{f.risk_level}] {f.code} area={f.area}")
        print(f"Bericht: {REPORT_JSON}")

    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
