# DCC Report Freshness & Test Filter — Result

## Ursache

Das DCC zeigte **Dev-Server-Agent-Uploads** (älteste vom 2026-05-30) als „Neueste Berichte“. Repo-Abschlussberichte vom 02./03.06.2026 waren nicht angebunden; der Evidence-Index nutzte einen begrenzten mtime-Walk ohne Report-Priorität.

## Fix

- Backend: `dev_dashboard_recent_evidence.py` + API `/api/dev-dashboard/recent-evidence`
- Summary: `recent_reports` / `recent_tests` (Default 5)
- Frontend: `RecentEvidenceFeedPanel` mit Filtern; Manual-Runs auf 5 begrenzt
- Dev-Server: Klartext „Agent-Uploads“

## Keine Runtime-Aktionen

Kein ISO/QEMU/USB/Backup/Restore/Deploy.
