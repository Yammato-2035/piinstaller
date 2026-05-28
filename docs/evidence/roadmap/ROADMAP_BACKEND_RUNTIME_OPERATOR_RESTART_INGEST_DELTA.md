# Roadmap Delta — Backend Runtime Operator Restart Ingest

Datum: 2026-05-28

## Eingangsquellen

- Operator-Output (Ground-Truth): Journal-Fehler zum fehlenden `piinstaller.debug.jsonl`-Pfad, Service `active`, MainPID `138932`, `/api/version` success (`1.7.2`, `/opt/setuphelfer/backend`).
- Agent-Rerun: `./scripts/check-runtime-deploy-gate.sh` aus Repo-CWD mit Exit 11 (`/api/version HTTP 000000`).

## Entscheidung

- Next Prompt: `BACKEND_RUNTIME_RECOVERY_GATE`
- Rescue-Pfad bleibt bedingt: Nur bei nachgewiesenem Gate Exit 0 wieder `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE`.

## Zweck

- Konsistente Dokumentation trotz divergenter Messpunkte (Operator vs. Agent-Rerun).
