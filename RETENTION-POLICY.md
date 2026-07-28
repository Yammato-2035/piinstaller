# Gate-Retention-Policy (Paket 3, E-08)

> Ziel: Verhindern, dass ein Release-Gate wochenlang unverändert "rot"
> oder "grün" bleibt, während sich die Version darunter weiterbewegt —
> das entwertet das Gate-System (siehe Befund: `release_readiness_gate.json`
> stand ~2,5 Monate unverändert auf `do_not_release`, während 18
> Minor-Versionen gebaut wurden).

## Warum Git-Commit-Datum statt JSON-Feld

16 von 35 bestehenden Gate-Dateien enthalten **kein** Zeitstempel-Feld
(`generated`, `date`, `stand` o.ä.) im JSON selbst — u.a.
`hardware_release_gate.json` und `website_release_gate.json`, beides
P0-kritische Gates. Ein Freshness-Check, der sich auf den JSON-Inhalt
verlässt, wäre dort blind. Die Prüfung nutzt deshalb primär
`git log -1 --format=%cI -- <datei>` (Datum des letzten Commits, der die
Datei tatsächlich verändert hat) — das funktioniert unabhängig vom
Schema und lässt sich nicht durch Copy-Paste eines alten Inhalts
unbemerkt umgehen, wie es weiter unten geprüft wird.

## Schwellenwerte

| Kategorie | Gates (Beispiele) | Schwelle | Wirkung bei Überschreitung |
|---|---|---|---|
| **Kritisch (P0)** | `release_readiness_gate.json`, `hardware_release_gate.json`, `backup_restore_release_gate.json`, `supply_chain_gate.json`, `apt_update_delivery_gap.json` | 14 Tage | Status `STALE-KRITISCH` — sollte vor jedem Release-Versuch geprüft werden |
| **Standard** | alle übrigen `*_gate.json`, `*.json` unter `release-gates/` | 30 Tage | Status `STALE` — Hinweis, kein Blocker |
| **Analyse-Dokumente (`.md`)** | `ci_*_analysis_*.md`, `*_NEXT_STEP_DECISION.md` | — | Nicht geprüft — das sind Momentaufnahmen, keine lebenden Gates |

Die Liste der P0-Gates liegt in `scripts/gate_freshness_policy.json` und
ist dort erweiterbar, ohne den Prüf-Code selbst anzufassen.

## Verdachtsmoment "kopiert statt neu generiert"

Wenn ein Gate ein eigenes Datumsfeld enthält UND dieses Datum mehr als
7 Tage vom tatsächlichen Git-Commit-Datum abweicht, wird das als
`VERDACHT_KOPIERT` markiert — typisches Muster: ein altes Gate-JSON
wurde als Vorlage kopiert, das `generated`-Feld aber nicht aktualisiert.
Das ist kein Fehlalarm-Fall, sondern soll bewusst auffallen.

## Was das Skript NICHT tut

- Es überschreibt **keine** bestehenden Gate-Dateien und ändert nicht
  deren Ampel-Status — Freshness ist eine eigene Dimension, kein Ersatz
  für die inhaltliche Prüfung. Ergebnis liegt separat in
  `GATE_FRESHNESS_REPORT.json`.
- Es trifft keine Release-Entscheidung. Ein `STALE-KRITISCH`-Gate heißt:
  "geh das nochmal durch", nicht automatisch "Release blockiert".

## Wartung

Wenn ein Gate bewusst lange nicht angefasst wird, weil der Bereich
gerade nicht aktiv bearbeitet wird (z. B. Website-Gate während Fokus auf
Hardware-Tests liegt) — das ist eine legitime Situation, keine Anomalie.
Die Freshness-Prüfung soll das sichtbar machen, nicht bewerten. Die
Bewertung triffst du.
