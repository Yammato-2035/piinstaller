# Partitionshelfer – Phase 2.1 Safety Preview UI

**Stand:** 2026-06-10  
**Phase:** 2.1 (read-only)  
**Zielgruppe:** Einsteiger und Experten im Setuphelfer-Frontend

## Überblick

Der Partitionshelfer wurde auf das Setuphelfer-Design umgestellt: dunkles Theme, Kartenlayout, Ampellogik und große Lesbarkeit. Phase 2.1 ist eine **reine Sicherheits- und Vorschau-Phase** – keine Schreiboperationen.

## Datenträgerkarten

Statt technischer Tabellen zeigt die Startansicht **Datenträgerkarten**:

| Rolle | Beispiel |
|-------|----------|
| Systemlaufwerk | Interne SSD mit `/` und EFI |
| Backup-Ziel | Externe Platte unter `/media/…` |
| Rettungsstick | Setuphelfer Rescue (read-only) |

Jede Karte zeigt Name, Größe, Status-Badge und einen **Details**-Button.

## Grafische Partitionsansicht

Nach Auswahl eines Datenträgers erscheint eine **Balkenansicht** mit Farbcodierung:

- EFI → grün
- Linux Root → blau
- Home → violett
- Swap → grau

Pro Partition: Name, Dateisystem, Größe, Belegung. Im **Expertenmodus** zusätzlich UUID, Mountpoint, Typ.

## Sicherheitsstatus (rechts, dauerhaft)

Das Panel `PartitionSafetyStatusPanel` bleibt sichtbar und zeigt:

- SMART
- Bootfähigkeit
- Systemlaufwerk erkannt
- Backup gefunden
- Hardstops
- `write_allowed` (immer **false**)
- Restore-Handoff

Ampel: grün / gelb / rot.

## Hardstops

Bei blockierenden Codes erscheint ein großer Warnblock mit Titel, Erklärung, Risiko und Handlungsempfehlung – ohne nackte Rohcodes.

Beispiele: `target_is_system_disk`, `partition_target_is_backup_source`, `target_identity_unknown`, `smart_failing`.

## Restore-Handoff

Das Panel zeigt den Handoff-Status (bereit / Review / blockiert), geplante Aktionen aus dem Manifest-Layout und **`restore_execution_allowed=false`** deutlich sichtbar.

## API (read-only)

| Methode | Pfad |
|---------|------|
| GET | `/api/partitions/scan` |
| GET | `/api/partitions/hardstop-preview` |
| POST | `/api/partitions/manifest-layout-preview` |
| POST | `/api/partitions/restore-handoff-preview` |

**Nicht** verwendet: `/api/partitions/queue/apply` und andere Schreib-Endpunkte.

## Development Dashboard

Kachel **PARTITIONS** mit Checks: Geräte, SMART, Hardstops, Layout Preview, Restore Handoff.

## Grenzen Phase 2

- Kein Partition-Write, kein mkfs/parted/sgdisk/wipefs/dd
- Kein Resize, Formatieren, Löschen
- Kein Restore-Execute, kein Queue-Apply
- `write_allowed` und `restore_execution_allowed` bleiben **false**

## Phase 3 (offen)

- Kontrollierte Schreiboperationen nach Gate-Freigabe
- Queue-Apply nur mit Token und Rescue-Kontext
- HW-Abnahme mit echtem Zielmedium

## Evidence

Siehe `docs/evidence/partitions/PARTITIONS_PHASE2_UI_PREVIEW_STUB.md`.
