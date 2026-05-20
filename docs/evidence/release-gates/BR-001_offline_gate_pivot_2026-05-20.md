# BR-001 — Pivot Live → Offline Release-Gate (2026-05-20)

**STRICT:** Kein Backup-, Restore- oder Verify-Deep-Start in diesem Dokument. Nur Bewertung und Gate-Umstellung.

## Live-BR-001 — zusammengefasste Fehlerklassen

1. **apt/autoremove** — `e341a326ac69`, `UPDATE-CONFLICT-041`, `BR-001_package_activity_failure_2026-05-13.md`
2. **Timeshift** — live snapshots, `tar_failed` trotz Exclude-Versuch — `BR-001-full-root-stable-pigz-retry-2026-05-20.json`
3. **Chrome-Profil** — `~/.config/google-chrome` — `BR-001-full-root-stable-pigz-timeshift-retry-2026-05-20.json`
4. **Live-Dateien** — `TAR_CRITICAL_WARNING`, allgemeine volatile Pfade — `docs/knowledge-base/backup/BR001_TAR_LIVE_CACHE_FAILURES.md`
5. **tar Exit 1** — Job `c597e6f59e1f`, ~142 GiB partial, kein finales Archiv/SHA256/Verify Deep
6. **Ziel-I/O / Partial** — `f744c2936468`, Deploy/Partial-Blocker — `backup_pipeline_deploy_failure_mail_partial_cleanup_2026-05-20.json`

## Entscheidung

| Gate | Status | Release |
|------|--------|---------|
| BR-001-LIVE (Desktop, System läuft) | **rot / experimentell** | **Nein** — keine weiteren Live-Retries als Gate |
| BR-001-OFFLINE (Rettungsstick) | **rot** (noch nicht grün) | **Ja** — einziges Desktop-Full-Backup-Release-Gate |

## Rettungsstick IST (Code/Doku, keine HW-Abnahme)

| Baustein | Stand |
|----------|--------|
| `build/rescue` + `scripts/rescue/build-rescue-iso-controlled.sh` | Workspace-Layout; ISO nur mit `SETUPHELFER_RESCUE_BUILD_APPROVED=1`; Config oft fehlend |
| Storage discovery | `rescue_backup_discovery`, Deploy-Runner-Pipelines |
| Read-only mount | `runner_rescue_readonly_mount_orchestrator`, Handoff `readonly_mount_result.json` |
| Backup runner (Host) | `backup_runner.py`, pigz — offline Stick-Runtime Assembly **teilweise** |
| Verify deep | Engine + Tests; RS-007 Evidence **rot** |
| Restore preview | `rescue_restore_dryrun`, preview_only |
| Evidence | Collector/API; RS-001–RS-008 **rot** |

## Offene MVP-Module (Offline-BR-001)

Bootmedium-Build, materialisierte Live-Config, ISO-Testpipeline, Offline-UI im Live-System, E2E auf echter Hardware mit stillstehender Quellplatte.

## Partitionierung / Malware

- **Partitionierungsassistent:** empfohlen für Ersatzplatte/neue Medien; **nicht** Teil von BR-001-OFFLINE Backup-Gate.
- **Malware-Scan:** optional vor Restore; **kein** Backup-Blocker; klare UI-Warnung wenn ausstehend.

## Maschinenlesbar

`docs/evidence/runtime-results/BR-001-offline-gate-pivot-2026-05-20.json`

## Nächste Schritte (Roadmap)

1. RS-001 Boot + RS-002 Backend auf Stick-HW  
2. Read-only Mount interne Platte (RS-005)  
3. Offline Full-Backup auf externes Ziel → SHA256 → Verify Deep → Evidence RS-006/007  
4. BR-004/BR-005 an Offline-Archiv koppeln  
