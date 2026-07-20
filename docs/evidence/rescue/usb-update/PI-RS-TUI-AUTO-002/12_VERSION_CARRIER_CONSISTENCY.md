# 12 – Version Carrier Consistency

## Aktiv / verbindlich

| Carrier | Wert | OK |
|---------|------|----|
| Squash `VERSION` | 1.10.0.59 | ja |
| Squash `rescue_payload_version.json` | 1.10.0.59 | ja |
| Squash `version.json` | 1.10.0.59 | ja |
| ESP `version.json` project_version | 1.10.0.59 | ja |
| ESP `version.json` rescue_payload_version | 1.10.0.59 | ja |
| ESP `version.json` payload_sha256 | `3706b824a8992b8abf8d9e20a6d1daa47503cb7c3fada9ac5189e38c2b9ef43e` | ja |
| ESP evidence project_version | 1.10.0.59 | ja |

## Residuale Legacy-Felder (nicht boot-kritisch)

| Feld | Beobachtung |
|------|-------------|
| ESP `filesystem_squashfs_sha256` | alter Merge-Wert `38c14ed4…` (nicht neuer Squash) |
| ESP evidence `payload_sha256` (ältere Keys) | Merge-Residuum; verbindlich ist Updater-`payload_sha256`/`project_version` |
| `live/filesystem.squashfs.sha256` Sidecar | historisch (Inject-Staging-Sidecar nicht vom FAT32-Updater ersetzt) |

**Bewertung:** Aktive Release-Carrier = **1.10.0.59** und Squash-Hash Match. Kein aktiver Carrier zeigt `1.10.0.58`. Legacy-Hash-Nebenfelder dokumentiert.
