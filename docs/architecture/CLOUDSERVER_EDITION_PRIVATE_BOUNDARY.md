# Cloudserver Edition — Private Boundary

**Stand:** 2026-06-16  
**Status:** Zurückgestellt · **keine Implementierung** im Public-Repository  
**Domäne:** `setuphelfer.cloudserver_edition` (private)

---

## Zweck

Die **Cloudserver Edition** erweitert Setuphelfer um cloud-native Backup (Snapshots, inkrementelle Jobs, Datenbank-Hooks). Die **gesamte Produktimplementierung** ist proprietär und gehört ausschließlich in ein **privates Repository**.

Das Public-Repository enthält nur:

- Architektur- und Grenzdokumentation
- Public-safe Contract-Stubs (`docs/api/cloud_public_contracts_openapi.yaml`)
- Core-Facades, die später auch Cloudserver nutzen wird (`storage_facade`, `safety_facade`)

---

## Grenzlinie

| Schicht | Public | Private |
|---------|--------|---------|
| Block-/Mount-/Safety-Logik | `backend/core/*_facade.py` | — |
| Snapshot-Provider | Interface-Stub (optional) | `backend/cloudserver_edition/` |
| Inkrementelle Backup-Jobs | — | Private Orchestrierung |
| DB-Hooks / Cloud-Metadaten | — | Private Module |
| Lizenz / Feature-Gate | — | `setuphelfer.operator_private` |
| Operator-UI für Cloud-Kunden | — | Private Frontend |

---

## Erlaubte Abhängigkeiten (Private → Public)

```text
cloudserver_edition  →  storage_facade, mount_facade, safety_facade
                      →  telemetry_client_contract (opt-in Reports)
                      →  audit_event_contract
```

**Verboten:** Public-Code importiert `cloudserver_edition` oder `cloudserver_private`.

---

## Safety-Kontext

`SafetyContext.cloudserver_future` in `safety_facade.py` ist **reserviert** für spätere Cloudserver-Zielvalidierung. Bis zur Freigabe gilt derselbe Plan-only-/Gate-Modus wie für andere Editionen.

---

## Verbotene Pfade im Public-Repo

Gate `scripts/check-public-private-boundary.sh` blockiert u. a.:

- `backend/cloudserver_private/`
- `backend/cloudserver_edition/`

---

## Öffentliche Contracts (Stubs)

- `docs/api/cloud_public_contracts_openapi.yaml` — neutrale Endpunkt-Stubs, Beispiel-Host `cloud.private.setuphelfer.example`
- Keine echten API-Keys, keine Kunden-IDs, keine Provider-Tokens

---

## Handoff

Vollständige Übergabe an Private-Repo-Team: [`docs/private-handoff/CLOUDSERVER_PRIVATE_REPO_HANDOFF.md`](../private-handoff/CLOUDSERVER_PRIVATE_REPO_HANDOFF.md)

---

## Roadmap-Hinweis

Cloudserver wird **nicht** vor Recovery-Core (Backup/Restore/Rescue) priorisiert. Status bleibt bewusst **gelb/zurückgestellt** — keine „production ready“-Aussage.
