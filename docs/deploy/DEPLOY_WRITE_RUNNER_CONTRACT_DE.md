# Deploy Write Runner — Contract (Phase Dry-Run)

## Zweck

Trennung von **unprivilegiertem Backend** und einem **optional privilegierten, One-Shot-Runner**, der später echte Blockdevice-Writes ausführen kann. **Diese Phase:** nur **Job-Contract**, **Validierung** und **Dry-Run-CLI** — **kein** Öffnen von Devices, **kein** Schreiben.

## Warum nicht das gesamte Backend als root?

Große Angriffsfläche (Netzwerk, Sessions, Dateipfade). Nur ein minimaler Runner soll erhöhte Rechte erhalten — und nur für einen klar begrenzten Job.

## Warum separater Runner?

Rechte minimal halten: Backend erzeugt und signiert Jobs; Runner liest **lokal** genau **eine** Jobdatei, validiert, führt später (nicht in dieser Phase) den Write aus.

## Warum Jobfile?

Reproduzierbarer, auditierbarer Input; keine Shell-RPCs, keine freien Kommandos im JSON.

## Warum Hash-Bindung?

`job_hash` (SHA256 über kanonisches JSON **ohne** `job_hash`) bindet alle Felder inkl. Ziel, Image-Metadaten und Guard-Metadaten — Manipulation fällt auf.

## Warum noch kein echter Write?

Explizite Phasen: erst Contract + Dry-Run + Tests; dann Betrieb mit sudoers/Pfadbeschränkung.

## Module / Werkzeuge

- `backend/deploy/real_write_runner_contract.py` — `build_real_write_job`, `validate_real_write_job`, `compute_job_hash`
- `backend/tools/deploy_write_runner.py` — CLI `--job` und `--dry-run`

### CLI

```bash
python3 backend/tools/deploy_write_runner.py --job /pfad/job.json --dry-run
```

Ausgabe: eine JSON-Zeile auf stdout mit `DEPLOY_RUNNER_DRY_RUN_OK` oder `DEPLOY_RUNNER_DRY_RUN_BLOCKED` (inkl. Lifecycle-Felder: `runner_state`, `lock_id`, `audit_entries_written`; siehe `DEPLOY_RUNNER_LIFECYCLE_DE.md`).

## Jobdatei-Pfad (`--job`)

Erlaubt nur unter:

- `/var/lib/setuphelfer/deploy-jobs/` (Ziel für späteren Betrieb)
- `backend/cache/deploy` (modulstabil, für Entwicklung/CI)

Der vom Operator übergebene Pfad wird mit `expanduser` + `resolve` normalisiert und muss mit `relative_to` unter einer dieser Wurzeln liegen. **Symlinks auf der Jobdatei** (direkt auf `--job`) werden **abgelehnt** (fail-closed). Directory-Traversal (`../`) endet nach Auflösung ggf. außerhalb des Präfixes und wird blockiert.

## Image-Pfade

Erlaubt: wie `inspect_deploy_image` (konfigurierte Cache-Präfixe) **plus** festes Backend-Deploy-Cache-Verzeichnis `backend/cache/deploy` (aufgelöst relativ zum Modul), damit Jobs vom Backend und vom Runner mit unterschiedlichem CWD konsistent validieren.

## Validierungscodes

- `DEPLOY_RUNNER_JOB_VALID`
- `DEPLOY_RUNNER_JOB_INVALID`
- `DEPLOY_RUNNER_JOB_EXPIRED`
- `DEPLOY_RUNNER_JOB_HASH_MISMATCH`
- `DEPLOY_RUNNER_JOB_IMAGE_INVALID`
- `DEPLOY_RUNNER_JOB_TARGET_INVALID`

## Replay (optional, Tests / gehärteter Betrieb)

Umgebungsvariable `DEPLOY_RUNNER_REPLAY_GUARD=1`: nach **erfolgreicher** Job-Validierung merkt sich der Prozess `(job_id, job_hash)`; ein zweiter Dry-run mit denselben Werten im **selben** Prozess liefert `DEPLOY_RUNNER_JOB_REPLAY_DUPLICATE`. Über Prozessgrenzen hinweg ist das nicht wirksam ohne persistenten Ledger oder Token.

## Runtime-Nachweise

Siehe `docs/evidence/DEPLOY_WRITE_RUNNER_RUNTIME_VALIDATION.md` (Systemanalyse, Isolation, sudoers-Risiken, Testkommandos).

## Späteres Betriebmodell (Dokumentation)

- sudoers nur für dieses eine Runner-Skript; **keine** Wildcards in Argumenten, `env_keep`/`LD_PRELOAD`/`PYTHONPATH` eindämmen (Details in Evidence-Dokument)
- `--job` nur unter z. B. `/var/lib/setuphelfer/deploy-jobs/` (zusätzlich zum Runner-internen Check)
- kein `shell=True`, kein `dd`/Partitionierungs-Tools im Runner

## Grenzen (diese Phase)

- Keine Root-Prüfung, kein Device-Open, kein Byte-Write.
