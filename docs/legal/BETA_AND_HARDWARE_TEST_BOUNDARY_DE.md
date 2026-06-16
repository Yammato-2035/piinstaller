# Beta- und Hardware-Test-Grenzen

**Stand:** 2026-06-16

## Beta-Hinweis

Setuphelfer befindet sich in interner Betatestphase (`release_stage: internal_testing`). Hardware-E2E (MSI, Raspberry Pi) erfordert Operator-Freigabe und vollständige Evidence.

## Hardware-Test-Grenzen

| Aktion | MSI-Lauf (Plan) | MSI Precheck (nächster Prompt) |
|--------|-----------------|--------------------------------|
| Read-only Scan | Geplant | Erlaubt |
| Backup/Restore | **Verboten** | **Verboten** |
| Partitionierung | **Verboten** | **Verboten** |
| Wipe | **Verboten** | **Verboten** |

## Safety-Gates

- Keine Safety-Gates schwächen
- Keine Fake-Green-Zustände
- `blocked` und `review_required` ehrlich melden

## Evidence-Pflicht

Jeder Hardware-Lauf erzeugt Evidence unter `docs/evidence/msi/` oder Runtime-Evidence-Pfade — ohne personenbezogene Secrets.
