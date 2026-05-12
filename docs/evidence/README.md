# Evidence-Verzeichnis (Setuphelfer)

Dieses Verzeichnis sammelt **maschinenlesbare und nachvollziehbare** Testnachweise. Eine Ampel **Grün** ist nur gerechtfertigt, wenn hier (oder verlinkt) vollständige Evidence liegt: Zeitstempel, Umgebung, Version, reproduzierbare Schritte, Logs/Auszüge.

## Ordner

| Ordner | Inhalt |
|--------|--------|
| `hardware/` | Hardwareläufe (Pi, Laptop, Medien) |
| `backup-restore/` | Backup, Verify, Restore, Fehlerfälle |
| `rescue-stick/` | Read-only Rescue-/Live-Flows |
| `website/` | Transparenz-, Status-, Affiliate-Checks |
| `release-gates/` | Sammelgates, Inventare, CI-/Release-Nachweise (`current_failures.json`, **`blocker_inventory.json`** Prompt 2, **`ci_evidence.json`** — letzter GitHub-Lauf inkl. Conclusion/Run-ID, **`ci_failure_analysis_STRICT_*.md`**, `ci_deploy_runner_permission_boundary_analysis_*.md`, `post_workspace_sync_commit_hygiene_*.md`, `mode_change_inventory_*.json`, `workspace_artifact_inventory_*.json`, Pytest-Zusammenfassungen, optional `diagnostics_evidence_seed_audit_*.json` für `data/diagnostics/evidence`) |

## Schema

JSON-Dateien nutzen das Feld `schema: "setuphelfer.evidence.v1"`. Pflichtfelder für **abgenommene** Evidence:

- `executed_at` (ISO-8601)
- `environment` (OS, Arch, Gerät, Medien)
- `result` (ok / fail / blocked)
- `artifacts` (Pfade zu Logs, Screenshots, Exporten)
- `evidence_complete: true`

Templates mit `evidence_complete: false` sind **kein** Grün-Nachweis.

## Regel

> Grün gibt es nur mit Testnachweis, Doku und Evidence-Datei.

Keine Grün-Markierung allein aufgrund von Code-Review oder `py_compile`.
