# Partitionshelfer – Professional UI Rework Analyse

**Datum:** 2026-06-10  
**HEAD (Start):** `6b543e4`  
**Version (Start):** `1.7.12.3`  
**Branch:** `main`

## Phase-0 Status

| Prüfung | Ergebnis |
|---------|----------|
| `check-runtime-profile-deploy-gate.sh` | Nicht grün (uncommitted Backend-Drift + Profil-Gate offen) |
| `check-runtime-deploy-gate.sh` | Legacy-Hinweis → Profil-Gate verwenden |
| Uncommitted Änderungen | Rescue, Profile-Gate, DCC-Evidence (außerhalb dieses Auftrags) |

## Ist-vs-Ziel

| Bereich | Aktuell (vor Rework) | Ziel | Problem | Maßnahme |
|---------|----------------------|------|---------|----------|
| Branding/Logo | PageHeader ohne Logo | Setuphelfer-Logo oben links | Kein Werkzeug-Branding | `PartitionToolShell` |
| Seitenlayout | Website-artig, Panda-Strip | Diagnose-Cockpit | Zu verspielt | Tool-Shell, dunkle Fläche |
| Tool-Header | Generischer PageHeader | Titel + Read-only-Badge + Version | Keine Werkzeugidentität | Tool-Chrome |
| Datenträgerkarten | Rollen nur Frontend-Heuristik | Backend-Klassifikation + Icons | Windows-NVMe falsch | `storage_role_classification` + Karten |
| Partitionsgrafik | Dominant | Kurz auf Seite 1 | OK aus 2.3 | Beibehalten, Details collapsible |
| Sicherheitsstatus | Mini-Karten | Dominant rechts | OK | Beibehalten |
| Hardstops | Hero-Block | Windows/Linux/Rescue Codes | Nur system_disk | Erweiterte Codes + i18n |
| Restore-Handoff | Volle Breite unten | Unverändert read-only | OK | Beibehalten |
| Laufwerkssymbole | Rollen-Icons generisch | NVMe/USB/HDD/Windows/Linux | Zu wenig Info | `deviceIconUtils.ts` |
| Windows-Erkennung | NTFS-Hinweis ohne Rolle | `windows_system_disk` | EFI+NTFS offline ignoriert | Backend-Engine |
| Rettungsstick | Name-Heuristik | `rescue_stick` + Evidence | Nicht wiederverwendbar | Core-Modul + Arch-Doku |

## Referenz

- Mockup-Alignment: `docs/evidence/ui/PARTITION_MANAGER_MOCKUP_ALIGNMENT.md`
- Architektur Rescue: `docs/architecture/STORAGE_ROLE_CLASSIFICATION_FOR_RESCUE.md`

## Constraints eingehalten

- Kein Partition-Write, kein Restore Execute, kein Queue Apply
- Safety-Gates nicht abgeschwächt
- Keine Klassifikation nur über Gerätenamen
