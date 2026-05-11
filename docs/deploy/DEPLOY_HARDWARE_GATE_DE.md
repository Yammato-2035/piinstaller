# Deploy Hardware Gate (DE)

## Ziel

Defensive Hardware-Gate-Schicht fuer zukuenftige Real-Write-Freigaben.

## Eigenschaften

- read-only Bewertung physischer Testmedien
- fail-closed bei unklaren Geraeten
- operator protocol als reine Checkliste
- keine Execute-/Write-Engine

## Metadaten-Vollstaendigkeit

- Ziel-Metadaten (`removable`, `transport`, `size`, `rotational`, `model`) werden aus Inspect/lsblk defensiv uebernommen.
- Bei Partition-Targets wird die Parent-Disk robust gemappt (z. B. `/dev/sdb1` -> `/dev/sdb`), inklusive Parent-Metadaten.
- Fehlende optionale Felder erzeugen Warnungen, aber bei sonst sauberem Ziel keinen automatischen Readiness-Downgrade.
