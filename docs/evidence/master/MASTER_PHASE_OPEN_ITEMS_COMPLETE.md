# Offene Master-Phase-Punkte — Abschluss (öffentliches Repo)

**Version:** 1.9.17.2

## Umgesetzt

| Punkt | Artefakt |
|-------|----------|
| `rescue_network` API | `backend/api/routes/rescue_network.py` |
| Evidence-Bundle-Schreiben | `scripts/rescue/write-master-assessment-evidence.sh` |
| Private Monorepo-Skeleton | `docs/private-server-skeletons/` (3 Server + infra) |
| Lab-Mocks starten | `scripts/start-rescue-lab-mocks.sh` |
| Privates Repo bootstrap | `scripts/bootstrap-setuphelfer-private-repo.sh` |

## Bewusst blockiert (nichts entgegen)

| Punkt | Grund |
|-------|--------|
| Payload/ISO-Build | Operator-Freigabe + Hard-Safety-Regeln |
| IONOS-Produktiv-Deploy | Separater Deploy-Run |
| `gh repo create` auf deinem GitHub | Erfordert lokales `gh auth` — Script bereit |

## Nächster Schritt (Laptop)

```bash
cd ~/piinstaller
./scripts/bootstrap-setuphelfer-private-repo.sh ~/setuphelfer-private
./scripts/start-rescue-lab-mocks.sh
```
