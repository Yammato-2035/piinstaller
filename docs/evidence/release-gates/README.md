# Release-Gates Evidence

JSON-Dateien unter diesem Verzeichnis speisen das Development Cockpit (`tests_evidence`, Release-Gates).

## Ampel-Logik (ehrlich)

| Datei | Typische Ampel | Bedeutung |
|-------|----------------|-----------|
| `current_failures.json` | grün | pytest/CI ohne Failures |
| `test_inventory.json` | gelb | Tests ok, Release wegen BR-001 blockiert |
| `release_readiness_gate.json` | rot | Release blockiert (BR-001) |
| `backup_restore_release_gate.json` | rot | Backup/Restore-Release blockiert |
| `backend_version_update_gate.json` | gelb | Version/Runtime-Gate ok, APT-Kanal offen |
| `apt_update_delivery_gap.json` | rot | Kein produktives APT-Update |

**Runtime-Deploy-Gate grün** (`check-runtime-deploy-gate.sh`) schließt **BR-001 nicht** automatisch.

## Aggregat `tests_evidence` (API)

- **gelb**: nur Release-Gates rot, pytest/Inventory konsistent
- **rot**: pytest rot oder strukturell unvollständige Evidence
- Einzeldateien `release_*` / `backup_restore_*` bleiben **rot**, bis BR-001 echte Evidence hat

## Kein Fake-Grün

BR-001, Restore, Hardware und CI dürfen nicht kosmetisch auf grün gesetzt werden.
