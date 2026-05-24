# Partitionshelfer – Browser-UI-Smoke (Finalisierung)

**Datum:** 2026-05-24  
**Workspace HEAD:** `ffd2d8a`  
**URL:** `http://127.0.0.1:3001/?page=partitions`  
**UI-Bundle (Runtime):** `index-DE0P57Wp.js`

## Runtime-Gate (Phase 0)

| Prüfung | Ergebnis |
|---------|----------|
| `git rev-parse --short HEAD` | `ffd2d8a` |
| `./scripts/check-runtime-deploy-gate.sh` | **Exit 0** |
| `setuphelfer-backend.service` | **active** |
| `setuphelfer.service` | **active** |

## Automatisierter Browser-Smoke (Playwright, headless)

**Vorbereitung (nur Test-Harness, kein Produktiv-Change):**

- `localStorage.setItem('pi-installer-first-run-done', '1')` – First-Run-Wizard übersprungen
- Sudo-Dialog per Schließen-Button (X) geschlossen, falls sichtbar
- Partition **nvme0n1p2** in der Liste angeklickt

**Screenshot:** `/tmp/partitions_ui_smoke.png` (lokal, nicht im Repo)

### Prüfliste

| # | Kriterium | Ergebnis |
|---|-----------|----------|
| 1 | Seite lädt ohne sichtbaren Fehler | **OK** (HTTP 200) |
| 2 | Disk-/Partitionsliste sichtbar | **OK** (sda, nvme0n1, nvme1n1) |
| 3 | Partition ausgewählt | **OK** (nvme0n1p2) |
| 4 | Panel „Sicherheitsvorschau“ | **OK** |
| 5 | Hardstop-Bereich | **OK** („Hardstops“, „Keine blockierenden Hardstops“) |
| 6 | storage_safety / Status | **OK** („Storage-Facade“, Risiko gelb, Schreibzugriff blockiert) |
| 7 | Manifest-Bereich | **OK** („MANIFEST-LAYOUT-VORSCHAU“) |
| 8 | Manifest-Pfad-Feld | **OK** („Manifest-Pfad (read-only)“ + Hint Allowlist) |
| 9 | Leeres Manifest | **OK** („Kein Manifest geladen – optional Pfad …“) |
| 10 | Restore-Handoff | **OK** („RESTORE-HANDOFF“, Restore-Ausführung blockiert) |
| 11 | Nächste sichere Handlung | **OK** |
| 12 | Schreibschutz-Banner | **OK** („Schreiboperationen bleiben deaktiviert“) |
| 13 | Keine aktiven Format-/Löschen-/Apply-Buttons | **OK** (kein enabled danger button im Smoke) |
| 14 | „Bald verfügbar“ nur disabled | **OK** (nicht im sichtbaren Detail nach Klick; Detail-Actions code-seitig disabled) |
| 15 | Queue/apply nicht ausgelöst | **OK** (kein Queue-Inhalt, kein Apply-Klick) |

### UI-Gesamtstatus

**green**

**Hinweis manueller Browser:** Beim ersten Besuch können **Systemcheck**- und **Sudo**-Overlays die Partitionsseite überdecken. Für manuelle Abnahme: First-Run abschließen oder `pi-installer-first-run-done` setzen, Sudo-Dialog schließen, dann Partition wählen.

## Phase 2 – API-Inspect-Smoke (read-only)

```bash
curl -s "http://127.0.0.1:8000/api/partitions/hardstop-preview?target_device=/dev/sda1&use_inspect=true" \
  | jq '.storage_safety.status, .evaluation.status, .write_allowed, .storage_safety.decision_source'
```

**Ergebnis:**

| Feld | Wert |
|------|------|
| `storage_safety.status` | `blocked` |
| `evaluation.status` | `blocked` |
| `write_allowed` | `false` |
| `decision_source` | `core_storage_facade` |

Keine Schreibfreigabe.

## Nicht ausgeführt

Partition-Write, Queue-Apply, Format, mount, Backup/Restore, ISO-Build, Feature-Fixes.
