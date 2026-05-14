# Setuphelfer Development Cockpit (intern)

**Matrix:** DEV-001 (Gelb) — siehe `docs/testing/DEVELOPMENT_COCKPIT_MATRIX.md`.

Dieses Verzeichnis indexiert **Prompts**, **Abschlussberichte** und **Modul-Metadaten** für das interne Dashboard (`GET /api/dev-dashboard/status`, `modules`, `evidence-index`; UI-Seite „Development Cockpit“, Sidebar nur bei Entwickler-Profil).

- `modules/*.json` — maschinenlesbare Moduldefinitionen (Ampel, nächste Schritte, Blocker, Artefakt-Pfade).
- `prompts/` — Ablage für wiederverwendbare Entwickler-Prompts (optional).
- `reports/` — Kurzberichte / Session-Abschlüsse (optional).

**Hinweis:** Markdown unter `docs/` wird im Dashboard primär **verlinkt** (Existenz-Check), nicht vollständig geparst.

## Konvention: Prompts

- Speicherort: `docs/dev-dashboard/prompts/` (Dateiname z. B. `PROMPT_<thema>_<datum>.md` oder `.txt`).
- Im Modul-JSON: Feld `prompt_files` als **Liste von Repo-relativen Pfaden** (keine eingebetteten Langtexte).
- Wenn noch keine Prompt-Dateien existieren: Kurzindex `docs/dev-dashboard/reports/prompts-missing.md` verlinken und `prompt_files` leer lassen (keine Platzhalter-Riesenfiles).
- Keine Log-Auszüge oder Shell-Transkripte direkt in `modules/*.json` ablegen — nur Verweis auf Datei.

## Konvention: Abschlussberichte

- Speicherort: `docs/dev-dashboard/reports/` (z. B. `SESSION_<datum>_<kurz>.md`).
- Im Modul-JSON: Feld `report_files` mit relativen Pfaden.
- Für release-relevante Feststellungen zusätzlich die bestehende Evidence-Struktur unter `docs/evidence/` nutzen und in `evidence_files` verlinken.

## Konvention: Module → Prompts/Berichte

- Jedes Modul in `modules/<slug>.json` hat eine stabile `id` (kebab-case, konsistent mit Dateiname empfohlen).
- `artifacts[]` beschreibt Pfade mit `kind` (`doc`, `faq`, `kb`, `evidence`, `prompt`, `report`, `gate`, …) für Existenz-Checks in der API.
- `children[]` optional: Unterpunkte mit eigener `id`, `status`, `summary` — **keine** tiefen Objekt-Bäume; maximal flache Liste.

## Commit-Hashes

- Optionales Feld `commits`: Liste von Strings, z. B. `abc1234 Kurzbeschreibung` oder `abc1234` — manuell nach Merge pflegen, nicht automatisch aus CI schreiben.

## Nächste Schritte (`next_steps`)

- Kurze imperative Sätze oder Ticket-IDs, max. eine Zeile pro Eintrag.
- Regelmäßig abhaken/ersetzen, wenn erledigt; veraltete Einträge vermeiden.

## Nebenschritte / Blocker (`blockers`)

- `blockers`: konkrete Hindernisse (Gate, HW, fehlende Evidence).
- Feinere „Nebenschritte“ gehören in `next_steps` oder in Kinder-`summary` unter `children`, nicht in riesige `summary`-Felder der Wurzel.

## API-Normalisierung

- Unbekannte Ampel-Werte in JSON werden serverseitig auf `gray` gesetzt; Listenfelder fehlender Keys werden zu `[]`. Parser bleiben tolerant (kein 500 bei fehlenden Dateien).

## Testlücken (Frontend)

- Vollständige Interaktions- und Layout-Tests mit `@testing-library/react` + **jsdom** sind im Projekt derzeit **nicht** als Abhängigkeit vorgesehen. Smoke-Tests nutzen `react-dom/server` (`renderToStaticMarkup`) auf `DevDashboardBody` — keine echten Klicks, keine echten `fetch`-Calls in diesen Tests.
