# F.1 Monolith Slice Result

**Datum:** 2026-06-16

## app.py

| Metrik | Vorher | Nachher |
|--------|--------|---------|
| Zeilen | ~8829 | ~8831 (+2 Router-Registrierung) |
| Neue `@app.* /api/msi` | 0 | **0** |

## Neue Module (nicht Monolith)

- `backend/core/windows_ntfs_detection_contract.py`
- `backend/core/msi_windows_handlers.py`
- `backend/api/routes/msi_windows.py`

## Wiederverwendung

- `storage_role_classification` für Disk-Rollen
- Keine zweite BitLocker/NTFS-Heuristik in `app.py`

## Nächste Monolith-Slices (unverändert)

users, sudo-password, raspberry-pi config, webserver, NAS, radio, dev-dashboard
