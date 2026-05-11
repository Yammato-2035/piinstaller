# Deploy Runtime Identifier Elimination (DE)

Gezielte Eliminierung aktiver Runtime-Identifier (critical/high) ohne Evidence-, History- oder generische Doku-Schreibzugriffe.

**Phasen (Handoff):**

1. `runtime_identifier_elimination_targets.json` — Aggregation aus Hotspot-Analyse, optional Cycle-2-Postcheck, Consistency-Handoff; keine Tests, keine Kommentar-only-Zeilen, kein Unknown-Cluster.
2. `runtime_identifier_elimination_plan.json` — Kreuzung mit `setuphelfer_safe_rewrite_plan.json`; `write_allowed` nur bei eindeutigem `rename_now` und erlaubtem Pfad; `compatibility_aliases.json` fuer `compatibility_alias_required`.
3. `runtime_identifier_elimination_result.json` — Apply nur `write_allowed: true`, Backups unter `legacy-backups/`, laengere Tokens zuerst, atomisch `.tmp` -> replace.
4. `runtime_compatibility_alias_validation.json` — Pruefung der Alias-Policy (read-only, keine neuen Writes) plus Zaehler produktiver Inventory-Treffer.
5. `runtime_identifier_elimination_postcheck.json` — Inventory, Consistency, Hotspot-Analyse neu; Felder `runtime_identifier_elimination_complete` und vorbereiteter Patch-Bump **1.7.0 → 1.7.1** nur wenn alle Eliminationsbedingungen erfuellt sind (kein automatisches Versionsfile-Update).

Keine Runtime, kein systemctl, kein chmod/chown, kein Loeschen; bis zur Vollstaendigkeit SemVer **1.7.0**.

API: `/api/deploy/runtime-identifier-elimination-targets`, `…-plan`, `…-apply`, `/api/deploy/runtime-compatibility-alias-validation`, `…-elimination-postcheck`.

## FAQ (Kurz)

- **Cleanup-Zyklus vs Runtime-Elimination:** Zyklus 1/2 arbeiten batchweise mit definierten Grenzen; Elimination priorisiert Runtime-Hotspots und Safe-Plan explizit fuer Produktivpfade.
- **Warum Runtime zuerst:** ENV, Pfade, Units und App-IDs wirken live; Doku-Kommentare nicht.
- **Warum Aliases read-only:** Kompatibilitaet ohne neue pi-installer-Schreibwege.
- **Wann 1.7.1:** Nur wenn Postcheck `runtime_identifier_elimination_complete` true liefert (keine critical/high-Reste, Consistency nicht blocked, keine aktiven Runtime-Identifier).
