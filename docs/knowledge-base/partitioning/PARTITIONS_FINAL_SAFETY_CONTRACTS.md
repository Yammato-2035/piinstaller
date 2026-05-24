# Partitionshelfer – Finale Safety Contracts (read-only)

## Grundsatz

Der Partitionshelfer liefert bis zur Rettungsstick-/Restore-Freigabe **nur Vorschau**: Hardstop, Manifest-Layout, Restore-Handoff. **Kein** automatisches `allowed` für Schreiben.

## Storage-Facade

`build_partition_target_safety_context()` bündelt:

- `safety.write_guard.evaluate_write_target` (bei Inspect-Daten)
- `evaluate_backup_before_write_requirement`
- Pfadregeln: `/`, `/boot`, `/tmp`, `/media/…` nicht pauschal freigegeben
- `operator_override` erzeugt **niemals** Partition-Write-Freigabe

## Manifest

- `manifest=null` → `unavailable`
- `manifest_path` → nur `MANIFEST.json` unter `write_safe_prefixes_resolved()`
- Kein tar-Extract, kein Restore-Start

## Restore-Handoff

- `restore_execution_allowed=false` immer
- Block bei Hardstop `blocked`, fehlendem Verify, BBW nicht satisfied
- `handoff_sources` für späteren Rettungsstick-Flow

## FAQ-Kurzantworten

**Warum schreibt der Partitionshelfer noch nicht?**
Phase-2/Finale-Vorschau: alle Gates müssen vor echtem Apply durch Rettungsstick/Operator passieren.

**Warum Manifest-Preview?**
Restore-Kompatibilität (Layout, Boot/EFI) ohne Ziel zu mounten oder zu beschreiben.

**Warum kein Restore im Handoff?**
Handoff ist Übergabe-Datenmodell; Ausführung nur nach Verify + Rescue-Gates.

**Warum Rettungsstick danach?**
Live-OS und isolierte Writes sind eigene Pipeline – Partitions-Safety liefert read-only Entscheidungsdaten.
