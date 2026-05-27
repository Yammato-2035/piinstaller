# Low-Effort Green Candidates (Developer Dashboard)

**Stand:** 2026-05-27 · **Gate:** Exit 0 · **Quelle:** Live-API + Workspace-Analyse

„Nach grün bringen“ = Zustand **erfüllt** + Evidence + Gate — **nicht** nur Ampelfarbe.

| Bereich | Aktuell | Fehlender Nachweis | Aufwand | Risiko | Jetzt umsetzbar? | Empfehlung |
|---------|---------|-------------------|---------|--------|------------------|------------|
| runtime_gate | green | — | low | low | ja | OK-Badge / Ready-Sektion (Darstellung) |
| deploy_drift | green | — | low | low | ja | Evidence-Link, Hervorhebung |
| documentation | yellow | Roadmap-FAQ/KB | low | low | ja | Doku ergänzen, Ampel unverändert |
| i18n | yellow | neue Keys | low | low | ja | de/en sync (erledigt) |
| roadmap | partial | Cockpit-UI + ggf. FE-Deploy | low | low | ja (Code) | RoadmapDrawer im Cockpit |
| diagnostics | yellow | Teststrecke/HW | medium | medium | nein | Fortschritt zeigen |
| rescue_iso | yellow | ISO/Boot/Deps | high | forbidden_now | nein | Operator-Build-Prompt |
| backup | red | BR-001-OFFLINE HW | high | forbidden_now | nein | Kein Fake-Green |
| restore | red | HW-Restore | high | forbidden_now | nein | deferred |
| packaging | red | Install-Test | high | forbidden_now | nein | readiness only |
| release_readiness | red | CI/Legal | high | forbidden_now | nein | rot belassen |
| verify | red | BR-004/005 | high | forbidden_now | nein | blocked |
| hardware | red | HW-Matrix | high | forbidden_now | nein | rot belassen |

## Ausdrücklich nicht grün setzen

Backup, Restore, Rescue-ISO-Artefakt, Packaging-Install, Release-Gate, Hardware — ohne belastbare Evidence.
