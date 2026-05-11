# Write-Safety – Überblick (DE)

## Warum Write-Safety existiert

Zukünftige Schreiboperationen (Restore, Image-Deploy, Partitionierung) könnten **Systemplatten** oder **Dualboot-Umgebungen** zerstören. Die Auswertung nutzt **nur** bereits gesammelte Inspect-Daten (`devices_classified`, `filesystems.detected`, `mountability`) — **ohne** neue Hardware-Erkennung und **ohne** Schreibzugriff.

## Wann blockiert wird

- Kategorie **`system_disk`** oder Mount **`/`** auf einer Partition des Geräts
- **`live_system`** (typische Live-FS)
- **NTFS** ohne Linux-FS und ohne durchgängiges **`backup_candidate`**-Muster → **`SAFETY_WINDOWS_DETECTED`**
- **NTFS + Linux-FS** auf derselben Disk → **`SAFETY_DUALBOOT`**
- Unklare Identität / Gerät nicht in der klassifizierten Liste → **`SAFETY_UNKNOWN_DEVICE`**

## Warum kein Override in Phase 1

Phase 1 liefert nur **API-Felder und UI-Anzeige**. Ein Override wäre eine **neue privilegierte Aktion** und gehört nicht zu dieser rein informativen Ausbaustufe.

Siehe: `docs/safety/WRITE_SAFETY_DE.md`.
