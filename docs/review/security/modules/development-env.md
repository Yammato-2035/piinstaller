# Security Review: DevelopmentEnv

## Kurzbeschreibung

Dev-Umgebung: Paket-/Tool-Installation (apt, pip, npm). Nur für experienceLevel === 'developer' sichtbar (developerOnly). API: /api/devenv/status, ggf. configure.

## Angriffsfläche

Eingaben: Paket-/Tool-Wünsche. Kritische Aktionen: apt, pip, npm mit sudo.

## Schwachstellen

Paketnamen müssen validiert werden (Whitelist oder striktes Format); keine beliebigen Befehle.

## Ampelstatus

**GRÜN** (eingeschränkte Sichtbarkeit, Entwickler-Kontext). Betroffene Dateien: backend/modules/devenv.py, app.py, frontend/src/pages/DevelopmentEnv.tsx.
