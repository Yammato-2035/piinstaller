# Setuphelfer Development Cockpit (intern)

**Matrix:** DEV-001 (Gelb) — siehe `docs/testing/DEVELOPMENT_COCKPIT_MATRIX.md`.

Dieses Verzeichnis indexiert **Prompts**, **Abschlussberichte** und **Modul-Metadaten** für das interne Dashboard (`GET /api/dev-dashboard/status`, `modules`, `evidence-index`; UI-Seite „Development Cockpit“, Sidebar nur bei Entwickler-Profil).

- `modules/*.json` — maschinenlesbare Moduldefinitionen (Ampel, nächste Schritte, Blocker, Artefakt-Pfade).
- `prompts/` — Ablage für wiederverwendbare Entwickler-Prompts (optional).
- `reports/` — Kurzberichte / Session-Abschlüsse (optional).

**Hinweis:** Markdown unter `docs/` wird im Dashboard primär **verlinkt** (Existenz-Check), nicht vollständig geparst.
