> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/legal/BETA_AND_HARDWARE_TEST_BOUNDARY_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/legal/BETA_AND_HARDWARE_TEST_BOUNDARY_DE.md`). Bitte bei Release manuell gegenlesen.

# Beta- und Hardware-Test-Grenzen

**Stand:** 2026-06-16

## Beta-Hinweis

Setuphelfer befindet sich in Interneer Betatestphase (`release_stage: Interneal_testing`). Hardware-E2E (MSI, Raspberry Pi) erfordert Operator-Freigabe und vollständige Evidence.

## Hardware-Test-Grenzen

| Aktion | MSI-Lauf (Plan) | MSI Precheck (nächster Prompt) |
|--------|-----------------|--------------------------------|
| lecture seule Scan | Geplant | Erlaubt |
| Retourup/Restauration | **Verboten** | **Verboten** |
| Partitionierung | **Verboten** | **Verboten** |
| Wipe | **Verboten** | **Verboten** |

## Safety-Gates

- Keine Safety-Gates schwächen
- Keine Fake-vert-Zustände
- `bloqué` und `review_requirouge` ehrlich melden

## Evidence-Pflicht

Jeder Hardware-Lauf erzeugt Evidence unter `docs/evidence/msi/` oder Runtime-Evidence-Pfade — ohne personenbezogene Secrets.
