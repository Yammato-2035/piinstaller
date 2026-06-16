# Partitionshelfer Phase 2 – Wissensbasis

Kurzreferenz für Support und Entwicklung.

## UI-Komponenten (Phase 2.1)

| Komponente | Zweck |
|------------|-------|
| `PartitionOverviewCards` | Datenträgerkarten (System / Backup / Rescue) |
| `PartitionGraphicLayout` | Farbige Partitionsleiste |
| `PartitionSafetyStatusPanel` | Dauerhafter Sicherheitsstatus rechts |
| `PartitionHardstopPanel` | Hardstop-Warnungen mit Erklärung |
| `PartitionRestorePreviewPanel` | Restore-Handoff-Vorschau |

## Expertenmodus

- **Einsteiger:** nur Funktion und Größe pro Partition
- **Experte:** UUID, Mountpoint, Parttyp, Gerätepfad

## Sicherheitsprinzip

Alle Preview-APIs liefern `write_allowed: false`. Die UI zeigt das explizit an. Queue/Apply und Restore-Execute sind **nicht** angebunden.

## i18n-Bereiche

- `partitionManager.*` – Seite und Karten
- `partitionSafety.*` – Statuspanel
- `hardstops.*` – Hardstop-Erklärungen
- `restorePreview.*` – Restore-Handoff
- `partitionManager.layoutPreview.*` – Grafische Ansicht

## Verweise

- [PARTITION_MANAGER_PHASE2_UI_DE.md](../../partitions/PARTITION_MANAGER_PHASE2_UI_DE.md)
- [PARTITIONS_PHASE2_SAFETY_CONTRACTS.md](../../evidence/partitions/PARTITIONS_PHASE2_SAFETY_CONTRACTS.md) (Evidence)
