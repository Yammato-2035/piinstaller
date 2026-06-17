# RS-F2S Initial Status

**Stand:** 2026-06-17  
**Branch:** `main`  
**HEAD:** `00bb2a4` (vor RS-F2S-Arbeit)

| Feld | Wert |
|------|------|
| Workspace-Version | 1.9.3.0 (nach RS-F2S-Code) |
| Runtime-Version | 1.9.2.0 → deploy auf 1.9.3.0 ausstehend |
| Runtime-Gate | grün (release-Profil, dev-dashboard 404 erwartet) |
| Backend-Version-Gate | grün nach Deploy 1.9.2.0 |
| Public/Private-Gate | grün (Exit 0) |
| Module-Boundary-Gate | review_required (Exit 0, Warnungen) |
| Dirty Tree | ja (RS-F2S-Arbeit, untracked Evidence) |

## Schreibmodus

| Aktion | Erlaubt |
|--------|---------|
| ISO build / verify | ja (read-only verify + ggf. controlled rebuild) |
| USB write | nur nach Operator-Bestätigung + gültigem Ziel |
| MSI backup | **nein** |
| Restore | **nein** |
| Externe Backup-HDD formatieren | **nein** |
| Interne Datenträger beschreiben | **nein** |

## Architektur-Hinweis

Development-Laptop = Build/Stick-Schreiber/Verifier. MSI-Backup nur vom gebooteten Rettungsstick.
