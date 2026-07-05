# i18n Rollout — Fortschritt

**Stand:** 2026-07-05  
**Projektversion:** 1.9.19.2  
**Zweck:** Phase-1 Übersetzungsmarathon — vollständiger struktureller Rollout

## Deploy

| Check | Status |
|-------|--------|
| `deploy-to-opt.sh` → `/opt/setuphelfer` | ✅ 1.9.19.1 live |
| `check-runtime-profile-deploy-gate.sh` | ✅ grün |
| `/api/version` = Workspace | ✅ nach Deploy |

## Rescue — 100 %

| Bereich | Keys DE/EN/FR/NL |
|---------|------------------|
| `frontend/src/rescue/i18n/*.json` | 487 / 487 / 487 / 487 |
| Hardcoded-Scan | **0 Hits** |

## Frontend Haupt-UI — 100 % strukturell

| Bereich | Keys |
|---------|------|
| `de.json` / `en.json` | 3447 |
| `fr.json` / `nl.json` | 3447 (+ 9 flache Schlüssel nachgezogen) |
| Hardcoded-Scan | **0 Hits** |
| DCC `dccVis001.*` | 130 Keys FR/NL |

## Dokumentation — 100 % FR/NL (DE/EN-Paare)

| Metrik | Wert |
|--------|------|
| DE/EN-Paare | **326** |
| FR-Paare | **326 (100 %)** |
| NL-Paare | **326 (100 %)** |
| Neu in diesem Lauf | +24 DE, +17 EN, +183 FR, +183 NL |
| Skript | `marathon-sync-doc-translations.py --coverage 100 --all-prefixes` |

**Fix:** `find_file` unterstützt jetzt `notifications_en.md`-Konvention (Kleinschreibung).

## Skripte

- `scripts/i18n/marathon-sync-locales.py`
- `scripts/i18n/scan-hardcoded-ui-strings.py`
- `scripts/docs/marathon-sync-doc-translations.py` (`--coverage 50|100`, `--all-prefixes`)

## Offen (Qualität, nicht Struktur)

- FR/NL glossary-Texte in UI und Docs inhaltlich gegenlesen
- Governance-Matrix `i18n`: Review vor grün

## Gesamtstatus

**GELB** — strukturell 100 % (Rescue, Frontend-Keys, Docs FR/NL); inhaltliches Review FR/NL ausstehend.
