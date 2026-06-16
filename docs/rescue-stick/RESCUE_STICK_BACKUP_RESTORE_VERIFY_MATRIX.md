# Rettungsstick — Backup/Restore/Verify Matrix

**Stand:** F.1 — 2026-06-16

| Fähigkeit | Linux ext4 | NTFS Windows | BitLocker | Status F.1 |
|-----------|------------|--------------|-----------|--------------|
| read-only detect | ja | ja | eingeschränkt | **grün** |
| image backup | geplant | geplant (F.2) | nur Rohimage/Key-abhängig | **blocked** |
| file backup | ja | später | nein ohne Key | geplant |
| manifest | ja | ja | — | geplant |
| sha256 | ja | ja | — | geplant |
| verify image | ja | ja | — | F.3 blocked |
| restore image | ja | geplant (F.4) | strukturell | **blocked** |
| boot plausibility | Linux | Windows Boot Manager | — | F.1 read-only |
| login verification | n/a | nein (Passwort fehlt) | — | Policy |
| write repair | nein | nein | nein | **verboten** |
| Linux install after wipe | ja | nach Freigabe | — | **blocked** |

Evidence: `docs/evidence/msi/F1_MSI_WINDOWS_READONLY_PRECHECK_RESULT.json`
