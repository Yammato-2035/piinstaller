# DCC Report Freshness — Source Audit

**Status:** `stale_source_path_gap` (behoben durch neuen Evidence-Feed)

## Befund

| Kriterium | Ergebnis |
|-----------|----------|
| Neue Evidence 02./03.06 im Repo | **yes** (z. B. `QEMU_GUEST_AGENT_*`, `DEVELOPER_QEMU_ISO_*`, `controlled_iso_build_*`) |
| DCC „letzte Berichte“ (Dev-Server) | **Agent-Uploads** aus `DevServerStorage` — älteste Einträge vom **2026-05-30** |
| Control-Center `recent_files` | **mtime-Walk** mit `max_files=80`, 8 Dateien/Bucket — **keine** gezielte Report-Sortierung |
| Abweichung mtime vs. embedded `**Datum:**` | **yes** — Datum in MD wurde nicht für Sortierung genutzt |

## Ursache sichtbarer 30.05.-Berichte

`latest_findings` = letzte **Dev-Server-Agent-Reports**, nicht Repo-Abschlussberichte.

**Status (vor Fix):** `stale_source_path_gap` + `frontend_display_bug`
