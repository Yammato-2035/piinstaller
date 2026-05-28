# Controlled Command Runner MVP Decision

Datum: 2026-05-28

## Entscheidung

Start bei **MVP-0** (Dokumentation/Schema/Allowlist-Design), keine Runtime-Ausführung.

## Begründung

- Phase-0-Gate war im Lauf nicht grün.
- Aktiver Rescue-Blocker (Chroot-/Mount-Cleanup) hat technische Priorität.
- Sicherheitsgrenze soll vor jeder Execute-Funktion sauber fixiert werden.

## Ergebnis

- Boundary-Regeln dokumentiert (intern, nicht user-facing).
- Controlled-Runner-Datenmodell und Allowlist-Entwurf erstellt.
- Roadmap-Pfad `developer-tooling/controlled-command-runs` als nicht produktrelevanter Track ergänzt.
