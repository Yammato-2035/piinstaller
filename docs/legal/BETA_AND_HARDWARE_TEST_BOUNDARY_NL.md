> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/legal/BETA_AND_HARDWARE_TEST_BOUNDARY_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/legal/BETA_AND_HARDWARE_TEST_BOUNDARY_DE.md`). Bitte bei Release manuell gegenlesen.

# Beta- und Hardware-Test-Grenzen

**Stand:** 2026-06-16

## Beta-Hinweis

Setuphelfer befindet sich in Interner Betatestphase (`release_stage: Internal_testing`). Hardware-E2E (MSI, Raspberry Pi) erfordert Operator-Freigabe und vollständige Evidence.

## Hardware-Test-Grenzen

| Aktion | MSI-Lauf (Plan) | MSI Precheck (nächster Prompt) |
|--------|-----------------|--------------------------------|
| alleen-lezen Scan | Geplant | Erlaubt |
| Terugup/Herstel | **Verboten** | **Verboten** |
| Partitieierung | **Verboten** | **Verboten** |
| Wipe | **Verboten** | **Verboten** |

## Safety-Gates

- Keine Safety-Gates schwächen
- Keine Fake-groen-Zustände
- `geblokkeerd` und `review_requirood` ehrlich melden

## Evidence-Pflicht

Jeder Hardware-Lauf erzeugt Evidence unter `docs/evidence/msi/` oder Runtime-Evidence-Pfade — ohne personenbezogene Secrets.
