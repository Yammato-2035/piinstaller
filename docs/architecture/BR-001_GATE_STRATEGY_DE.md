# BR-001 Gate-Strategie — Live vs. Offline (Rettungsstick)

**Stand:** 2026-05-20  
**Entscheidung:** Live-Desktop-BR-001 ist kein Release-Gate mehr. Release-Gate für Desktop Privat ist **BR-001-OFFLINE** über den Setuphelfer-Rettungsstick.

## Warum Live-BR-001 nicht weiterverfolgt wird

Live-Full-Root auf einem laufenden Desktop scheitert reproduzierbar an Umgebungs-Randbedingungen, die kein stabiles Release-Gate sind:

| Kategorie | Befund (Evidence) |
|-----------|-----------------|
| **apt / autoremove** | Job `e341a326ac69`: `backup.blocked_package_activity`, `apt-get autoremove --purge` während Lauf — `BR-001_package_activity_failure_2026-05-13.md` |
| **Timeshift** | Live-Snapshots unter `/timeshift`: `Datei hat sich beim Lesen geändert`, `tar_failed` — `BR-001-full-root-stable-pigz-retry-2026-05-20.json` |
| **Chrome-Profil** | `~/.config/google-chrome` geändert während Lesen — `BR-001-full-root-stable-pigz-timeshift-retry-2026-05-20.json` (Timeshift ausgeschlossen, Abbruch dennoch) |
| **Live-Dateien allgemein** | Browser-Caches, Paketmanager, Hintergrunddienste → `TAR_CRITICAL_WARNING` / `tar` Exit 1 |
| **Ziel-I/O** | Schreib-EIO auf USB (`f744c2936468`), große `.partial` ohne finales Archiv — `BR-001_write_io_error_2026-05-14.md` |
| **tar Exit 1** | Mehrere Jobs (~142–212 GiB partial), kein SHA256, kein Verify Deep — u. a. `c597e6f59e1f` 2026-05-20 |

**Konsequenz:** Weitere Live-Desktop-Retries sind **experimentell** (Entwicklung/Monitoring), nicht Bestandteil des Release-Gates. Kein „noch ein Retry“ als Ampel-Hebel.

## Neue BR-001-Definition

| ID | Kontext | Rolle | Grün wenn |
|----|---------|-------|-----------|
| **BR-001-LIVE** | Desktop Privat, System läuft | **Experimentell** — `system-stable`, inkrementell, UI-Hinweise | Optional; **nicht** Release-blockierend |
| **BR-001-OFFLINE** | Rettungsstick, Quellplatte **still** | **Release-Gate** Desktop Privat | Full-Backup offline: externes Ziel, pigz, finales Archiv, SHA256, Manifest, Verify Deep, Restore Preview (read-only) |

Verkettung Release: **BR-001-OFFLINE** → BR-004 → BR-005 (dieselbe Archivdatei).

## Architektur nach Zieltyp

| Zieltyp | Backup-Modus | Release-Gate |
|---------|--------------|--------------|
| **Desktop Privat** | Rettungsstick / offline-full | **BR-001-OFFLINE** |
| **Desktop Privat (live)** | system-stable, Profile, inkrementell | Kein Full-Root-Gate |
| **Cloudserver** | Snapshot + inkrementell | Eigene Matrix (nicht BR-001-LIVE) |

## Offline-BR-001 — Module (Soll)

| Modul | Repo-Stand | MVP |
|-------|------------|-----|
| Bootmedium-Build (`build/rescue`, live-build) | Skripte vorhanden, ISO **dry-run** / Config **fehlend** | Ja |
| Hardware-/Storage-Erkennung | Inspect, Device Classification, Rescue Discovery | Ja |
| Read-only Mount Quellplatte | Orchestrator + Handoff-Pipelines (Unit-Tests) | Ja |
| Zielprüfung extern | Backup-Target-Policies, Write-Guard | Ja |
| Offline Backup pigz | `backup_runner` / Archive-Options (Host); Stick-Runtime Assembly **teilweise** | Ja |
| SHA256 + Manifest | Runner vorhanden; offline E2E **offen** | Ja |
| Verify Deep | Engine vorhanden; RS-007 Evidence **rot** | Ja |
| Restore Preview | `rescue_restore_dryrun`, preview_only | Ja |
| Anfänger-Partitionierungsassistent | **Nicht** implementiert — siehe unten | Nein (Restore auf Ersatzplatte) |
| Malware/Virenscan vor Restore | **Nicht** implementiert — optional, kein Backup-Blocker | Nein |

Inventar: `docs/evidence/runtime-results/handoff/rescue_stick_component_inventory.json` (Generator: `runner_rescue_stick_component_inventory.py`).

## Partitionierungsassistent — ja, später

**Empfehlung:** Für **neue SSD/HDD/NVMe** und **Restore auf Ersatzplatte** wird ein geführter Partitionierungsassistent **benötigt** (nicht für reines Backup auf externes Medium).

Anforderungen:

- Erkennung vorhandener Partitionen/Dateisysteme
- **Warnung** bei vorhandenen Daten
- Explizite Bestätigung + Hinweis auf **Datensicherung vor Überschreiben**
- Kein stiller `mkfs`/`parted`-Lauf ohne Operator-Freigabe (align mit `DEPLOY_WRITE_RUNNER_CONTRACT`)

Bis zur Implementierung: Restore auf Ersatzplatte nur über dokumentiertes Runbook / Expertenmodus.

## Malware / Virenscan

| Phase | Rolle |
|-------|--------|
| **Backup** | **Kein** Blocker; kein Gate-Grün abhängig von Scan |
| **Restore (optional)** | Operator kann Scan **vor** Restore anbieten (ClamAV o. ä.) — UI-Warnung: „Scan nicht durchgeführt“ / „Fund — Restore abbrechen“ |
| **Release** | BR-001-OFFLINE **ohne** Scan; separater optionaler RS-/Restore-Hinweis |

## Verweise

- Rettungsstick: `docs/rescue/SETUPHELFER_RESCUE_STICK_ARCHITECTURE_DE.md`
- Matrix: `docs/testing/BACKUP_RESTORE_TEST_MATRIX.md`, `docs/testing/RESCUE_STICK_TEST_MATRIX.md`
- Evidence-Pivot: `docs/evidence/release-gates/BR-001_offline_gate_pivot_2026-05-20.md`
- Development Cockpit: `br001_gates` in `/api/dev-dashboard/status`
