# Inspect Phase 2 – Klassifikationslogik, CIAO, Risiken (DE/EN)

## DE: Klassifikationslogik (kurz)

Die Funktion `classify_system` in `backend/inspect/classifier.py` wertet **nur** Felder aus dem Phase-0/1-Payload aus:

1. **BROKEN_BOOT** zuerst: `capabilities.os_hints.possible_broken_boot` oder Boot-Codes aus `boot.codes` (Kernel/initrd/fstab/…).
2. **EMPTY**: `possible_empty_disk` oder Datenträger ohne Partitionen und ohne erkannte FS-Metadaten.
3. **DUALBOOT**: Im Map `filesystems.detected` gleichzeitig **NTFS** und ein **Linux-FS** (ext2/3/4, xfs, btrfs). Confidence wird **defensiv** gesenkt bei widersprüchlichen Layout-Hinweisen oder wenn `possible_dualboot` nicht zur Kombination passt.
4. **LINUX**: Linux-FS im erkannten Satz, **kein** NTFS dort.
5. **WINDOWS**: **Nur**, wenn neben **NTFS** ein **Zusatzsignal** in derselben `detected`-Map steht: **vfat/fat32** (EFI-ähnlich) **oder** **mindestens zwei** NTFS-Einträge. **Alleiniges NTFS** ohne diese Signale → **`PARTIAL_SYSTEM`** (`classifier.indicator.ntfs_only_ambiguous`), **nicht** WINDOWS — NTFS allein ist **kein** sicherer Windows-Nachweis.
6. **PARTIAL_SYSTEM**: z. B. Fragmente, widersprüchliche Hinweise, oder NTFS ohne klares Muster.
7. **UNKNOWN**: Fallback.

Kein Scan nach `Microsoft`-Dateien; die Phase-0/1-Payload liefert dafür **keine** Pfade. Keine neuen Hardware-Scans.

## EN: Classification logic (short)

`classify_system` (`backend/inspect/classifier.py`) consumes **only** the phase 0/1 payload:

1. **BROKEN_BOOT** first.
2. **EMPTY**.
3. **DUALBOOT** if **NTFS** and a **Linux FS** appear in `filesystems.detected` — confidence is **conservative** when hints disagree.
4. **LINUX** when Linux FS present without NTFS.
5. **WINDOWS** **only** if **NTFS** plus **vfat/fat32** in the same map **or** **two or more NTFS** partitions are listed. **NTFS-only** → **`PARTIAL_SYSTEM`**, not WINDOWS — **NTFS alone is not proof of Windows**.
6. **PARTIAL_SYSTEM** / **UNKNOWN**.

No Microsoft-folder probing; not provided by phase 0/1 data.

## CIAO-Prinzip

| Buchstabe | Bedeutung | Inspect-Phase |
|-----------|-----------|---------------|
| C | Collect | 0/1 (Rohdaten) |
| I | Interpret | 2 (`classification`) |
| A | Advise | 2 (`advice`, nur Codes, **keine Aktion**) |
| O | Operate | **nicht** Teil von Inspect |

**Empfehlungen (`advice`)** lösen **keine** Reparatur, kein Restore, kein Deploy aus — nur strukturierte Codes für menschliche/nachgelagerte Prozesse.

## Risiken falscher Interpretation

- **NTFS-Datenpartition** → mit neuer Regel **PARTIAL_SYSTEM**, nicht automatisch WINDOWS.
- **Rescue-/Live-Umgebung** sieht nicht zwangsläufig die Zielplatte.
- **vfat** kann Linux-ESP sein; Kombination **vfat + NTFS** ist nur ein **Heuristik-Hinweis**, kein Beweis.

Siehe auch: `docs/inspect/INSPECT_PHASE_2_DE.md`, FAQ `docs/faq/BACKUP_RESTORE_FAQ_DE.md` (Phase 2).
