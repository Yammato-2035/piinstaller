# Inspect Phase 2 (DE) – Klassifikation & Empfehlung (CIAO: Interpret + Advise)

## Ziel

Aufbauend auf Phase 0/1 liefert Phase 2 **Interpretation** und **strukturierte Empfehlungscodes** – weiterhin **ohne Schreiboperationen**, ohne Reparatur, ohne Restore, ohne Deploy.

## API

`GET /api/inspect/run` enthält **zusätzlich** (bestehende Felder unverändert):

- `classification`: `system_type`, `confidence`, `indicators` (Codes), `risk_level`
- `advice`: `recommended_paths[]` mit `code`, `priority`, `requires_confirmation`

## Systemtypen (`system_type`)

| Wert | Kurzbedeutung |
|------|----------------|
| `EMPTY` | Keine verwertbaren Partitionen / leerer Datenträger-Hinweis |
| `WINDOWS` | Nur, wenn neben **NTFS** in `filesystems.detected` ein **Zusatzsignal** steht: **vfat/fat32** (typ. EFI) und/oder **mindestens zwei NTFS-Partitionen**. Reines **NTFS ohne** solches Muster → **`PARTIAL_SYSTEM`** (kein sicherer Windows-Nachweis). |
| `LINUX` | Linux-typische FS (ext2/3/4, xfs, btrfs), kein NTFS im erkannten Satz |
| `DUALBOOT` | NTFS und Linux-FS **gleichzeitig** im erkannten `filesystems.detected` (Confidence abgesenkt, wenn Layout-Hinweise widersprüchlich sind) |
| `BROKEN_BOOT` | Bootanalyse meldet kritische Codes (Kernel/initrd/fstab/…) |
| `PARTIAL_SYSTEM` | Widersprüchliche oder unvollständige Signale |
| `UNKNOWN` | Defensiver Fallback |

## CIAO-Prinzip (Phase 2)

- **C**ollect: Phase 0/1 (unverändert).
- **I**nterpret: `backend/inspect/classifier.py` – nur aus vorhandenen JSON-Rohdaten.
- **A**dvise: `backend/inspect/advisor.py` – nur Codes und Prioritäten, **keine** Ausführung.
- **O**perate: bewusst **nicht** Teil von Inspect.

## Web-UI (Hinweis)

Die Seite **Inspect** zeigt `indicators` als **technische Codes** (kein Freitext-Backend). Es gibt **keine** Schaltflächen, die Repair/Restore/Deploy auslösen. `advice` ist rein informativ.

## Runtime-Abnahme (Repo)

Wenn `127.0.0.1:8000` von der installierten Dienst-Instanz (`/opt/setuphelfer`) belegt ist, das **Repo-Backend** z. B. so starten und prüfen:

`PI_INSTALLER_BACKEND_PORT=8010 PI_INSTALLER_SKIP_SERVICE_CONFLICT_GUARD=1 ./scripts/start-backend.sh`

`curl -sS http://127.0.0.1:8010/api/inspect/run` muss `classification` und `advice` enthalten. Aktualisierung von `/opt`: bestehendes `scripts/deploy-to-opt.sh` (kein neues Skript).

## Risiken

Klassifikation kann **falsch** sein (z. B. **NTFS-Datenpartition** wird nicht mehr pauschal als `WINDOWS` gewertet; **Zusatzsignale** aus der Map nötig). Rescue-System sieht ggf. nicht die Zielplatte. Im Zweifel **`UNKNOWN`**, **`PARTIAL_SYSTEM`** oder niedrigeres `confidence`.

## Implementierung

- `backend/inspect/classifier.py` – `classify_system`
- `backend/inspect/advisor.py` – `generate_advice`
- Einbindung in `backend/inspect/collector.py` nach Aufbau der Rohdaten
