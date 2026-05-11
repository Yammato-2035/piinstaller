# Setuphelfer Hardware-Testmatrix

## Legende

| Status | Bedeutung |
|--------|-----------|
| Grün | bestanden, Evidence vorhanden |
| Gelb | teilweise bestanden / Review nötig |
| Rot | offen / fehlgeschlagen |
| Schwarz | geparkt |

## Matrix

| ID | Gerät | CPU/Arch | Quelle | Ziel | Testart | Risiko | Status | Evidence | Bemerkung |
|----|-------|----------|--------|------|---------|--------|--------|----------|-----------|
| HW-001 | Raspberry Pi 5 | ARM64 | SD 32 GB | USB-SSD | Full Backup | mittel | Rot | docs/evidence/hardware/HW-001.json | offen |
| HW-002 | Raspberry Pi 5 | ARM64 | NVMe 500 GB | USB-SSD 1 TB | Full Backup | mittel | Rot | docs/evidence/hardware/HW-002.json | offen |
| HW-003 | Raspberry Pi 5 | ARM64 | SD 32 GB | NVMe 500 GB | Restore | hoch | Rot | docs/evidence/hardware/HW-003.json | nur freigegebenes Testmedium |
| HW-004 | Raspberry Pi 5 | ARM64 | NVMe 500 GB | NVMe 500 GB | Restore-Vergleich | hoch | Rot | docs/evidence/hardware/HW-004.json | nur Testkonfiguration |
| HW-005 | Laptop UEFI | x86_64 | interne NVMe | externe SSD | Backup + Verify | mittel | Rot | docs/evidence/hardware/HW-005.json | Ziel explizit extern |
| HW-006 | Laptop UEFI | x86_64 | externe SSD | interne Test-SSD | Restore | hoch | Rot | docs/evidence/hardware/HW-006.json | nur dedizierte Test-SSD |
| HW-007 | Laptop Dualboot | x86_64 | Windows-NVMe | kein Ziel | Safety: kein Write | kritisch | Rot | docs/evidence/hardware/HW-007.json | darf nicht schreiben |
| HW-008 | USB-Stick | x86_64/ARM64 | Rescue Boot | kein Ziel | Boot + Inspect read-only | hoch | Rot | docs/evidence/hardware/HW-008.json | read-only |
| HW-009 | externe SSD | — | Backupziel | n/a | Mount-/Permission-Test | mittel | Rot | docs/evidence/hardware/HW-009.json | offen |
| HW-010 | SD-Karte | — | Backupquelle | USB-Ziel | Langsamer Datenträger | mittel | Rot | docs/evidence/hardware/HW-010.json | I/O-/Timeout-Risiko |

## Zusatz (Referenz aus kompakter Matrix)

| ID | Gerät | Kurztest | Status | Evidence |
|----|-------|----------|--------|----------|
| HW-REF-006 | Rescue USB | Boot + Inspect read-only | Rot | docs/evidence/hardware/HW-008.json (gemeinsamer Rescue-Pfad) |

*Hinweis:* HW-REF-006 verweist logisch auf den Rescue-Stick-Flow; Evidence primär unter `docs/evidence/rescue-stick/`.
