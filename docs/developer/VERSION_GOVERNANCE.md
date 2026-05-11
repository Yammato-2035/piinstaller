# Version Governance (STRICT Mode)

## SemVer-Regeln

### PATCH
- reine Bugfixes
- Doku/FAQ/KB/i18n
- kleine Sicherheitsfixes
- keine neuen Pipelines

### MINOR
- neue STRICT-MODE-Module
- neue Evidence-Ketten
- neue API-Routen
- neue Safety-Gates
- neue Test-Matrizen

### MAJOR
- Architekturwechsel
- neue Plattform
- neue Runtime-/Deploy-Engine
- Raspberry-Pi-Produktionsfreigabe
- Rescue-Stick-Produktionsreife

## Pflicht pro abgeschlossener STRICT-Phase
- Version erhöhen (mind. PATCH, i.d.R. MINOR bei neuer Kette)
- Evidence-Artefakte zuordnen
- Teststatus dokumentieren
- Release-Level dokumentieren (z. B. `internal_testing`)
