# Setuphelfer Update-Prüfung beim Start (Konzept)

**Geltung:** Konzept und Grenzen. **Kein** automatisches `apt upgrade`, **keine** stille Paketinstallation im Rahmen dieser Aufgabe.

## Grundsätze

1. Beim **Start** der Anwendung (oder beim ersten Dashboard-Laden) lokale **Installationsversion** (aus `config/version.json` bzw. API) mit der vom **Paketmanager** angebotenen Version für das Setuphelfer-Paket vergleichen — sobald eine **signierte** APT-Quelle konfiguriert ist.
2. **Niemals** blindes `apt upgrade` beim Start ausführen.
3. Ist ein Update verfügbar: Hinweis im UI; **`apt install`/`upgrade`** nur nach **expliziter Bestätigung** durch die Bedienperson.
4. **Kritische** Updates dürfen gefährliche Funktionen (z. B. Backup/Restore) **blockieren**, bis die Runtime dem erwarteten Paketstand entspricht — Detailregeln später in UI/Gates.
5. Paketmanager-Anbindung **nur** über **signierte** Paketquelle (`APT_REPOSITORY_PLAN.md`).
6. **`apt update`** = nur **Index-Aktualisierung**; **`apt install`/`apt upgrade`** = getrennte, bestätigte Schritte.
7. Vor Installationshinweis: **dpkg-/apt-Lock** prüfen (parallele Paketoperation) und Warnung ausgeben.
8. Jeder Update-Versuch wird **protokolliert** (Audit/Journal — in späterer Implementierung).

## Optionale API (in dieser Aufgabe nicht implementiert)

`GET /api/update/status` — nur lesend, geplantes JSON siehe englische Schwesterdatei `SETUPHELFER_UPDATE_CHECK_EN.md` (Felder `installed_version`, `backend_version`, `package_version_available`, `update_available`, `update_channel`, `apt_repo_configured`, `warnings`, `can_update`, `requires_confirmation`).

**Keine** Installation durch dieses Konzeptdokument.

## Verweise

- `docs/packaging/PACKAGE_DEPLOYMENT_GATE_DE.md`  
- `docs/evidence/release-gates/apt_update_delivery_gap.json`  
- `docs/roadmap/APT_UPDATE_DELIVERY_PLAN.md`
