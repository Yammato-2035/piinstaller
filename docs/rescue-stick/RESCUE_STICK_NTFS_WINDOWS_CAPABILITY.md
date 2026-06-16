# Rettungsstick — NTFS/Windows Capability

**Stand:** F.1 — 2026-06-16  
**Contract:** `backend/core/windows_ntfs_detection_contract.py`

## NTFS/Windows Support Scope (Stufe 1)

Unterstützt:

- Windows/EFI/NTFS **read-only** erkennen
- BitLocker-**Indikatoren** erkennen (kein Bypass)
- Image-Backup **vorbereiten** (F.2 gated)
- Manifest/SHA256/Verify **vorbereiten**
- Restore-Test **strukturell** bewerten
- Bootstruktur plausibilisieren (Windows Boot Manager)
- Windows-Login **nicht** erforderlich wenn Passwort fehlt

Nicht unterstützt:

- Passwort zurücksetzen, BitLocker umgehen
- NTFS reparieren, chkdsk, ntfsfix
- Registry/SAM, automatische Windows-Reparatur
- Datenentschlüsselung ohne Recovery-Key
- NTFS-Schreiben ohne gesonderte Freigabe

## Rescue-ISO Pakete (geplant)

- `ntfs-3g` read-only Mount nur mit expliziter Operator-Freigabe in späteren Phasen
- `partclone`, `dd` status-only in Observability — Execute gated

## API (read-only)

- `GET /api/msi/windows/capabilities`
- `POST /api/msi/windows/precheck/parse-readonly`

Keine Execute-Endpunkte im Public Repo.
