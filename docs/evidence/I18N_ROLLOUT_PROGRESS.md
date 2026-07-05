# i18n Rollout — Fortschritt

**Stand:** 2026-07-05  
**Projektversion:** 1.9.19.0  
**Zweck:** Sprachumschalter, aktive Sprache, schrittweise Übersetzungen (DE/EN/FR/NL)

## Phase 1 — UI-Sprachumschalter (abgeschlossen)

| Artefakt | Status |
|----------|--------|
| `AppLanguageSwitcher` (DE/EN/FR/NL) | ✅ |
| Aktive Sprache sichtbar (Header, Einstellungen, DCC) | ✅ |
| `setAppLocale` + `localStorage` für FR/NL | ✅ |
| `dccVis001.fr.json` / `dccVis001.nl.json` vollständig (130 Keys) | ✅ |
| FR/NL Fallback auf EN für Haupt-UI (~3400 Keys) | ✅ bewusst |

**Nachweis:** `frontend/src/components/AppLanguageSwitcher.tsx`, Vitest `AppLanguageSwitcher.test.ts`

## Phase 2 — Dokumentations-Scanner (abgeschlossen)

| Änderung | Wirkung |
|----------|---------|
| Scanner erkennt `*.de.md` / `*.en.md` / `*.fr.md` / `*.nl.md` | DCC-FAQ/KB zählen in Paaren |
| `kb_total` inkl. `docs/kb/` | KB-Zähler im DCC korrekt |

**Nachweis:** `backend/core/dev_control_center_summary.py`, pytest `test_dot_lang_translation_pairs`

## Phase 3 — Docs-Übersetzungen (gestartet)

| Batch | Dateien | Status |
|-------|---------|--------|
| Blueprints EN | `BLUEPRINT_*_EN.md`, `LINUX_DEVELOPMENT_WORKSTATION_BLUEPRINT_EN.md` | ✅ 3 Paare neu |
| DCC FAQ/KB | `DCC_VIS_001_*.{de,en,fr,nl}.md` | ✅ bereits vorhanden |
| Architecture DE fehlend | ~40+ Stubs in `docs/architecture/` | 🔴 offen |
| Haupt-UI `fr.json` / `nl.json` | ~3400 Keys | 🔴 später |

## Metriken (Workspace, nach Scanner-Fix)

Zähler via `build_documentation_stats` — nach Deploy/Refresh im DCC unter „Dokumentation & Diagnostik“.

| Metrik | Vorher (DCC) | Ziel |
|--------|--------------|------|
| DE/EN-Paare | 175 | steigend |
| FR-Dateien | 0 | ≥ FAQ/KB/DCC |
| NL-Dateien | 0 | ≥ FAQ/KB/DCC |
| KB-Zähler | unvollständig | inkl. `docs/kb/` |

## Nächste Schritte (empfohlen)

1. Architecture-Blueprints: fehlende `_EN.md` aus DE-Stubs (Batch à 10)
2. Governance-Matrix `i18n`: von `gray` auf `yellow` wenn FR/NL-DCC vollständig
3. Optional: `fr.json`/`nl.json` Kernbereiche (Settings, Sidebar, Dev-Dashboard)

## Gesamtstatus

**GELB** — Switcher + DCC-FR/NL + Scanner + erster Docs-Batch erledigt; Massenübersetzung Haupt-UI und Architecture offen.
