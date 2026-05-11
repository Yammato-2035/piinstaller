# Setuphelfer Branding Guard (Policy)

Ziel: Nach der Migration dürfen keine **neuen aktiven** Legacy-Marken mehr in Runtime-Code, Konfiguration, ENV, Services oder Packaging landen. Dieses Dokument ist die Referenz für den automatisierten Guard und für manuelle Reviews.

## Aktiv verboten (Produktivkontext)

- `pi-installer`
- `piinstaller`
- `pi-installer-frontend`
- `PI_INSTALLER_*` (Präfix für Umgebungsvariablen und ähnliche Bezeichner)
- `de.pi-installer.app`
- `/opt/pi-installer`
- `pi-installer.service`

## Aktiv erlaubt (Runtime-Marke Setuphelfer)

- `setuphelfer`, `Setuphelfer`
- `SETUPHELFER_*`
- `de.setuphelfer.app`
- `/opt/setuphelfer`
- `setuphelfer.service`

## Erlaubte Legacy-Kontexte (nur Lesen / Historie / Vertrag)

Treffer der verbotenen Zeichenketten sind **kein** Branding-Verstoß, wenn sie ausschließlich in diesen Bereichen vorkommen:

- `docs/evidence/`
- `docs/history/`
- `changelog/` (inkl. History-Pfade)
- Migrationsdokumentation unter `docs/migration/`
- `compatibility_aliases.json` (Kompatibilitätsvertrag)
- Explizite Legacy-/Branding-Policies, z. B. dieses Dokument
- Ausgewählte Deploy-/KB-Dokumente, die Migration oder Zero-State explizit beschreiben (siehe Runner-Whitelist für Dateinamen)

## Guard-Artefakte

- Python-Runner: `backend/deploy/runner_setuphelfer_branding_guard.py` (nur Analyse + Evidence-JSON)
- Optional lokales Skript: `scripts/check-setuphelfer-branding-guard.sh` (nur Suche, keine Änderungen, kein automatischer Git-Hook)

Kein Rewrite, keine Runtime-Ausführung der Anwendung, keine Service-Manipulation, kein Release/Tag/Publish.
