> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/legal/BETA_AND_HARDWARE_TEST_BOUNDARY_DE.md`). Bitte bei Release manuell gegenlesen.

# Beta- und Hardware-Test-Grenzen

**Stand:** 2026-06-16

## Beta-Hinweis

Setuphelfer befindet sich in internaler Betatestphase (`release_stage: internalal_testing`). Hardware-E2E (MSI, Raspberry Pi) erfordert Operator-Freigabe und vollständige Evidence.

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
