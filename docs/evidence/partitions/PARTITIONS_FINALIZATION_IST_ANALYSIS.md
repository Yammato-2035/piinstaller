# Partitionshelfer – IST-Analyse (Finalisierung)

**Datum:** 2026-05-22
**HEAD (Analyse):** `a7e61e6`
**Runtime-Gate:** Exit 0

## API-Pfade (`/api/partitions/*`)

| Pfad | Methode | Funktion |
|------|---------|----------|
| `/scan` | GET | Disks/Partitionen lesend |
| `/safety-check` | GET | Legacy-Safety-Warnungen |
| `/queue` | GET/DELETE | Queue (Stub) |
| `/queue/apply` | POST | Stub – blockiert Writes |
| `/hardstop-preview` | GET | Hardstop + Storage-Facade |
| `/manifest-layout-preview` | POST | Inline + optional `manifest_path` read-only |
| `/restore-handoff-preview` | POST | Handoff ohne Restore-Start |

## UI

- `PartitionManager.tsx` – Scan, Auswahl, Safety-Preview, optional Manifest-Pfad
- `PartitionSafetyPreviewPanel.tsx` – Hardstop, Manifest, Handoff, Schreibschutz, nächste sichere Handlung
- `partitionApi.ts` – Phase-2-Fetcher
- i18n `partition.phase2.*` (DE/EN)

## Safety-Gates

| Gate | Ort | Wirkung |
|------|-----|---------|
| `write_allowed=false` | API + Core | überall erzwungen |
| `partition_storage_facade` | `backend/core/` | write_guard, backup_before_write, Pfadregeln |
| `partition_hardstop` | apps/core | Systemdisk, Backup-Quelle, SMART, Facade-Hardstops |
| `manifest_layout_preview` | apps/core | nur JSON-Lesen, Allowlist für Datei |
| `restore_handoff_contract` | apps/core | Verify, Hardstop, BBW – `restore_execution_allowed=false` |
| `safe_device` Allowlist | `write_safe_prefixes_resolved` | Manifest-Dateilesen |
| Queue `/apply` | routes | Phase-2-Stub, keine Ausführung |

## Ampel

| Bereich | Status | Hinweis |
|---------|--------|---------|
| Scan / Safety-Check Phase 1 | **green** | read-only produktiv |
| Hardstop-Preview + Facade | **green** | finalisiert read-only |
| Manifest inline + Datei | **green** | Allowlist-Pfad, kein tar-Extract |
| Restore-Handoff | **green** | Preview only |
| Queue Apply / Partition Writes | **blocked** | bewusst nicht freigegeben |
| Rettungsstick Live/ISO | **blocked** | nur Doku-Vorbereitung |
| Hardware-Verify Deep | **blocked** | nicht im Scope |

## Stubs

- `/queue/apply` – bestätigt, führt nichts aus
- Partitions-Wizard-Schreibaktionen – UI ohne Backend-Write

## Wiederverwendbar für Rettungsstick

- `storage_safety` / `handoff_sources` Struktur
- Manifest-Layout + Kompatibilitätswarnungen
- `required_next_gates` (Verify, BBW, Hardstop)
- `rescue_handoff_next` Hinweisstring

## Offene Lücken (review_required)

- Echter Restore auf Zielhardware
- ISO/Live-Build, debootstrap, chroot
- EFI/Bootloader-Write
- Partition-Apply nach expliziter Gate-Freigabe (zukünftige Phase)
