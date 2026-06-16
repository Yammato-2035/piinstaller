# Private Repository Strategy

**Stand:** 2026-06-16

## Ziel

Kommerzielle und interne Säulen in einem **privaten** Repository entwickeln, während das öffentliche Repo Open-Core, Client und public-safe Contracts trägt.

## Geplante private Repos (oder Monorepo-Private-Subtree außerhalb Public)

| Modul | Inhalt |
|-------|--------|
| `setuphelfer-cloud` | Cloud Backup, Cloud Edition Free/Pro |
| `setuphelfer-telemetry-server` | Ingest, Signaturprüfung, interne Auswertung |
| `setuphelfer-diagnostics-server` | Diagnose-Regeln, Hardware-Fingerprints |
| `setuphelfer-operator` | Operator-Dashboard, Kundenverwaltung |
| `setuphelfer-commercial` | Lizenz, Billing, Subscriptions |
| `setuphelfer-blueprints-commercial` | Nextcloud-Cloud, Mailserver, Cloud-Härtung Pro |

## Public Repo bleibt

- Sync-fähige Version (`config/version.json`)
- Client-Stubs die private APIs **nicht** implementieren
- Handoff-Dokumente unter `docs/private-handoff/`
- Boundary-Gate in CI und pre-commit

## Migrationsregeln

1. Kein Copy-Paste privater Logik ins Public Repo „als Stub“
2. Neue kommerzielle Features starten im privaten Repo
3. Public erhält nur Contracts, Redaction, Opt-in-Texte
4. `check-public-private-boundary.sh` Exit ≠ 0 → kein Push

## Status

| Schritt | Ampel |
|---------|-------|
| Handoff-Docs | Gelb |
| Privates Repo angelegt | Rot/Pending |
| CI Boundary Gate | Grün |

Runbook: `docs/runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_DE.md`
